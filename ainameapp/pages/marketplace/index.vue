<template>
  <DashboardLayout currentMenu="expert" pageTitle="专家服务">
    <view class="content-inner">
      
      <view class="hero-section">
        <view class="hero-title">真人专家精批</view>
        <view class="hero-copy">AI 提效，专家审核，为重要名字提供更有分量的决策依据。</view>
      </view>

      <view class="filters">
        <view v-for="item in types" :key="item.value" 
              :class="['chip', type === item.value ? 'active' : '']" 
              @click="setType(item.value)">
          {{ item.label }}
        </view>
      </view>

      <view v-if="loading" class="state-box">
        <text class="state-text">正在加载专家列表...</text>
      </view>
      <view v-else-if="!experts.length" class="state-box">
        <text class="state-text">暂无已认证专家</text>
      </view>

      <view v-else class="expert-list">
        <view v-for="expert in experts" :key="expert.id" class="expert-card">
          <view class="expert-head">
            <view class="avatar">{{ expert.display_name.slice(0, 1) }}</view>
            <view class="expert-main">
              <view class="name-line">
                <text class="expert-name">{{ expert.display_name }}</text>
                <text class="verified">✅ 已认证</text>
              </view>
              <view class="expert-type">平台认证专家 · {{ labelType(expert.expert_type) }}</view>
            </view>
          </view>
          
          <view class="service-title">{{ primaryPackage(expert)?.name || labelType(expert.expert_type) }}</view>
          <view class="bio">{{ expert.bio }}</view>
          
          <view class="card-footer">
            <view class="price-info">
              <text class="price">{{ primaryPackage(expert) ? `¥${primaryPackage(expert).price}` : '暂无套餐' }}</text>
              <text class="rating">★ {{ Number(expert.average_rating).toFixed(1) }}（{{ expert.review_count }} 条评价）</text>
            </view>
            <button class="consult-btn" :disabled="!primaryPackage(expert)" @click="openOrder(expert)">
              立即咨询
            </button>
          </view>
        </view>
      </view>

      <view v-if="orderOpen" class="overlay" @click="closeOrder">
        <view class="sheet" @click.stop>
          <view class="sheet-handle"></view>
          <view class="sheet-head">
            <view>
              <view class="sheet-title">提交精批需求</view>
              <view class="sheet-sub">{{ selectedExpert?.display_name }} · {{ labelType(selectedExpert?.expert_type) }}</view>
            </view>
            <view class="close-btn" @click="closeOrder">×</view>
          </view>

          <view class="field-label">选择服务套餐</view>
          <view class="package-list">
            <view v-for="item in selectedPackages" :key="item.id" 
                  :class="['package-card', form.package_id === item.id ? 'selected' : '']" 
                  @click="form.package_id = item.id">
              <view class="package-info">
                <view class="package-name">{{ item.name }}</view>
                <view class="package-desc">交付周期: {{ item.delivery_days }} 天 · {{ item.description }}</view>
              </view>
              <view class="package-price">
                <text v-if="profile?.is_vip" class="old-price">¥{{ item.price }}</text>
                <text class="current-price">¥{{ payable(item) }}</text>
              </view>
            </view>
          </view>
          
          <view v-if="profile?.is_vip" class="vip-tip">👑 尊贵的 VIP 用户，您在此专家服务中专享 9 折特权</view>

          <view class="field-label" style="margin-top: 32rpx;">选择需求模式</view>
          <view class="mode-tabs">
            <view :class="['mode-tab', mode === 'asset' ? 'active' : '']" @click="mode = 'asset'">选择已收藏资产</view>
            <view :class="['mode-tab', mode === 'manual' ? 'active' : '']" @click="mode = 'manual'">直接输入名字</view>
          </view>

          <template v-if="mode === 'asset'">
            <picker :range="assetLabels" @change="selectAsset">
              <view class="form-input picker">
                <text>{{ selectedAssetLabel }}</text>
                <text class="arrow">▼</text>
              </view>
            </picker>
          </template>
          
          <template v-else>
            <input class="form-input" :value="form.name" placeholder="请输入需要精批的姓名或品牌名" @input="form.name = $event.detail.value" />
            <picker :range="categoryLabels" @change="e => form.category = categoryLabels[e.detail.value]">
              <view class="form-input picker">
                <text>起名分类：{{ form.category }}</text>
                <text class="arrow">▼</text>
              </view>
            </picker>
            <textarea class="form-area compact" :value="form.moral" placeholder="有什么特殊的寓意或期待？（可选）" @input="form.moral = $event.detail.value" />
          </template>
          
          <view class="field-label" style="margin-top: 16rpx;">需求补充说明</view>
          <textarea class="form-area" :value="form.requirements" placeholder="请详细说明起名背景、用途和特殊关注点（至少 5 个字）" @input="form.requirements = $event.detail.value" />
          
          <button class="btn-primary submit-btn" :loading="submitting" @click="createOrder">
            创建订单并支付
          </button>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const experts = ref([]);
