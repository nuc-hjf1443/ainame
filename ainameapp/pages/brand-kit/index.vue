<template>
  <DashboardLayout currentMenu="ai_name">
  <view class="page">
    <view v-if="!draft.name" class="empty-state">
      <view class="empty-title">请先选择企业名字</view>
      <button class="primary-btn" @click="goHome">返回企业起名</button>
    </view>

    <template v-else>
      <view class="brand-hero">
        <view class="hero-eyebrow">BRAND LAUNCH KIT</view>
        <view class="brand-name">{{ draft.name }}</view>
        <view class="brand-moral">{{ draft.moral || '为好名字建立清晰、统一的品牌表达' }}</view>
      </view>

      <view v-if="!kit" class="panel form-panel">
        <view class="panel-title">完善品牌信息</view>
        <view class="field-label">所属行业</view>
        <input class="field" :value="form.industry" placeholder="例如：射击小游戏公司" @input="form.industry = $event.detail.value" />
        <view class="field-label">目标用户</view>
        <input class="field" :value="form.audience" placeholder="例如：小学生、年轻游戏玩家" @input="form.audience = $event.detail.value" />
        <view class="field-label">视觉风格</view>
        <picker :range="styleOptions" @change="event => form.design_style = styleOptions[event.detail.value]"><view class="field picker">{{ form.design_style }}</view></picker>
        <view class="field-label">品牌主色</view>
        <picker :range="colorOptions" @change="event => form.primary_color = colorOptions[event.detail.value]"><view class="field picker"><text class="color-dot" :style="{ background: colorValue(form.primary_color) }"></text>{{ form.primary_color }}</view></picker>
        <button class="primary-btn" :loading="creating" @click="createKit">生成一键品牌方案</button>
      </view>

      <template v-else>
        <view class="panel summary-panel">
          <view class="panel-title">完整品牌信息</view>
          <view class="summary-row"><text>所属行业</text><text>{{ kit.industry }}</text></view>
          <view class="summary-row"><text>目标用户</text><text>{{ kit.audience }}</text></view>
          <view class="summary-row"><text>视觉风格</text><text>{{ kit.design_style }}</text></view>
          <view class="summary-row"><text>品牌主色</text><view class="summary-color"><text class="color-dot" :style="{ background: colorValue(kit.primary_color) }"></text>{{ kit.primary_color }}</view></view>
        </view>

        <view class="panel status-panel">
          <view class="status-head"><view><view class="panel-title">品牌方案</view><view class="status-copy">{{ statusText }}</view></view><button size="mini" class="refresh-btn" :loading="refreshing" @click="refreshKit">刷新状态</button></view>
          <view class="progress"><view class="progress-value" :style="{ width: `${progress}%` }"></view></view>
          <view class="material-count">已生成 {{ successCount }} / {{ kit.assets.length }} 份品牌素材</view>
        </view>

        <view class="panel material-panel">
          <view class="material-head"><view class="panel-title">品牌素材</view><view class="filters"><text :class="filter === 'ALL' ? 'active' : ''" @click="filter = 'ALL'">全部</text><text :class="filter === 'LOGO' ? 'active' : ''" @click="filter = 'LOGO'">Logo</text><text :class="filter === 'BUSINESS_CARD' ? 'active' : ''" @click="filter = 'BUSINESS_CARD'">名片</text></view></view>
          <view class="material-grid">
            <view v-for="asset in filteredAssets" :key="asset.id" class="material-item">
              <image v-if="asset.image_url" class="material-image" :src="asset.image_url" mode="aspectFill" @click="preview(asset.image_url)" />
              <view v-else :class="['material-placeholder', `variant-${asset.variant_index}`, asset.asset_type === 'BUSINESS_CARD' ? 'card-placeholder' : '']">
                <view class="logo-mark">{{ draft.name.slice(0, 1) }}</view>
                <view class="placeholder-name">{{ draft.name }}</view>
                <view class="placeholder-state">{{ asset.status === 'FAILED' ? '生成失败' : '生成中' }}</view>
              </view>
              <view class="material-label">{{ assetLabel(asset) }}</view>
              <view v-if="asset.status === 'FAILED'" class="asset-error">{{ asset.error_message || '素材生成失败' }}</view>
            </view>
          </view>
        </view>
      </template>
    </template>
  </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onLoad, onUnload } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const draft = reactive({ thread_id: '', name: '', moral: '', industry_hint: '' });
