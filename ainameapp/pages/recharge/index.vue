<template>
  <DashboardLayout currentMenu="recharge">
    <view class="pricing-page">
      <view class="pricing-hero">
        <view class="eyebrow">RECHARGE CENTER</view>
        <view class="title">Pricing</view>
        <view class="subtitle">选择适合你的起名额度和会员服务，支付成功后立即生效。</view>
        <view v-if="profile" class="balance-strip">
          <text>今日起名 {{ profile.naming_quota.remaining }} / {{ profile.naming_quota.limit }}</text>
          <text>购买余额 {{ profile.naming_balance || 0 }} 次</text>
          <text>视觉生成 {{ profile.visual_quota.remaining }} / {{ profile.visual_quota.limit }}</text>
        </view>
      </view>

      <view class="section-label">VIP 套餐</view>
      <view class="plan-grid">
        <view class="plan-card soft">
          <view class="plan-name">免费版</view>
          <view class="price-line"><text class="currency">¥</text><text class="price">0</text><text class="period">/ 当前账号</text></view>
          <view class="features">
            <view class="feature">每日 5 次智能起名</view>
            <view class="feature">可收藏名字资产</view>
            <view class="feature">可发布灵感投票</view>
          </view>
          <button class="secondary-btn" disabled>{{ profile && profile.is_vip ? '基础权益' : '当前默认' }}</button>
        </view>

        <view v-for="item in vipPackages" :key="item.id" :class="['plan-card', item.package_code === 'VIP_MONTHLY' ? 'highlight' : '']">
          <view class="plan-name">{{ item.name }}</view>
          <view class="price-line"><text class="currency">¥</text><text class="price">{{ priceText(item.price) }}</text><text class="period">/ {{ item.duration_days >= 365 ? '年' : '月' }}</text></view>
          <view class="features">
            <view class="feature">每日 {{ item.naming_daily_quota }} 次智能起名</view>
            <view class="feature">每日 {{ item.visual_daily_quota }} 次视觉生成</view>
            <view class="feature">专家服务 {{ discountText(item.expert_discount) }}</view>
            <view class="feature">{{ item.description || '会员权益立即生效' }}</view>
          </view>
          <button
            :class="currentVipPackage(item) ? 'secondary-btn' : 'primary-btn'"
            :disabled="currentVipPackage(item)"
            :loading="payingId === item.id"
            @click="buyPackage(item)"
          >
            {{ currentVipPackage(item) ? '当前套餐' : `购买 ${item.name}` }}
          </button>
        </view>
      </view>

      <view class="section-label quota-label">起名次数充值</view>
      <view class="plan-grid quota-grid">
        <view v-for="item in quotaPackages" :key="item.id" class="plan-card quota-card">
          <view class="plan-name">{{ item.name }}</view>
          <view class="price-line"><text class="currency">¥</text><text class="price">{{ priceText(item.price) }}</text><text class="period">/ 永久有效</text></view>
          <view class="quota-count">{{ item.api_quota }} 次</view>
          <view class="features">
            <view class="feature">免费/VIP 当日额度用完后自动抵扣</view>
            <view class="feature">仅用于智能起名和多轮微调</view>
            <view class="feature">失败退款会退回次数余额</view>
          </view>
          <button class="primary-btn" :loading="payingId === item.id" @click="buyPackage(item)">
            购买次数包
          </button>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const packages = ref([]);
const profile = ref(null);
const payingId = ref(null);

const vipPackages = computed(() => packages.value.filter(item => ['VIP_MONTHLY', 'VIP_YEARLY'].includes(item.package_code)));
const quotaPackages = computed(() => packages.value.filter(item => String(item.package_code || '').startsWith('QUOTA_NAMING_')));
const priceText = value => Number(value || 0).toFixed(2).replace(/\.00$/, '');
const discountText = value => `${Math.round(Number(value || 1) * 10)} 折`;
const currentVipPackage = item => Boolean(
  profile.value?.is_vip && (
    profile.value.vip_package_code
      ? profile.value.vip_package_code === item.package_code
      : profile.value.vip_package_name === item.name
  )
);

const redirectToAlipay = payment => {
  // #ifdef H5
  window.location.href = payment.payment_url;
  // #endif
  // #ifndef H5
  uni.showToast({ title: '当前仅 H5 支持支付宝沙箱支付', icon: 'none' });
  // #endif
};

