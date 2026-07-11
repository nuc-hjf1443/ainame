<template>
  <view class="page">
    <view class="panel">
      <view class="title">{{ title }}</view>
      <view class="copy">{{ message }}</view>
      <button class="primary" :loading="loading" @click="syncPayment">刷新支付状态</button>
      <button class="secondary" @click="goTarget">{{ targetText }}</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const loading = ref(false);
const outTradeNo = ref('');
const title = ref('正在确认支付');
const message = ref('正在向后端同步支付宝沙箱交易结果。');
const target = ref('/pages/recharge/index');
const targetText = ref('返回充值中心');
const PENDING_MEMBERSHIP_ALIPAY_KEY = 'pending_membership_alipay_out_trade_no';
const PENDING_EXPERT_ALIPAY_KEY = 'pending_expert_alipay_out_trade_no';
const paymentStatusText = value => ({
  PENDING: '待支付',
  PAID: '已支付',
  CANCELLED: '已取消',
  REFUNDED: '已退款'
}[value] || value || '-');

const goTarget = () => uni.reLaunch({ url: target.value });

const syncPayment = async () => {
  if (!outTradeNo.value) {
    title.value = '缺少支付单号';
    message.value = '请返回订单列表后重新发起支付。';
    return;
  }
  loading.value = true;
  try {
    const result = await http.syncAlipayOrder(outTradeNo.value);
    if (result.status === 'PAID') {
      title.value = '支付成功';
      message.value = '权益或订单状态已同步完成。';
      uni.removeStorageSync(PENDING_MEMBERSHIP_ALIPAY_KEY);
      uni.removeStorageSync(PENDING_EXPERT_ALIPAY_KEY);
      if (result.order_type === 'EXPERT_SERVICE') {
        target.value = '/pages/assets/index?tab=orders';
        targetText.value = '查看专家订单';
      } else {
        target.value = '/pages/recharge/index';
        targetText.value = '查看会员权益';
      }
      setTimeout(goTarget, 900);
    } else {
      title.value = '支付未完成';
      message.value = `当前订单状态：${paymentStatusText(result.status)}`;
    }
  } finally {
    loading.value = false;
  }
};

onLoad(query => {
  outTradeNo.value = query.out_trade_no || '';
  if (query.status === 'invalid') {
    title.value = '回跳验签失败';
    message.value = '请刷新支付状态或返回订单列表确认。';
  }
  syncPayment();
});
</script>

<style scoped>
.page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:40rpx;background:#f8f4ec;box-sizing:border-box}.panel{width:min(680rpx,100%);background:#fff;border:1px solid #e7e0d4;border-radius:8px;padding:48rpx;text-align:center}.title{font-size:42rpx;font-weight:800;color:#17243b}.copy{font-size:27rpx;color:#667085;line-height:1.7;margin:24rpx 0 36rpx}.primary,.secondary{height:88rpx;line-height:88rpx;border-radius:8px;font-size:28rpx;margin-top:18rpx}.primary{background:#24324a;color:#f5d392}.secondary{background:#fff;color:#17243b;border:1px solid #e7e0d4}
</style>
