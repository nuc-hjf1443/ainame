<template>
  <view class="page" v-if="expert">
    <view class="profile"><view class="avatar">{{expert.display_name.slice(0,1)}}</view><view><view class="name">{{expert.display_name}}</view><view class="type">{{typeLabel}} · {{expert.years_experience}} 年经验</view><view class="rating">★ {{Number(expert.average_rating).toFixed(1)}} · {{expert.review_count}} 条评价</view></view></view>
    <view class="section"><view class="section-title">专家简介</view><view class="copy">{{expert.bio}}</view><view class="credentials">资历：{{expert.credentials}}</view></view>
    <view class="section"><view class="section-title">选择平台套餐</view><view v-if="!packages.length" class="empty">暂无可用套餐</view><view v-for="item in packages" :key="item.id" :class="['package',form.package_id===item.id?'selected':'']" @click="form.package_id=item.id"><view><text class="package-name">{{item.name}}</text><text class="copy">{{item.description}}</text></view><view><text class="price">¥{{item.price}}</text><text class="days">{{item.delivery_days}} 天交付</text></view></view></view>
    <view class="section"><view class="section-title">选择名字资产</view><picker :range="assetLabels" @change="e=>form.naming_asset_id=assets[e.detail.value]?.id"><view class="field">{{selectedAssetLabel}}</view></picker><textarea class="area" v-model="form.requirements" placeholder="说明希望专家重点分析的问题"/></view>
    <button class="primary" :loading="loading" @click="createOrder">创建订单</button>
  </view>
</template>
<script setup>
import { computed, reactive, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { openAlipayWindow, startAlipayPayment } from '@/utils/alipayPayment.js';

const expert = ref(null);
const packages = ref([]);
const assets = ref([]);
const loading = ref(false);
const form = reactive({ package_id: null, naming_asset_id: null, requirements: '' });
const PENDING_EXPERT_ALIPAY_KEY = 'pending_expert_alipay_out_trade_no';
const typeLabel = computed(() => expert.value?.expert_type === 'CULTURE_MASTER' ? '国学命名' : '品牌咨询');
const assetLabels = computed(() => assets.value.map(item => `${item.name} · ${item.category}`));
const selectedAssetLabel = computed(() => assets.value.find(item => item.id === form.naming_asset_id)?.name || '请选择已收藏的名字');

const redirectToAlipay = (payment, payWindow = null) => {
  startAlipayPayment(payment, { pendingKey: PENDING_EXPERT_ALIPAY_KEY, payWindow });
};

const createOrder = async () => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  if (!form.package_id || !form.naming_asset_id || form.requirements.trim().length < 5) {
    return uni.showToast({ title: '请选择套餐、名字并填写需求', icon: 'none' });
  }
  loading.value = true;
  try {
    const order = await http.createExpertOrder({ expert_id: expert.value.id, ...form });
    uni.showModal({
      title: '订单已创建',
      content: `应付 ¥${order.amount}，是否前往支付宝沙箱支付？`,
      success: async result => {
        if (result.confirm) {
          const payWindow = openAlipayWindow();
          const payment = await http.startExpertAlipay(order.id);
          redirectToAlipay(payment, payWindow);
        } else {
          uni.reLaunch({ url: '/pages/assets/index?tab=orders' });
        }
      }
    });
  } finally {
    loading.value = false;
  }
};

onLoad(async query => {
  expert.value = await http.getExpert(Number(query.id));
  packages.value = await http.getExpertPackages('', expert.value.id);
  form.package_id = packages.value[0]?.id || null;
  if (uni.getStorageSync('token')) assets.value = (await http.getNameAssets()).items;
});
</script>
<style scoped>
.page{padding:30rpx;background:#f5f7f6;min-height:100vh;box-sizing:border-box}.profile,.section{background:#fff;border:1px solid #e2e8f0;border-radius:8rpx;padding:28rpx;margin-bottom:20rpx}.profile{display:flex;gap:24rpx;align-items:center}.avatar{width:100rpx;height:100rpx;border-radius:50%;background:#dff4ef;color:#0f766e;display:flex;align-items:center;justify-content:center;font-size:42rpx;font-weight:700}.name{font-size:38rpx;font-weight:700}.type,.rating{color:#0f766e;font-size:24rpx;margin-top:8rpx}.section-title{font-size:30rpx;font-weight:700;margin-bottom:18rpx}.copy,.credentials{font-size:25rpx;color:#64748b;line-height:1.7;display:block}.credentials{margin-top:16rpx}.package{border:1px solid #e2e8f0;padding:20rpx;border-radius:8rpx;margin-bottom:14rpx;display:flex;justify-content:space-between;gap:20rpx}.package.selected{border-color:#0f766e;background:#ecfdf8}.package-name,.price,.days{display:block}.package-name{font-weight:700}.price{color:#dc2626;font-size:32rpx;font-weight:700}.days{font-size:22rpx;color:#64748b}.field,.area{background:#f8fafc;padding:22rpx;border:1px solid #e2e8f0;border-radius:8rpx;box-sizing:border-box;width:100%}.area{height:150rpx;margin-top:16rpx}.primary{background:#0f766e;color:#fff;border-radius:8rpx}.empty{color:#94a3b8}
</style>