const packages = ref([]);
const assets = ref([]);
const profile = ref(null);
const loading = ref(false);
const submitting = ref(false);
const type = ref('');
const orderOpen = ref(false);
const selectedExpert = ref(null);
const mode = ref('asset');
const types = [{ label: '全部专家', value: '' }, { label: '国学命名', value: 'CULTURE_MASTER' }, { label: '品牌咨询', value: 'BRAND_CONSULTANT' }];
const categoryLabels = ['人名', '企业名', '宠物名'];
const form = reactive({ package_id: null, naming_asset_id: null, name: '', category: '企业名', moral: '', requirements: '' });

const labelType = value => value === 'CULTURE_MASTER' ? '国学命名专家' : '品牌咨询师';
const primaryPackage = expert => packages.value.find(item => item.expert_type === expert.expert_type);
const selectedPackages = computed(() => selectedExpert.value ? packages.value.filter(item => item.expert_type === selectedExpert.value.expert_type) : []);
const assetLabels = computed(() => assets.value.map(item => `${item.name} · ${item.category}`));
const selectedAssetLabel = computed(() => assets.value.find(item => item.id === form.naming_asset_id)?.name || '请点击选择已收藏的名字');
const payable = item => profile.value?.is_vip ? (Number(item.price) * 0.9).toFixed(2) : Number(item.price).toFixed(2);

const load = async () => {
  loading.value = true;
  try {
    const [expertResult, packageResult] = await Promise.all([http.getExperts(1, type.value), http.getExpertPackages()]);
    experts.value = expertResult.items || [];
    packages.value = packageResult || [];
    if (uni.getStorageSync('token')) {
      const [assetResult, profileResult] = await Promise.all([http.getNameAssets(), http.getMyProfile()]);
      assets.value = assetResult.items || [];
      profile.value = profileResult;
    }
  } catch (e) { console.error(e); } finally { loading.value = false; }
};

const setType = value => { type.value = value; load(); };
const resetForm = () => Object.assign(form, { package_id: null, naming_asset_id: null, name: '', category: '企业名', moral: '', requirements: '' });
const openOrder = expert => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  selectedExpert.value = expert;
  resetForm();
  form.package_id = primaryPackage(expert)?.id || null;
  mode.value = assets.value.length ? 'asset' : 'manual';
  orderOpen.value = true;
};
const closeOrder = () => { orderOpen.value = false; selectedExpert.value = null; };
const selectAsset = event => { form.naming_asset_id = assets.value[event.detail.value]?.id || null; };

