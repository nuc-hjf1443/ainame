<template>
  <DashboardLayout currentMenu="orders">
    <view class="orders-page">
      <view class="page-head">
        <view>
          <view class="eyebrow">MY ORDERS</view>
          <view class="title">我的订单</view>
          <view class="subtitle">查看支付状态，15分钟内未支付订单可继续拉起支付宝沙箱支付。</view>
        </view>
        <button class="refresh-btn" :loading="loading" @click="loadOrders">刷新</button>
      </view>

      <view v-if="loading && !orders.length" class="empty">订单加载中...</view>
      <view v-else-if="!orders.length" class="empty">暂无订单</view>
      <view v-else class="order-list">
        <view v-for="order in orders" :key="order.id" class="order-card">
          <view class="order-top">
            <view>
              <view class="order-title">{{ orderTitle(order) }}</view>
              <view class="order-no">订单号：{{ order.out_trade_no || order.id }}</view>
            </view>
            <view :class="['status-pill', statusClass(order.status)]">{{ statusText(order.status) }}</view>
          </view>

          <view class="order-grid">
            <view class="field">
              <text class="label">金额</text>
              <text class="value amount">¥{{ priceText(order.amount) }}</text>
            </view>
            <view class="field">
              <text class="label">类型</text>
              <text class="value">{{ typeText(order.order_type) }}</text>
            </view>
            <view class="field">
              <text class="label">服务状态</text>
              <text class="value">{{ serviceStatusText(order.service_status) }}</text>
            </view>
            <view class="field">
              <text class="label">支付渠道</text>
              <text class="value">{{ providerText(order.payment_provider) }}</text>
            </view>
            <view class="field">
              <text class="label">创建时间</text>
              <text class="value">{{ timeText(order.created_time) }}</text>
            </view>
            <view class="field">
              <text class="label">支付时间</text>
              <text class="value">{{ timeText(order.paid_time) }}</text>
            </view>
            <view class="field">
              <text class="label">支付截止</text>
              <text class="value">{{ order.status === 'PENDING' ? timeText(order.payment_deadline) : '-' }}</text>
            </view>
            <view class="field">
              <text class="label">支付宝交易号</text>
              <text class="value mono">{{ order.provider_trade_no || '-' }}</text>
            </view>
          </view>

          <view class="order-actions">
            <text v-if="canContinuePay(order)" class="deadline-tip">请在 {{ timeText(order.payment_deadline) }} 前完成支付</text>
            <text v-else-if="order.status === 'PENDING'" class="deadline-tip warn">订单已超过支付时限，刷新后会变为已取消</text>
            <button
              v-if="canContinuePay(order)"
              class="pay-btn"
              :loading="payingId === order.id"
              @click="continuePay(order)"
            >
              继续支付
            </button>
          </view>
        </view>
      </view>

      <view v-if="total > orders.length" class="pager">
        <button class="load-more" :loading="loadingMore" @click="loadMore">加载更多</button>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';
import { openAlipayWindow, startAlipayPayment } from '@/utils/alipayPayment.js';

const orders = ref([]);
const total = ref(0);
const page = ref(1);
const loading = ref(false);
const loadingMore = ref(false);
const payingId = ref(null);
const PAGE_SIZE = 20;
const PENDING_ALIPAY_KEY = 'pending_user_order_alipay_out_trade_no';

const priceText = value => Number(value || 0).toFixed(2);
const timeText = value => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  const pad = number => String(number).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

const orderTitle = order => order.service_package_name || order.package_name || order.payment_subject || '订单';
const typeText = type => ({ MEMBERSHIP: '会员/额度', EXPERT_SERVICE: '专家服务' }[type] || '-');
const providerText = provider => ({ ALIPAY_SANDBOX: '支付宝沙箱', MOCK: '模拟支付' }[provider] || provider || '-');
const statusText = status => ({ PENDING: '待支付', PAID: '已支付', CANCELLED: '已取消', REFUNDED: '已退款' }[status] || status || '-');
const serviceStatusText = status => ({
  PENDING_PAYMENT: '待支付',
  WAITING_ACCEPT: '待接单',
  IN_PROGRESS: '服务中',
  DELIVERED: '已交付',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  REFUND_PENDING: '退款审核中'
}[status] || '-');
const statusClass = status => String(status || '').toLowerCase();
const canContinuePay = order => {
  if (order.status !== 'PENDING') return false;
  if (!['MEMBERSHIP', 'EXPERT_SERVICE'].includes(order.order_type)) return false;
  if (!order.payment_deadline) return false;
  return new Date(order.payment_deadline).getTime() > Date.now();
};

