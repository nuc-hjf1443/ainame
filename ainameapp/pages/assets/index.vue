<template>
  <DashboardLayout currentMenu="assets">
    <BrandKitPanel v-if="brandKitDraft" :draft="brandKitDraft" @back="closeBrandKit" />
    <view v-else class="assets-page">
      <view v-if="!token" class="login-panel">
        <view class="page-title">资产中心</view>
        <view class="muted">登录后管理收藏名字、品牌视觉方案和专家订单。</view>
        <button class="primary" @click="goLogin">登录 / 注册</button>
      </view>

      <template v-else>
        <view class="page-head">
          <view>
            <view class="page-title">资产中心</view>
            <view class="muted">集中管理名字收藏、企业视觉方案和精批订单。</view>
          </view>
        </view>

        <view class="tabs">
          <view v-for="item in tabs" :key="item.value" :class="['tab', tab === item.value ? 'active' : '']" @click="tab = item.value">{{ item.label }}</view>
        </view>

        <view v-if="tab === 'names'" class="panel">
          <view class="category-tabs">
            <view v-for="item in categories" :key="item" :class="['category-tab', category === item ? 'active' : '']" @click="category = item">{{ item }}</view>
          </view>
          <view class="asset-list">
            <view v-for="item in filteredNames" :key="item.id" class="name-card">
              <view class="name-main">
                <view class="asset-name">{{ item.name }}</view>
                <view class="muted">{{ item.category }} · {{ item.moral || '暂无寓意说明' }}</view>
                <view v-if="item.reference" class="reference">出处：{{ item.reference }}</view>
              </view>
              <view class="actions">
                <button size="mini" class="primary-mini" @click="openOrder(item)">精批</button>
                <button v-if="item.category === '企业名'" size="mini" class="dark-mini" @click="startBrandKit(item)">生成品牌视觉</button>
                <button size="mini" class="outline-mini" @click="removeName(item.id)">取消收藏</button>
              </view>
            </view>
            <view v-if="!filteredNames.length" class="empty">当前分类还没有收藏名字</view>
          </view>
        </view>

        <view v-if="tab === 'kits'" class="kit-grid">
          <view v-for="kit in brandKits" :key="kit.id" class="kit-card">
            <view class="kit-head">
              <view>
                <view class="asset-name">{{ kit.name }}</view>
                <view class="muted">{{ kit.moral || '暂无寓意说明' }}</view>
              </view>
              <text :class="['status', kit.status]">{{ statusText(kit.status) }}</text>
            </view>
            <view class="kit-info">
              <view><text>行业</text><text>{{ kit.industry }}</text></view>
              <view><text>用户</text><text>{{ kit.audience }}</text></view>
              <view><text>风格</text><text>{{ kit.design_style }}</text></view>
              <view><text>主色</text><text>{{ kit.primary_color }}</text></view>
            </view>
            <view class="visual-grid">
              <view v-for="asset in kit.assets" :key="asset.id" class="visual-tile">
                <image v-if="asset.image_url" :src="asset.image_url" mode="aspectFill" @click="previewKit(kit, asset.image_url)" />
                <view v-else class="visual-placeholder">{{ asset.status === 'FAILED' ? '失败' : '生成中' }}</view>
                <view class="visual-label">{{ assetLabel(asset) }}</view>
              </view>
            </view>
            <button class="danger-btn" @click="deleteKit(kit)">删除整套方案</button>
          </view>
          <view v-if="!brandKits.length" class="empty panel">还没有企业品牌视觉方案</view>
        </view>

        <view v-if="tab === 'orders'" class="panel">
          <view v-for="item in orders" :key="item.id" class="order-card">
            <view class="order-head">
              <view>
                <view class="asset-name">{{ item.asset_name }}</view>
                <view class="muted">{{ item.expert_name }} · {{ item.package_name }} · 实付 ¥{{ item.amount }}</view>
              </view>
              <text class="status">{{ orderStatusText(item.status) }}</text>
            </view>
            <view class="muted">需求：{{ item.requirements }}</view>
            <view class="actions">
              <button v-if="item.status === 'PENDING_PAYMENT'" size="mini" class="primary-mini" @click="pay(item.id)">支付宝支付</button>
              <button v-if="item.status === 'PENDING_PAYMENT' && item.out_trade_no" size="mini" class="outline-mini" @click="syncOrderPayment(item)">刷新支付状态</button>
              <button v-if="canCancel(item)" size="mini" class="outline-mini" @click="cancel(item)">取消订单</button>
              <button v-if="item.status === 'DELIVERED'" size="mini" class="primary-mini" @click="complete(item.id)">确认完成</button>
              <button v-if="item.status === 'COMPLETED' && !item.reviewed" size="mini" class="primary-mini" @click="openReview(item)">评价专家</button>
            </view>
            <view v-if="item.report" class="report">{{ item.report.conclusion }}</view>
          </view>
          <view v-if="!orders.length" class="empty">还没有专家订单</view>
        </view>
      </template>

      <view v-if="orderOpen" class="overlay" @click="closeOrder">
        <view class="sheet" @click.stop>
          <view class="sheet-title">为「{{ orderAsset?.name }}」选择精批专家</view>
          <view class="expert-grid">
            <view v-for="expert in experts" :key="expert.id" :class="['expert-card', selectedExpert?.id === expert.id ? 'selected' : '']" @click="selectExpert(expert)">
              <view class="expert-name">{{ expert.display_name }}</view>
              <view class="muted">{{ labelType(expert.expert_type) }} · {{ expert.years_experience }} 年经验</view>
              <view class="muted">★ {{ Number(expert.average_rating).toFixed(1) }} · {{ expert.review_count }} 条评价</view>
            </view>
          </view>
          <view class="field-label">服务套餐</view>
          <view class="package-list">
            <view v-for="item in selectedPackages" :key="item.id" :class="['package-card', orderForm.package_id === item.id ? 'selected' : '']" @click="orderForm.package_id = item.id">
              <text>{{ item.name }} · {{ item.delivery_days }} 天</text>
              <text>¥{{ payable(item) }}</text>
            </view>
          </view>
          <view class="field-label">精批需求</view>
          <textarea class="form-area" :value="orderForm.requirements" placeholder="说明希望专家重点分析的问题（至少5个字）" @input="orderForm.requirements = $event.detail.value" />
          <button class="primary" :loading="submitting" @click="createOrder">创建订单并支付</button>
        </view>
      </view>

      <view v-if="reviewOpen" class="overlay" @click="closeReview">
        <view class="sheet review-sheet" @click.stop>
          <view class="sheet-title">评价「{{ reviewOrder?.expert_name }}」</view>
          <view class="field-label">服务评分</view>
          <view class="rating-row">
            <view v-for="score in ratings" :key="score" :class="['rating-chip', reviewForm.rating === score ? 'selected' : '']" @click="reviewForm.rating = score">
              {{ score }} 星
            </view>
          </view>
          <view class="field-label">评价内容</view>
          <textarea class="form-area" :value="reviewForm.content" placeholder="可以补充专家分析是否专业、交付是否清晰（可选）" @input="reviewForm.content = $event.detail.value" />
          <view class="dialog-actions">
            <button class="outline" @click="closeReview">取消</button>
            <button class="primary" :loading="reviewSubmitting" @click="submitReview">提交评价</button>
          </view>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import BrandKitPanel from '@/components/BrandKitPanel/BrandKitPanel.vue';