const form = reactive({ industry: '', audience: '', design_style: '现代简约', primary_color: '蓝色' });
const styleOptions = ['现代简约', '科技未来', '国潮东方', '活力潮玩', '高端商务'];
const colorOptions = ['蓝色', '绿色', '紫色', '红色', '黑金'];
const kit = ref(null);
const creating = ref(false);
const refreshing = ref(false);
const filter = ref('ALL');
let timer = null;
let pollCount = 0;

const successCount = computed(() => kit.value?.assets.filter(item => item.status === 'SUCCESS').length || 0);
const progress = computed(() => kit.value?.assets.length ? Math.round(kit.value.assets.filter(item => ['SUCCESS', 'FAILED'].includes(item.status)).length / kit.value.assets.length * 100) : 0);
const filteredAssets = computed(() => !kit.value ? [] : kit.value.assets.filter(item => filter.value === 'ALL' || item.asset_type === filter.value));
const statusText = computed(() => ({ PENDING: '方案已创建，正在准备素材', PROCESSING: 'AI 正在生成 Logo 与名片素材', SUCCESS: '品牌方案已生成', FAILED: '本次方案生成失败，额度已返还' }[kit.value?.status] || '正在处理'));
const colorMap = { 蓝色: '#3b5bdb', 绿色: '#0f9d87', 紫色: '#6d28d9', 红色: '#ef4444', 黑金: '#202938' };
const colorValue = name => colorMap[name] || '#3b5bdb';
const assetLabel = asset => `${asset.asset_type === 'LOGO' ? 'Logo 概念' : '名片概念'} ${asset.variant_index}`;

const stopPolling = () => { if (timer) clearInterval(timer); timer = null; };
const startPolling = () => {
  stopPolling();
  pollCount = 0;
  timer = setInterval(async () => {
    pollCount += 1;
    await refreshKit(true);
    if (['SUCCESS', 'FAILED'].includes(kit.value?.status) || pollCount >= 24) stopPolling();
  }, 5000);
};
const createKit = async () => {
  if (form.industry.trim().length < 2 || form.audience.trim().length < 2) return uni.showToast({ title: '请填写行业和目标用户', icon: 'none' });
  creating.value = true;
  try {
    kit.value = await http.createBrandKit({
      thread_id: draft.thread_id,
      name: draft.name,
      moral: draft.moral || '',
      category: '企业名',
      industry: form.industry.trim(),
      audience: form.audience.trim(),
      design_style: form.design_style,
      primary_color: form.primary_color,
      image_model: 'wan2.6-image'
    });
    uni.setStorageSync('activeBrandKit', { id: kit.value.id, name: kit.value.name });
    startPolling();
  } finally {
    creating.value = false;
  }
};
const refreshKit = async silent => {
  if (!kit.value?.id) return;
  if (!silent) refreshing.value = true;
  try { kit.value = await http.getBrandKit(kit.value.id); } finally { if (!silent) refreshing.value = false; }
};
const preview = url => uni.previewImage({ current: url, urls: kit.value.assets.filter(item => item.image_url).map(item => item.image_url) });
const goHome = () => uni.reLaunch({ url: '/pages/index/index' });

onLoad(async () => {
  Object.assign(draft, uni.getStorageSync('brandKitDraft') || {});
  form.industry = draft.industry_hint || '';
  const active = uni.getStorageSync('activeBrandKit') || {};
  if (active.id && active.name === draft.name) {
    try {
      kit.value = await http.getBrandKit(active.id);
      if (!['SUCCESS', 'FAILED'].includes(kit.value.status)) startPolling();
    } catch (error) {
      uni.removeStorageSync('activeBrandKit');
    }
  }
});
onUnload(stopPolling);
</script>