const syncPendingPayment = async () => {
  const outTradeNo = uni.getStorageSync(PENDING_ALIPAY_KEY);
  if (!outTradeNo || !uni.getStorageSync('token')) return;
  try {
    const result = await http.syncAlipayOrder(outTradeNo, { silent: true });
    if (result.status === 'PAID') {
      uni.removeStorageSync(PENDING_ALIPAY_KEY);
      uni.showToast({ title: '支付已同步', icon: 'none' });
    }
  } catch (e) {
    // Keep the trade number for the next page visit.
  }
};

const fetchPage = async targetPage => {
  const result = await http.getMyPaymentOrders(targetPage, PAGE_SIZE);
  total.value = result.total || 0;
  page.value = targetPage;
  orders.value = targetPage === 1 ? result.items || [] : orders.value.concat(result.items || []);
};

const loadOrders = async () => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  loading.value = true;
  try {
    await syncPendingPayment();
    await fetchPage(1);
  } finally {
    loading.value = false;
  }
};

const loadMore = async () => {
  if (loadingMore.value) return;
  loadingMore.value = true;
  try {
    await fetchPage(page.value + 1);
  } finally {
    loadingMore.value = false;
  }
};

const continuePay = async order => {
  if (!canContinuePay(order)) {
    uni.showToast({ title: '订单已超过支付时限', icon: 'none' });
    await loadOrders();
    return;
  }
  const payWindow = openAlipayWindow();
  payingId.value = order.id;
  try {
    const payment = await http.startPaymentOrderAlipay(order.id);
    startAlipayPayment(payment, { pendingKey: PENDING_ALIPAY_KEY, payWindow });
  } finally {
    payingId.value = null;
  }
};

onShow(loadOrders);
</script>

<style scoped>
.orders-page{min-height:100%;padding:32rpx 28rpx 80rpx;box-sizing:border-box;background:#fff;color:#111827}.page-head{display:flex;align-items:flex-start;justify-content:space-between;gap:24rpx;margin-bottom:28rpx}.eyebrow{font-size:22rpx;letter-spacing:4rpx;color:#9ca3af;font-weight:700}.title{font-size:48rpx;font-weight:900;margin-top:10rpx}.subtitle{font-size:26rpx;color:#6b7280;margin-top:10rpx}.refresh-btn,.load-more{height:72rpx;line-height:72rpx;border-radius:12rpx;background:#fff;border:1px solid #e5e7eb;color:#374151;font-size:26rpx;font-weight:700;margin:0}.refresh-btn::after,.load-more::after,.pay-btn::after{border:none}.empty{padding:80rpx 0;text-align:center;color:#9ca3af;font-size:28rpx}.order-list{display:flex;flex-direction:column;gap:20rpx}.order-card{border:1px solid #eef0f4;border-radius:16rpx;padding:28rpx;background:#fff;box-shadow:0 10rpx 28rpx rgba(15,23,42,.04)}.order-top{display:flex;justify-content:space-between;align-items:flex-start;gap:20rpx;margin-bottom:24rpx}.order-title{font-size:30rpx;font-weight:900}.order-no{margin-top:8rpx;font-size:22rpx;color:#6b7280;word-break:break-all}.status-pill{flex-shrink:0;padding:8rpx 18rpx;border-radius:999px;font-size:22rpx;font-weight:800;background:#f3f4f6;color:#4b5563}.status-pill.pending{background:#fff7ed;color:#c2410c}.status-pill.paid{background:#ecfdf5;color:#047857}.status-pill.cancelled{background:#f3f4f6;color:#6b7280}.status-pill.refunded{background:#eff6ff;color:#24324a}.order-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18rpx 24rpx}.field{min-width:0}.label{display:block;font-size:22rpx;color:#9ca3af;margin-bottom:6rpx}.value{display:block;font-size:25rpx;color:#111827;font-weight:700;word-break:break-word}.amount{color:#24324a}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}.order-actions{display:flex;align-items:center;justify-content:space-between;gap:20rpx;margin-top:26rpx;padding-top:22rpx;border-top:1px solid #f3f4f6}.deadline-tip{font-size:24rpx;color:#6b7280}.deadline-tip.warn{color:#c2410c}.pay-btn{width:auto;height:72rpx;line-height:72rpx;border-radius:12rpx;background:#24324a;color:#fff;font-size:26rpx;font-weight:800;margin:0;padding:0 30rpx}.pager{display:flex;justify-content:center;margin-top:28rpx}@media(max-width:900px){.page-head{flex-direction:column}.refresh-btn{width:100%}.order-top{flex-direction:column}.order-grid{grid-template-columns:1fr 1fr}.order-actions{flex-direction:column;align-items:stretch}.pay-btn{width:100%}}@media(max-width:520px){.order-grid{grid-template-columns:1fr}.title{font-size:42rpx}}
</style>