const token = ref('');
const tab = ref('names');
const category = ref('全部');
const names = ref([]);
const brandKits = ref([]);
const orders = ref([]);
const experts = ref([]);
const packages = ref([]);
const profile = ref(null);
const brandKitDraft = ref(null);
const orderOpen = ref(false);
const orderAsset = ref(null);
const selectedExpert = ref(null);
const submitting = ref(false);
const reviewOpen = ref(false);
const reviewSubmitting = ref(false);
const reviewOrder = ref(null);
const orderForm = reactive({ package_id: null, requirements: '' });
const reviewForm = reactive({ rating: 5, content: '' });

const tabs = [{ label: '名字资产', value: 'names' }, { label: '企业视觉方案', value: 'kits' }, { label: '专家订单', value: 'orders' }];
const categories = ['全部', '人名', '企业名', '宠物名'];
const ratings = [5, 4, 3, 2, 1];
const filteredNames = computed(() => category.value === '全部' ? names.value : names.value.filter(item => item.category === category.value));
const selectedPackages = computed(() => selectedExpert.value ? packages.value.filter(item => item.expert_type === selectedExpert.value.expert_type) : []);
const labelType = value => value === 'CULTURE_MASTER' ? '国学命名专家' : '品牌咨询师';
const payable = item => profile.value?.is_vip ? (Number(item.price) * 0.9).toFixed(2) : Number(item.price).toFixed(2);
const statusText = value => ({ PENDING: '准备中', PROCESSING: '生成中', SUCCESS: '已完成', FAILED: '失败' }[value] || value);
const orderStatusText = value => ({
  PENDING_PAYMENT: '待支付',
  WAITING_ACCEPT: '待专家接单',
  IN_PROGRESS: '精批中',
  DELIVERED: '已交付',
  COMPLETED: '已完成',
  CANCELLED: '已取消'
}[value] || value || '-');
const paymentStatusText = value => ({
  PENDING: '待支付',
  PAID: '已支付',
  CANCELLED: '已取消',
  REFUNDED: '已退款'
}[value] || value || '-');
const assetLabel = asset => `${asset.asset_type === 'LOGO' ? 'Logo' : '名片'} ${asset.variant_index}`;
const redirectToAlipay = payment => {
  // #ifdef H5
  window.location.href = payment.payment_url;
  // #endif
  // #ifndef H5
  uni.showToast({ title: '当前仅 H5 支持支付宝沙箱支付', icon: 'none' });
  // #endif
};