<style scoped>
.page{min-height:100vh;background:#f2f5f9;padding:28rpx;box-sizing:border-box;color:#111c35}.brand-hero{background:linear-gradient(120deg,#1f2a69,#5c1fc2);color:#fff;border-radius:8rpx;padding:46rpx 38rpx;margin-bottom:22rpx}.hero-eyebrow{font-size:22rpx;letter-spacing:8rpx;color:#d8c7ff}.brand-name{font-size:56rpx;font-weight:700;margin-top:28rpx}.brand-moral{font-size:27rpx;line-height:1.6;margin-top:16rpx;color:#ede9fe}.panel{background:#fff;border-radius:8rpx;padding:30rpx;margin-bottom:22rpx}.panel-title{font-size:34rpx;font-weight:700}.field-label{font-size:23rpx;color:#64748b;margin:24rpx 0 10rpx}.field{height:84rpx;width:100%;box-sizing:border-box;padding:0 20rpx;border:1px solid #dbe3ed;background:#f8fafc;border-radius:8rpx;font-size:27rpx}.picker{display:flex;align-items:center}.color-dot{display:inline-block;width:24rpx;height:24rpx;border-radius:50%;margin-right:14rpx;flex-shrink:0}.primary-btn{background:#5245e8;color:#fff;border-radius:40rpx;margin-top:28rpx}.summary-panel{padding-bottom:12rpx}.summary-row{display:flex;justify-content:space-between;gap:30rpx;padding:24rpx 0;border-bottom:1px solid #e5eaf0;font-size:27rpx}.summary-row>text:first-child{color:#64748b}.summary-row>text:last-child{text-align:right}.summary-color{display:flex;align-items:center}.status-head,.material-head{display:flex;align-items:center;justify-content:space-between;gap:20rpx}.status-copy{font-size:23rpx;color:#64748b;margin-top:8rpx}.refresh-btn{margin:0;background:#fff;color:#4f46e5;border:1px solid #c7d2fe}.progress{height:14rpx;background:#e2e8f0;margin-top:24rpx;overflow:hidden}.progress-value{height:100%;background:#5245e8;transition:width .3s}.material-count{text-align:center;color:#4f46e5;font-size:24rpx;margin-top:18rpx}.filters{display:flex;gap:8rpx}.filters text{font-size:22rpx;padding:9rpx 14rpx;color:#64748b}.filters .active{background:#eef2ff;color:#4338ca}.material-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18rpx;margin-top:24rpx}.material-item{background:#f8fafc;border:1px solid #e5eaf0;min-width:0}.material-image,.material-placeholder{width:100%;height:310rpx}.material-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;background:#f4f7fb}.card-placeholder{background:linear-gradient(145deg,#f8fafc 0 48%,#e7ecf5 48% 52%,#f8fafc 52%)}.logo-mark{width:104rpx;height:104rpx;transform:rotate(45deg);background:#3b5bdb;color:#fff;display:flex;align-items:center;justify-content:center;font-size:42rpx;font-weight:700}.logo-mark::first-letter{transform:rotate(-45deg)}.variant-2 .logo-mark{background:#0f9d87;border-radius:50%}.placeholder-name{font-weight:700;font-size:27rpx;margin-top:24rpx}.placeholder-state{font-size:20rpx;color:#94a3b8;margin-top:6rpx}.material-label{padding:18rpx;text-align:center;color:#52647f;font-size:25rpx}.asset-error{padding:0 14rpx 14rpx;color:#dc2626;font-size:20rpx}.empty-state{text-align:center;background:#fff;padding:100rpx 30rpx}.empty-title{font-size:34rpx;font-weight:700}@media(min-width:900px){.page{max-width:960px;margin:0 auto}.material-grid{grid-template-columns:repeat(4,1fr)}.material-image,.material-placeholder{height:260rpx}}@media(max-width:360px){.material-grid{grid-template-columns:1fr}}
</style>