const createOrder = async () => {
  if (!form.package_id) return uni.showToast({ title: '请选择服务套餐', icon: 'none' });
  if (mode.value === 'asset' && !form.naming_asset_id) return uni.showToast({ title: '请选择名字资产', icon: 'none' });
  if (mode.value === 'manual' && !form.name.trim()) return uni.showToast({ title: '请输入需要精批的名字', icon: 'none' });
  if (form.requirements.trim().length < 5) return uni.showToast({ title: '请填写至少 5 个字的详细需求', icon: 'none' });
  const payload = { expert_id: selectedExpert.value.id, package_id: form.package_id, requirements: form.requirements.trim() };
  if (mode.value === 'asset') payload.naming_asset_id = form.naming_asset_id;
  else Object.assign(payload, { name: form.name.trim(), category: form.category, moral: form.moral.trim() || null });
  submitting.value = true;
  try {
    const order = await http.createExpertOrder(payload);
    orderOpen.value = false;
    uni.showModal({ title: '订单已创建', content: `实付 ¥${order.amount}，是否立即模拟支付？`, success: async result => {
      if (result.confirm) await http.payExpertOrder(order.id);
      uni.reLaunch({ url: '/pages/assets/index?tab=orders' });
    }});
  } finally { submitting.value = false; }
};

onShow(load);
</script>

<style lang="scss" scoped>
.content-inner { max-width: 1200px; margin: 0 auto; }
.hero-section { background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #FFFFFF; padding: 48rpx 40rpx; border-radius: 24rpx; margin-bottom: 40rpx; }
.hero-title { font-size: 48rpx; font-weight: 800; }
.hero-copy { font-size: 28rpx; margin-top: 12rpx; opacity: 0.9; }
.filters { display: flex; gap: 16rpx; margin-bottom: 40rpx; overflow-x: auto; }
.chip { padding: 14rpx 32rpx; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 999px; font-size: 26rpx; cursor: pointer; }
.chip.active { background: #EEF2FF; color: #4F46E5; border-color: #A5B4FC; }
.expert-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 32rpx; }
.expert-card { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 24rpx; padding: 40rpx; }
.expert-head { display: flex; gap: 24rpx; align-items: center; margin-bottom: 24rpx; }
.avatar { width: 96rpx; height: 96rpx; border-radius: 50%; background: #EEF2FF; color: #4F46E5; display: flex; align-items: center; justify-content: center; font-size: 40rpx; font-weight: 800; }
.expert-name { font-size: 34rpx; font-weight: 700; }
.expert-type { color: #6B7280; font-size: 24rpx; margin-top: 8rpx; }
.service-title { font-size: 30rpx; font-weight: 700; margin-bottom: 12rpx; }
.bio { color: #4B5563; font-size: 26rpx; line-height: 1.6; margin-bottom: 32rpx; height: 80rpx; overflow: hidden; }
.card-footer { display: flex; align-items: flex-end; justify-content: space-between; border-top: 1px solid #F3F4F6; padding-top: 24rpx; }
.price { color: #DC2626; font-size: 36rpx; font-weight: 800; }
.rating { color: #F59E0B; font-size: 24rpx; margin-left: 12rpx; }
.consult-btn { background: #4F46E5; color: #FFFFFF; border-radius: 12rpx; font-size: 26rpx; padding: 0 32rpx; height: 72rpx; line-height: 72rpx; }
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: flex-end; }
.sheet { width: 100%; max-height: 80vh; background: #FFFFFF; border-radius: 24rpx 24rpx 0 0; padding: 40rpx; box-sizing: border-box; }
.form-input { height: 96rpx; border: 1px solid #D1D5DB; border-radius: 16rpx; margin-bottom: 24rpx; padding: 0 32rpx; }
.form-area { height: 200rpx; border: 1px solid #D1D5DB; border-radius: 16rpx; padding: 24rpx 32rpx; width: 100%; box-sizing: border-box; margin-bottom: 24rpx; }
.submit-btn { background: #4F46E5; color: #FFFFFF; height: 96rpx; border-radius: 16rpx; line-height: 96rpx; }
@media (max-width: 768px) {
  .expert-list { grid-template-columns: 1fr; }
  .expert-card { padding: 32rpx; }
  .card-footer { align-items: stretch; flex-direction: column; gap: 24rpx; }
  .consult-btn { width: 100%; }
}
</style>