const load = async () => {
  token.value = uni.getStorageSync('token');
  if (!token.value) return;
  const [nameResult, kitResult, orderResult, profileResult] = await Promise.all([
    http.getNameAssets(1, 100),
    http.getBrandKits(1, 50),
    http.getMyExpertOrders(1),
    http.getMyProfile()
  ]);
  names.value = nameResult.items || [];
  brandKits.value = kitResult.items || [];
  orders.value = orderResult.items || [];
  profile.value = profileResult;
  uni.setStorageSync('user', { ...(uni.getStorageSync('user') || {}), username: profileResult.username, email: profileResult.email, role: profileResult.role });
};

const loadOrderOptions = async () => {
  if (experts.value.length && packages.value.length) return;
  const [expertResult, packageResult] = await Promise.all([http.getExperts(1, ''), http.getExpertPackages()]);
  experts.value = expertResult.items || [];
  packages.value = packageResult || [];
};

const openOrder = async asset => {
  if (!token.value) return goLogin();
  orderAsset.value = asset;
  selectedExpert.value = null;
  Object.assign(orderForm, { package_id: null, requirements: `请对「${asset.name}」进行专业精批，重点分析寓意、传播感和使用风险。` });
  await loadOrderOptions();
  if (experts.value.length) selectExpert(experts.value[0]);
  orderOpen.value = true;
};

const selectExpert = expert => {
  selectedExpert.value = expert;
  orderForm.package_id = packages.value.find(item => item.expert_type === expert.expert_type)?.id || null;
};

const closeOrder = () => { orderOpen.value = false; orderAsset.value = null; selectedExpert.value = null; };

