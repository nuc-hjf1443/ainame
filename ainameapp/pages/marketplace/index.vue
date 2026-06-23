<template>
  <view class="page">
    <view class="hero">
      <view class="hero-title">真人专家精批</view>
      <view class="hero-copy">AI 提效，专家审核，为重要名字提供更有分量的决策依据。</view>
    </view>

    <view class="filters">
      <view v-for="item in types" :key="item.value" :class="['chip', type === item.value ? 'active' : '']" @click="setType(item.value)">{{ item.label }}</view>
    </view>

    <view v-if="loading" class="state">正在加载专家...</view>
    <view v-else-if="!experts.length" class="state">暂无已认证专家</view>
    <view v-else class="expert-list">
      <view v-for="expert in experts" :key="expert.id" class="expert-card">
        <view class="expert-head">
          <view class="avatar">{{ expert.display_name.slice(0, 1) }}</view>
          <view class="expert-main">
            <view class="name-line"><text class="expert-name">{{ expert.display_name }}</text><text class="verified">已认证</text></view>
            <view class="expert-type">平台认证专家 · {{ labelType(expert.expert_type) }}</view>
          </view>
        </view>
        <view class="service-title">{{ primaryPackage(expert)?.name || labelType(expert.expert_type) }}</view>
        <view class="bio">{{ expert.bio }}</view>
        <view class="card-footer">
          <view>
            <text class="price">{{ primaryPackage(expert) ? `¥${primaryPackage(expert).price}` : '暂无套餐' }}</text>
            <text class="rating">★ {{ Number(expert.average_rating).toFixed(1) }}（{{ expert.review_count }}）</text>
          </view>
          <button class="consult-btn" size="mini" :disabled="!primaryPackage(expert)" @click="openOrder(expert)">立即咨询</button>
        </view>
      </view>
    </view>

    <view v-if="orderOpen" class="overlay" @click="closeOrder">
      <view class="sheet" @click.stop>
        <view class="sheet-handle"></view>
        <view class="sheet-head"><view><view class="sheet-title">提交精批需求</view><view class="sheet-sub">{{ selectedExpert.display_name }} · {{ labelType(selectedExpert.expert_type) }}</view></view><text class="close" @click="closeOrder">×</text></view>

        <view class="field-label">服务套餐</view>
        <view class="package-list">
          <view v-for="item in selectedPackages" :key="item.id" :class="['package', form.package_id === item.id ? 'selected' : '']" @click="form.package_id = item.id">
            <view><view class="package-name">{{ item.name }}</view><view class="package-desc">{{ item.delivery_days }} 天交付 · {{ item.description }}</view></view>
            <view class="package-price"><text v-if="profile?.is_vip" class="old-price">¥{{ item.price }}</text><text>¥{{ payable(item) }}</text></view>
          </view>
        </view>
        <view v-if="profile?.is_vip" class="vip-tip">VIP 专家服务享 9 折</view>

        <view class="mode-tabs">
          <view :class="['mode-tab', mode === 'asset' ? 'active' : '']" @click="mode = 'asset'">选择已收藏资产</view>
          <view :class="['mode-tab', mode === 'manual' ? 'active' : '']" @click="mode = 'manual'">直接输入名字</view>
        </view>

        <template v-if="mode === 'asset'">
          <picker :range="assetLabels" @change="selectAsset"><view class="form-input picker">{{ selectedAssetLabel }}</view></picker>
          <view v-if="!assets.length" class="field-help">暂无收藏资产，可切换为直接输入。</view>
        </template>
        <template v-else>
          <input class="form-input" :value="form.name" placeholder="需要精批的姓名或品牌名" @input="form.name = $event.detail.value" />
          <picker :range="categoryLabels" @change="e => form.category = categoryLabels[e.detail.value]"><view class="form-input picker">分类：{{ form.category }}</view></picker>
          <textarea class="form-area compact" :value="form.moral" placeholder="名字寓意（可选）" @input="form.moral = $event.detail.value" />
        </template>
        <textarea class="form-area" :value="form.requirements" placeholder="详细说明背景、用途和关注点（至少 5 个字）" @input="form.requirements = $event.detail.value" />
        <button class="submit-btn" :loading="submitting" @click="createOrder">创建订单</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

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
const types = [{ label: '全部', value: '' }, { label: '国学命名', value: 'CULTURE_MASTER' }, { label: '品牌咨询', value: 'BRAND_CONSULTANT' }];
const categoryLabels = ['人名', '企业名', '宠物名'];
const form = reactive({ package_id: null, naming_asset_id: null, name: '', category: '企业名', moral: '', requirements: '' });

