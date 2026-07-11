<template>
  <DashboardLayout currentMenu="expert">
    <view class="detail-page" v-if="expert">
      <view class="breadcrumb">首页 〉 专家服务 〉 专家详情</view>
      <view class="layout">
        <view class="main">
          <view class="expert-banner">
            <view class="portrait">{{ expert.display_name.slice(0,1) }}</view>
            <view class="banner-copy">
              <view class="name-row">
                <text class="expert-name">{{ expert.display_name }}</text>
                <text class="badge">资深命名专家</text>
              </view>
              <view class="rating">★ {{ Number(expert.average_rating || 0).toFixed(1) }} 分 ｜ 已完成 {{ expert.review_count || 0 }} 单</view>
              <view class="tags">
                <text>{{ typeLabel }}</text><text>传统文化</text><text>品牌策略</text>
              </view>
            </view>
            <view class="stats">
              <view><text>从业经验</text><strong>{{ expert.years_experience }}年+</strong></view>
              <view><text>服务客户</text><strong>500+</strong></view>
              <view><text>好评率</text><strong>98%</strong></view>
              <view><text>平均响应</text><strong>30分钟内</strong></view>
            </view>
          </view>

          <view class="intro-card">
            <view class="section-title">专家简介</view>
            <view class="intro">{{ expert.bio }}</view>
            <view class="intro muted">{{ expert.credentials }}</view>
          </view>

          <view class="section-title block-title">服务套餐</view>
          <view class="package-grid">
            <view v-for="item in packages" :key="item.id" :class="['package-card', selectedPackage?.id === item.id ? 'selected' : '']" @click="selectedPackage = item">
              <view class="package-head">
                <view><strong>{{ item.name }}</strong><text>{{ item.delivery_days }} 天交付</text></view>
                <text v-if="selectedPackage?.id === item.id" class="hot">已选</text>
              </view>
              <view class="price">¥ {{ payable(item) }}</view>
              <view class="desc">{{ item.description }}</view>
              <button class="outline">选择此套餐</button>
            </view>
          </view>

          <view class="review-card">
            <view class="review-head">
              <view class="section-title">用户评价</view>
              <view>综合评分 <strong>{{ Number(expert.average_rating || 0).toFixed(1) }}</strong></view>
            </view>
            <view class="review-row">
              <view class="review-avatar">云</view>
              <view>
                <view class="review-meta">云舟科技 · 专业版 · ★★★★★</view>
                <view class="review-text">名字非常有内涵，既符合行业属性，又朗朗上口，后续品牌规划也给了很多建议。</view>
              </view>
            </view>
          </view>
        </view>

        <view class="side">
          <view class="booking-card">
            <view class="book-name">{{ expert.display_name }}</view>
            <view><text class="book-price">¥ {{ selectedPackage ? payable(selectedPackage) : '-' }}</text><text class="muted"> 起</text></view>
            <view class="divider"></view>
            <view class="booking-title">立即预约</view>
            <button class="outline-full" @click="startChat">先咨询</button>
            <button class="dark-full" @click="openOrder">立即下单</button>
            <view class="guarantee" v-for="item in guarantees" :key="item.title">
              <view class="guarantee-icon">{{ item.icon }}</view>
              <view><text>{{ item.title }}</text><text>{{ item.desc }}</text></view>
            </view>
          </view>
          <view class="side-card">
            <view class="section-title">擅长行业</view>
            <view class="industry-grid">
              <text v-for="item in industries" :key="item">{{ item }}</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="orderOpen" class="overlay" @click="orderOpen = false">
        <view class="order-sheet" @click.stop>
          <view class="section-title">提交精批需求</view>
          <view class="field-label">选择已收藏资产</view>
          <picker :range="assetLabels" @change="selectAsset"><view class="input">{{ selectedAssetLabel }}</view></picker>
          <view class="field-label">或直接输入名称</view>
          <input class="input" v-model="orderForm.name" placeholder="请输入需要精批的姓名或品牌名" />
          <view class="field-label">需求补充说明</view>
          <textarea class="area" v-model="orderForm.requirements" placeholder="请说明命名背景、用途和关注点（至少 5 个字）"></textarea>
          <button class="dark-full" :loading="submitting" @click="createOrder">创建订单并支付</button>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';
import { openAlipayWindow, startAlipayPayment } from '@/utils/alipayPayment.js';

const expertId = ref(null);
const expert = ref(null);
const packages = ref([]);
const selectedPackage = ref(null);
const assets = ref([]);
const profile = ref(null);
const orderOpen = ref(false);
const submitting = ref(false);
const orderForm = reactive({ naming_asset_id: null, name: '', requirements: '' });
const PENDING_EXPERT_ALIPAY_KEY = 'pending_expert_alipay_out_trade_no';
const guarantees = [
  { icon: '一', title: '一对一专属服务', desc: '全程沟通，量身定制' },
  { icon: '改', title: '不满意可修改', desc: '多轮修改，直到满意' },
  { icon: '密', title: '保密协议', desc: '严格保护商业信息' },
  { icon: '时', title: '按时交付', desc: '超时赔付，保障交付时效' }
];
const industries = ['科技互联网', '文化教育', '消费零售', '金融服务', '健康医疗', '制造工业'];