const createOrder = async () => {
  if (!selectedExpert.value) return uni.showToast({ title: '请选择专家', icon: 'none' });
  if (!orderForm.package_id) return uni.showToast({ title: '请选择服务套餐', icon: 'none' });
  if (orderForm.requirements.trim().length < 5) return uni.showToast({ title: '请填写至少 5 个字的需求', icon: 'none' });
  submitting.value = true;
  try {
    const order = await http.createExpertOrder({
      expert_id: selectedExpert.value.id,
      package_id: orderForm.package_id,
      naming_asset_id: orderAsset.value.id,
      requirements: orderForm.requirements.trim()
    });
    orderOpen.value = false;
    uni.showModal({
      title: '订单已创建',
      content: `实付 ¥${order.amount}，是否前往支付宝沙箱支付？`,
      success: async result => {
        if (result.confirm) {
          const payment = await http.startExpertAlipay(order.id);
          redirectToAlipay(payment);
        } else {
          tab.value = 'orders';
          await load();
        }
      }
    });
  } finally {
    submitting.value = false;
  }
};

const startBrandKit = asset => {
  brandKitDraft.value = {
    naming_asset_id: asset.id,
    thread_id: asset.thread_id,
    name: asset.name,
    moral: asset.moral || '',
    reference: asset.reference || '',
    industry_hint: asset.reference || ''
  };
};
const closeBrandKit = async () => { brandKitDraft.value = null; await load(); };
const previewKit = (kit, url) => uni.previewImage({ current: url, urls: kit.assets.filter(item => item.image_url).map(item => item.image_url) });
const removeName = id => uni.showModal({ title: '取消收藏', content: '确认取消收藏这个名字？', success: async result => { if (result.confirm) { await http.deleteNameAsset(id); await load(); } } });
const deleteKit = kit => uni.showModal({ title: '删除品牌视觉方案', content: `确认删除「${kit.name}」整套方案及其 Logo/名片？`, success: async result => { if (result.confirm) { await http.deleteBrandKit(kit.id); await load(); } } });
const pay = async id => { const payment = await http.startExpertAlipay(id); redirectToAlipay(payment); };
const syncOrderPayment = async order => {
  const result = await http.syncAlipayOrder(order.out_trade_no);
  uni.showToast({ title: result.status === 'PAID' ? '支付已同步' : `当前状态：${paymentStatusText(result.status)}`, icon: 'none' });
  await load();
};
const complete = async id => { await http.completeExpertOrder(id); await load(); };
const canCancel = order => ['PENDING_PAYMENT', 'WAITING_ACCEPT'].includes(order.status);
const cancel = order => uni.showModal({
  title: '取消订单',
  content: order.status === 'WAITING_ACCEPT' ? '订单已支付，取消后会尝试原路退款，确认继续？' : '确认取消这笔待支付订单？',
  success: async result => {
    if (result.confirm) {
      await http.cancelExpertOrder(order.id);
      await load();
    }
  }
});
const openReview = order => {
  reviewOrder.value = order;
  Object.assign(reviewForm, { rating: 5, content: '' });
  reviewOpen.value = true;
};
const closeReview = () => {
  reviewOpen.value = false;
  reviewOrder.value = null;
};
const submitReview = async () => {
  if (!reviewOrder.value) return;
  reviewSubmitting.value = true;
  try {
    await http.reviewExpertOrder(reviewOrder.value.id, {
      rating: reviewForm.rating,
      content: reviewForm.content.trim() || null
    });
    uni.showToast({ title: '评价已提交' });
    closeReview();
    await load();
  } finally {
    reviewSubmitting.value = false;
  }
};
const goLogin = () => uni.navigateTo({ url: '/pages/login/login' });

onLoad(query => { if (query.tab) tab.value = query.tab; });
onShow(load);
</script>