const load = async () => {
  packages.value = await http.getMembershipPackages();
  if (uni.getStorageSync('token')) profile.value = await http.getMyProfile();
  else profile.value = null;
};

const buyPackage = item => {
  if (currentVipPackage(item)) return;
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  const content = item.package_code?.startsWith('QUOTA_NAMING_')
    ? `支付宝沙箱支付 ¥${priceText(item.price)}，到账 ${item.api_quota} 次起名余额。`
    : `支付宝沙箱支付 ¥${priceText(item.price)}，${item.name} 将立即开通或顺延。`;
  uni.showModal({
    title: `购买${item.name}`,
    content,
    success: async result => {
      if (!result.confirm) return;
      payingId.value = item.id;
      try {
        const order = await http.createMembershipOrder(item.id);
        const payment = await http.startMembershipAlipay(order.id);
        redirectToAlipay(payment);
      } finally {
        payingId.value = null;
      }
    }
  });
};

onShow(load);
</script>

<style scoped>
.pricing-page{min-height:100%;padding:36rpx 28rpx 100rpx;box-sizing:border-box;background:#fff;color:#111827}.pricing-hero{text-align:center;padding:48rpx 0 60rpx}.eyebrow{font-size:22rpx;letter-spacing:4rpx;color:#9ca3af;font-weight:700}.title{font-size:76rpx;font-weight:800;line-height:1.05;margin-top:24rpx;font-family:Georgia,'Times New Roman',serif;color:#111}.subtitle{font-size:28rpx;color:#8b91a1;margin-top:22rpx}.balance-strip{display:inline-flex;gap:24rpx;flex-wrap:wrap;justify-content:center;margin-top:36rpx;padding:18rpx 28rpx;background:#f8fafc;border:1px solid #e5e7eb;border-radius:999px;color:#4b5563;font-size:24rpx}.section-label{text-align:center;font-size:30rpx;font-weight:800;margin:0 0 28rpx}.quota-label{margin-top:64rpx}.plan-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32rpx;max-width:1040px;margin:0 auto}.plan-card{background:#fff;border:1px solid #eef0f4;border-radius:18rpx;padding:40rpx 34rpx;min-height:620rpx;display:flex;flex-direction:column;box-shadow:0 12rpx 36rpx rgba(15,23,42,.03)}.plan-card.soft{background:#fbfcfe}.plan-card.highlight{border-color:#cfd8ea;box-shadow:0 16rpx 42rpx rgba(37,99,235,.08)}.plan-name{font-size:28rpx;font-weight:800}.price-line{display:flex;align-items:flex-end;margin-top:22rpx}.currency{font-size:34rpx;font-weight:900;margin-bottom:8rpx}.price{font-size:54rpx;font-weight:900;line-height:1}.period{font-size:22rpx;font-weight:700;color:#111;margin-left:6rpx;margin-bottom:9rpx}.features{display:flex;flex-direction:column;gap:22rpx;margin-top:34rpx;flex:1}.feature{position:relative;padding-left:38rpx;font-size:24rpx;line-height:1.35;font-weight:600;color:#1f2937}.feature::before{content:'✓';position:absolute;left:0;top:0;color:#9ca3af;font-weight:900}.primary-btn,.secondary-btn{height:88rpx;line-height:88rpx;border-radius:14rpx;font-size:28rpx;font-weight:800;margin:42rpx 0 0}.primary-btn{background:#4f6ff2;color:#fff;box-shadow:0 8rpx 16rpx rgba(79,111,242,.22)}.secondary-btn{background:#fff;color:#9ca3af;border:1px solid #e5e7eb}.primary-btn::after,.secondary-btn::after{border:none}.quota-grid{max-width:1040px}.quota-card{min-height:520rpx}.quota-count{display:inline-flex;align-self:flex-start;margin-top:24rpx;padding:12rpx 22rpx;border-radius:999px;background:#eef2ff;color:#4f46e5;font-size:26rpx;font-weight:800}@media(max-width:900px){.plan-grid{grid-template-columns:1fr}.plan-card{min-height:auto}.title{font-size:58rpx}.pricing-hero{padding-top:24rpx}.balance-strip{border-radius:18rpx}}@media(min-width:1200px){.pricing-page{padding-top:48rpx}}
</style>