const typeLabel = computed(() => expert.value?.expert_type === 'CULTURE_MASTER' ? '国学命名' : '品牌咨询');
const assetLabels = computed(() => assets.value.map(item => `${item.name} · ${item.category}`));
const selectedAssetLabel = computed(() => assets.value.find(item => item.id === orderForm.naming_asset_id)?.name || '请选择已收藏资产（可选）');
const payable = item => profile.value?.is_vip ? (Number(item.price) * 0.9).toFixed(2) : Number(item.price).toFixed(2);
const load = async () => {
  if (!expertId.value) return;
  const [expertResult, packageResult] = await Promise.all([http.getExpert(expertId.value), http.getExpertPackages('', expertId.value)]);
  expert.value = expertResult;
  packages.value = packageResult || [];
  selectedPackage.value = packages.value[0] || null;
  if (uni.getStorageSync('token')) {
    const [assetResult, profileResult] = await Promise.all([http.getNameAssets(), http.getMyProfile()]);
    assets.value = assetResult.items || [];
    profile.value = profileResult;
  }
};
const ensureLogin = () => {
  if (uni.getStorageSync('token')) return true;
  uni.navigateTo({ url: '/pages/login/login' });
  return false;
};
const startChat = async () => {
  if (!ensureLogin() || !selectedPackage.value) return;
  const thread = await http.createExpertChatThread({ expert_id: expert.value.id, package_id: selectedPackage.value.id });
  uni.navigateTo({ url: `/pages/marketplace/chat?thread_id=${thread.id}` });
};
const openOrder = () => {
  if (!ensureLogin()) return;
  Object.assign(orderForm, { naming_asset_id: assets.value[0]?.id || null, name: '', requirements: `请对名称进行专业精批，重点分析寓意、传播感和使用风险。` });
  orderOpen.value = true;
};
const selectAsset = event => {
  orderForm.naming_asset_id = assets.value[event.detail.value]?.id || null;
};
const createOrder = async () => {
  if (!selectedPackage.value) return uni.showToast({ title: '请选择服务套餐', icon: 'none' });
  if (!orderForm.naming_asset_id && !orderForm.name.trim()) return uni.showToast({ title: '请选择资产或输入名称', icon: 'none' });
  if (orderForm.requirements.trim().length < 5) return uni.showToast({ title: '请填写至少 5 个字需求', icon: 'none' });
  const payload = { expert_id: expert.value.id, package_id: selectedPackage.value.id, requirements: orderForm.requirements.trim() };
  if (orderForm.naming_asset_id) payload.naming_asset_id = orderForm.naming_asset_id;
  else Object.assign(payload, { name: orderForm.name.trim(), category: '企业名', moral: null });
  submitting.value = true;
  try {
    const order = await http.createExpertOrder(payload);
    orderOpen.value = false;
    uni.showModal({
      title: '订单已创建',
      content: `实付 ¥${order.amount}，是否前往支付宝沙箱支付？`,
      success: async result => {
        if (!result.confirm) return;
        const payWindow = openAlipayWindow();
        const payment = await http.startExpertAlipay(order.id);
        startAlipayPayment(payment, { pendingKey: PENDING_EXPERT_ALIPAY_KEY, payWindow });
      }
    });
  } finally {
    submitting.value = false;
  }
};
onLoad(query => { expertId.value = Number(query.id || 0); });
onShow(load);
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.detail-page { max-width: 1320px; margin: 0 auto; }
.breadcrumb { color: $text-secondary; font-size: 13px; margin: 8px 0 18px; }
.layout { display: grid; grid-template-columns: minmax(0,1fr) 310px; gap: 20px; align-items: start; }
.expert-banner,.intro-card,.package-card,.review-card,.booking-card,.side-card,.order-sheet { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.expert-banner { display: grid; grid-template-columns: 150px minmax(0,1fr) 220px; gap: 28px; align-items: center; padding: 32px; background: linear-gradient(135deg,#17243b,#24324a); color: #fff; overflow: hidden; }
.portrait { width: 126px; height: 126px; border-radius: 50%; border: 3px solid rgba(199,154,75,.8); display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.14); color: #f5d392; font-size: 52px; font-weight: 900; }
.name-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.expert-name { font-size: 36px; font-weight: 900; }
.badge { padding: 6px 12px; border-radius: 999px; background: #f5d392; color: $brand-primary; font-size: 13px; font-weight: 900; }
.rating { margin-top: 12px; color: rgba(255,255,255,.9); font-size: 18px; }
.tags { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }
.tags text { padding: 7px 14px; border-radius: 999px; border: 1px solid rgba(255,255,255,.32); color: rgba(255,255,255,.9); }
.stats { display: grid; gap: 14px; border-left: 1px solid rgba(255,255,255,.22); padding-left: 28px; }
.stats text { color: rgba(255,255,255,.7); font-size: 13px; }
.stats strong { float: right; color: #fff; }
.intro-card,.review-card { padding: 24px; margin-top: 18px; }
.section-title { color: $brand-primary; font-size: 18px; font-weight: 900; }
.intro { margin-top: 14px; color: #52647f; line-height: 1.8; }
.muted { color: $text-secondary; }
.block-title { margin: 24px 0 14px; }
.package-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 14px; }
.package-card { padding: 22px; cursor: pointer; }
.package-card.selected { border-color: $brand-gold; box-shadow: 0 18px 48px rgba(199,154,75,.14); }
.package-head { display: flex; justify-content: space-between; gap: 12px; }
.package-head strong { display: block; color: $brand-primary; font-size: 22px; }
.package-head text { display: block; color: $text-secondary; margin-top: 6px; font-size: 13px; }
.hot { background: #c79a4b; color: #fff!important; padding: 6px 10px; border-radius: 999px; margin: 0!important; }
.price { margin-top: 20px; color: $brand-primary; font-size: 30px; font-weight: 900; }
.desc { min-height: 70px; margin: 14px 0; color: #52647f; font-size: 13px; line-height: 1.7; }
.outline,.outline-full,.dark-full { margin: 0; border-radius: 8px; font-weight: 900; }
.outline { width: 100%; height: 38px; line-height: 38px; background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.5); }
.outline::after,.outline-full::after,.dark-full::after { border: none; }
.review-head { display: flex; justify-content: space-between; gap: 18px; align-items: center; }
.review-head strong { color: $brand-primary; font-size: 26px; }
.review-row { display: grid; grid-template-columns: 44px minmax(0,1fr); gap: 14px; margin-top: 20px; padding-top: 18px; border-top: 1px solid #eee7dc; }
.review-avatar { width: 44px; height: 44px; border-radius: 50%; background: $brand-primary; color: #f5d392; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.review-meta { color: $brand-primary; font-weight: 900; }
.review-text { color: #52647f; line-height: 1.7; margin-top: 6px; }
.booking-card,.side-card { padding: 24px; margin-bottom: 18px; }
.book-name { color: $brand-primary; font-size: 22px; font-weight: 900; }
.book-price { display: inline-block; margin-top: 22px; color: $brand-primary; font-size: 36px; font-weight: 900; }
.divider { height: 1px; background: #eee7dc; margin: 22px 0; }
.booking-title { color: $brand-primary; font-weight: 900; margin-bottom: 14px; }
.outline-full,.dark-full { width: 100%; height: 46px; line-height: 46px; margin-bottom: 12px; }
.outline-full { background: #fff; color: $brand-primary; border: 1px solid $brand-primary; }
.dark-full { background: $brand-primary; color: #f5d392; }
.guarantee { display: grid; grid-template-columns: 34px minmax(0,1fr); gap: 12px; margin-top: 18px; }
.guarantee-icon { width: 34px; height: 34px; border-radius: 50%; background: #fffbf2; color: #b68136; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.guarantee text:first-child { display: block; color: $brand-primary; font-size: 13px; font-weight: 900; }
.guarantee text:last-child { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }
.industry-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 12px; margin-top: 16px; }
.industry-grid text { color: $brand-primary; background: #fbfaf7; border: 1px solid #eee7dc; border-radius: 8px; padding: 10px; text-align: center; font-size: 13px; }
.overlay { position: fixed; inset: 0; z-index: 100; background: rgba(23,36,59,.52); display: flex; align-items: center; justify-content: center; padding: 30px; }
.order-sheet { width: min(620px,100%); padding: 26px; }
.field-label { color: $text-secondary; font-size: 13px; margin: 18px 0 8px; }
.input,.area { width: 100%; box-sizing: border-box; border: 1px solid #e7e0d4; border-radius: 8px; background: #fbfaf7; color: $text-main; font-size: 14px; }
.input { height: 44px; line-height: 44px; padding: 0 14px; }
.area { height: 120px; padding: 14px; line-height: 1.6; }
@media (max-width: 1120px) {
  .layout { grid-template-columns: 1fr; }
  .expert-banner { grid-template-columns: 120px minmax(0,1fr); }
  .stats { grid-column: span 2; border-left: none; padding-left: 0; border-top: 1px solid rgba(255,255,255,.22); padding-top: 18px; }
}
@media (max-width: 760px) {
  .expert-banner,.package-grid { grid-template-columns: 1fr; }
  .stats { grid-column: span 1; }
}
</style>