<style scoped>
.assets-page{min-height:100%;color:#111827}.login-panel,.panel{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:32rpx;margin-bottom:28rpx}.login-panel{text-align:center;padding:100rpx 30rpx}.page-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:28rpx}.page-title{font-size:44rpx;font-weight:800}.muted{display:block;color:#6b7280;font-size:24rpx;line-height:1.6;margin-top:6rpx}.tabs,.category-tabs{display:flex;gap:14rpx;overflow-x:auto;margin-bottom:24rpx}.tab,.category-tab{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:16rpx 28rpx;white-space:nowrap;color:#4b5563;font-size:27rpx}.tab.active,.category-tab.active{background:#eef2ff;color:#4f46e5;border-color:#c7d2fe;font-weight:700}.asset-list{display:flex;flex-direction:column;gap:18rpx}.name-card,.order-card,.kit-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:28rpx}.name-card{display:flex;justify-content:space-between;gap:24rpx}.name-main{min-width:0}.asset-name{font-size:32rpx;font-weight:800;color:#111827}.reference{font-size:24rpx;color:#4b5563;margin-top:10rpx}.actions{display:flex;gap:12rpx;flex-wrap:wrap;align-items:center}.actions button{margin:0}.primary,.primary-mini{background:#4f46e5;color:#fff}.dark-mini{background:#111827;color:#fff}.outline-mini{background:#fff;color:#4b5563;border:1px solid #d1d5db}.danger-btn{background:#fff;color:#dc2626;border:1px solid #fecaca;border-radius:8px;margin-top:24rpx}.kit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24rpx}.kit-head,.order-head{display:flex;justify-content:space-between;gap:20rpx;align-items:flex-start;margin-bottom:18rpx}.status{font-size:23rpx;color:#4f46e5;background:#eef2ff;border-radius:999px;padding:8rpx 16rpx;white-space:nowrap}.status.FAILED{color:#dc2626;background:#fee2e2}.kit-info{display:grid;grid-template-columns:repeat(2,1fr);gap:12rpx;border-top:1px solid #f3f4f6;border-bottom:1px solid #f3f4f6;padding:20rpx 0;margin:18rpx 0}.kit-info view{display:flex;justify-content:space-between;gap:16rpx;font-size:24rpx}.kit-info text:first-child{color:#6b7280}.visual-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12rpx}.visual-tile{background:#f9fafb;border:1px solid #eef0f4;min-width:0}.visual-tile image,.visual-placeholder{width:100%;height:160rpx}.visual-placeholder{display:flex;align-items:center;justify-content:center;color:#9ca3af}.visual-label{text-align:center;color:#4b5563;font-size:22rpx;padding:10rpx}.report{background:#f9fafb;border-radius:8px;padding:20rpx;margin-top:16rpx;color:#374151}.empty{text-align:center;color:#9ca3af;padding:60rpx}.overlay{position:fixed;inset:0;background:rgba(17,24,39,.48);z-index:200;display:flex;align-items:center;justify-content:center;padding:36rpx}.sheet{width:min(920rpx,100%);max-height:86vh;overflow-y:auto;background:#fff;border-radius:8px;padding:34rpx}.sheet-title{font-size:34rpx;font-weight:800;margin-bottom:24rpx}.expert-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16rpx}.expert-card,.package-card{border:1px solid #e5e7eb;border-radius:8px;padding:20rpx}.expert-card.selected,.package-card.selected{border-color:#4f46e5;background:#eef2ff}.expert-name{font-weight:800}.field-label{font-size:24rpx;color:#6b7280;margin:24rpx 0 12rpx}.package-list{display:flex;flex-direction:column;gap:12rpx}.package-card{display:flex;justify-content:space-between}.form-area{width:100%;height:160rpx;box-sizing:border-box;border:1px solid #d1d5db;border-radius:8px;padding:20rpx;font-size:27rpx}.primary{border-radius:8px;margin-top:24rpx}@media(max-width:900px){.kit-grid,.expert-grid{grid-template-columns:1fr}.name-card{flex-direction:column}.visual-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>

<style scoped>
.outline{background:#fff;color:#4b5563;border:1px solid #d1d5db;border-radius:8px}
.review-sheet{width:min(720rpx,100%)}
.rating-row{display:flex;gap:12rpx;flex-wrap:wrap}
.rating-chip{padding:14rpx 22rpx;border:1px solid #d1d5db;border-radius:999px;color:#4b5563;background:#fff;font-size:26rpx}
.rating-chip.selected{background:#eef2ff;border-color:#4f46e5;color:#4f46e5;font-weight:700}
.dialog-actions{display:flex;justify-content:flex-end;gap:14rpx}
.dialog-actions button{margin:24rpx 0 0}
</style>