const labelType = value => value === 'CULTURE_MASTER' ? '国学命名专家' : '品牌咨询师';
const primaryPackage = expert => packages.value.find(item => item.expert_type === expert.expert_type);
const selectedPackages = computed(() => selectedExpert.value ? packages.value.filter(item => item.expert_type === selectedExpert.value.expert_type) : []);
const assetLabels = computed(() => assets.value.map(item => `${item.name} · ${item.category}`));
const selectedAssetLabel = computed(() => assets.value.find(item => item.id === form.naming_asset_id)?.name || '请选择已收藏的名字');
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
    } else {
      assets.value = [];
      profile.value = null;
    }
  } finally {
    loading.value = false;
  }
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
      uni.switchTab({ url: '/pages/profile/index' });
    }});
  } finally {
    submitting.value = false;
  }
};

onShow(load);
</script>

<style scoped>
.page{min-height:100vh;background:#f3f5f6;padding:28rpx;box-sizing:border-box;color:#102129}.hero{background:#0b695b;color:#fff;padding:42rpx 34rpx;border-radius:8rpx}.hero-title{font-size:42rpx;font-weight:700}.hero-copy{font-size:27rpx;line-height:1.65;margin-top:16rpx}.filters{display:flex;gap:12rpx;margin:24rpx 0;overflow-x:auto}.chip{padding:14rpx 22rpx;background:#fff;border:1px solid #dce5e4;border-radius:8rpx;white-space:nowrap;font-size:25rpx}.chip.active{background:#0f766e;color:#fff}.expert-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20rpx}.expert-card{background:#fff;border:1px solid #e4e9ec;border-radius:8rpx;padding:28rpx}.expert-head{display:flex;gap:20rpx;align-items:center}.avatar{width:84rpx;height:84rpx;border-radius:50%;background:#c9f7e5;color:#0f766e;display:flex;align-items:center;justify-content:center;font-size:36rpx;flex-shrink:0}.name-line{display:flex;gap:12rpx;align-items:center}.expert-name{font-size:31rpx;font-weight:700}.verified{color:#087f5b;font-size:21rpx}.expert-type{color:#64748b;font-size:23rpx;margin-top:6rpx}.service-title{font-size:31rpx;font-weight:700;margin-top:26rpx}.bio{color:#64748b;font-size:24rpx;line-height:1.55;margin-top:10rpx;min-height:74rpx;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.card-footer{display:flex;align-items:flex-end;justify-content:space-between;gap:18rpx;margin-top:24rpx}.price{display:block;color:#e65300;font-size:32rpx;font-weight:700}.rating{display:block;color:#0f766e;font-size:22rpx;margin-top:7rpx}.consult-btn,.submit-btn{background:#0f766e;color:#fff;border-radius:8rpx}.state{text-align:center;padding:100rpx 0;color:#64748b}.overlay{position:fixed;inset:0;background:rgba(15,23,42,.46);display:flex;align-items:flex-end;justify-content:center;z-index:50}.sheet{width:min(760rpx,100%);max-height:88vh;overflow-y:auto;background:#fff;border-radius:8rpx 8rpx 0 0;padding:22rpx 30rpx 34rpx;box-sizing:border-box}.sheet-handle{width:70rpx;height:7rpx;background:#cbd5e1;margin:0 auto 20rpx}.sheet-head{display:flex;justify-content:space-between;gap:20rpx}.sheet-title{font-size:34rpx;font-weight:700}.sheet-sub{color:#0f766e;font-size:23rpx;margin-top:6rpx}.close{font-size:48rpx;line-height:1}.field-label{font-size:24rpx;color:#64748b;margin:26rpx 0 10rpx}.package{border:1px solid #dbe3e7;border-radius:8rpx;padding:18rpx;display:flex;justify-content:space-between;gap:18rpx;margin-bottom:12rpx}.package.selected{border-color:#0f766e;background:#effcf8}.package-name{font-weight:700}.package-desc{font-size:22rpx;color:#64748b;margin-top:6rpx}.package-price{color:#e65300;font-weight:700;text-align:right;white-space:nowrap}.old-price{display:block;color:#94a3b8;text-decoration:line-through;font-size:21rpx}.vip-tip{color:#b45309;background:#fffbeb;padding:12rpx 16rpx;font-size:23rpx}.mode-tabs{display:grid;grid-template-columns:1fr 1fr;margin:24rpx 0 16rpx;border:1px solid #dbe3e7}.mode-tab{text-align:center;padding:18rpx;font-size:24rpx}.mode-tab.active{background:#0f766e;color:#fff}.form-input,.form-area{width:100%;box-sizing:border-box;border:1px solid #dbe3e7;background:#f8fafc;border-radius:8rpx;font-size:26rpx}.form-input{height:82rpx;padding:0 18rpx;margin-bottom:14rpx}.picker{display:flex;align-items:center}.form-area{height:170rpx;padding:18rpx;margin-bottom:16rpx}.form-area.compact{height:110rpx}.field-help{color:#94a3b8;font-size:22rpx;margin:-4rpx 0 14rpx}.submit-btn{margin-top:8rpx}@media(max-width:700px){.expert-list{grid-template-columns:1fr}}@media(min-width:900px){.page{max-width:1000px;margin:0 auto}}
</style>
