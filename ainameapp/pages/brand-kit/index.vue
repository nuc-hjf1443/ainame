<template>
  <DashboardLayout currentMenu="brand">
  <view class="page">
    <view v-if="!draft.name && !kit" class="empty-state">
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
        <view class="field-label">生图模型</view>
        <picker :range="modelOptionLabels" @change="event => form.image_model = modelOptions[event.detail.value].value"><view class="field picker">{{ modelText(form.image_model) }}</view></picker>
        <button class="primary-btn" :loading="creating" @click="createKit">生成一键品牌方案</button>
      </view>

      <template v-else>
        <view class="panel summary-panel">
          <view class="panel-title">完整品牌信息</view>
          <view class="summary-row"><text>所属行业</text><text>{{ kit.industry }}</text></view>
          <view class="summary-row"><text>目标用户</text><text>{{ kit.audience }}</text></view>
          <view class="summary-row"><text>视觉风格</text><text>{{ kit.design_style }}</text></view>
          <view class="summary-row"><text>品牌主色</text><view class="summary-color"><text class="color-dot" :style="{ background: colorValue(kit.primary_color) }"></text>{{ kit.primary_color }}</view></view>
          <view class="summary-row"><text>生图模型</text><text>{{ modelText(kit.image_model) }}</text></view>
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
              <image v-if="assetImageUrl(asset) && !brokenImages[asset.id]" class="material-image" :src="assetImageUrl(asset)" mode="aspectFill" @click="preview(assetImageUrl(asset))" @error="markImageBroken(asset)" />
              <view v-else :class="['material-placeholder', `variant-${asset.variant_index}`, asset.asset_type === 'BUSINESS_CARD' ? 'card-placeholder' : '']">
                <view class="logo-mark">{{ draft.name.slice(0, 1) }}</view>
                <view class="placeholder-name">{{ draft.name }}</view>
                <view class="placeholder-state">{{ asset.status === 'FAILED' ? '生成失败' : '生成中' }}</view>
              </view>
              <view class="material-label">{{ assetLabel(asset) }}</view>
              <view class="material-actions">
                <button size="mini" :loading="regeneratingAssets[asset.id]" :disabled="['PENDING','PROCESSING'].includes(asset.status)" @click="regenerateAsset(asset)">重新生成</button>
              </view>
              <view v-if="asset.status === 'FAILED'" class="asset-error">{{ assetErrorText(asset.error_message) }}</view>
              <view v-else-if="brokenImages[asset.id]" class="asset-error">图片地址不可用，建议刷新状态或重新生成</view>
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
const form = reactive({ industry: '', audience: '', design_style: '现代简约', primary_color: '蓝色', image_model: 'wan2.7-image' });
const styleOptions = ['现代简约', '科技未来', '国潮东方', '活力潮玩', '高端商务'];
const colorOptions = ['蓝色', '绿色', '紫色', '红色', '黑金'];
const modelOptions = [
  { label: 'wan2.7-image（更快）', value: 'wan2.7-image' },
  { label: 'wan2.7-image-pro（高质量）', value: 'wan2.7-image-pro' },
  { label: 'wan2.6-t2i（兼容）', value: 'wan2.6-t2i' }
];
const modelOptionLabels = computed(() => modelOptions.map(item => item.label));
const kit = ref(null);
const creating = ref(false);
const refreshing = ref(false);
const filter = ref('ALL');
const brokenImages = reactive({});
const regeneratingAssets = reactive({});
let timer = null;
let pollCount = 0;

const successCount = computed(() => kit.value?.assets.filter(item => item.status === 'SUCCESS').length || 0);
const progress = computed(() => kit.value?.assets.length ? Math.round(kit.value.assets.filter(item => ['SUCCESS', 'FAILED'].includes(item.status)).length / kit.value.assets.length * 100) : 0);
const filteredAssets = computed(() => !kit.value ? [] : kit.value.assets.filter(item => filter.value === 'ALL' || item.asset_type === filter.value));
const statusText = computed(() => ({ PENDING: '方案已创建，正在准备素材', PROCESSING: 'AI 正在生成 Logo 与名片素材', SUCCESS: '品牌方案已生成', FAILED: '本次方案生成失败，额度已返还' }[kit.value?.status] || '正在处理'));
const colorMap = { 蓝色: '#3b5bdb', 绿色: '#0f9d87', 紫色: '#6d28d9', 红色: '#ef4444', 黑金: '#202938' };
const colorValue = name => colorMap[name] || '#3b5bdb';
const modelText = value => modelOptions.find(item => item.value === value)?.label || value || '-';
const assetImageUrl = asset => http.normalizeAssetUrl(asset?.image_url);
const assetLabel = asset => `${asset.asset_type === 'LOGO' ? 'Logo 概念' : '名片概念'} ${asset.variant_index}`;
const assetErrorText = message => {
  const value = String(message || '').toLowerCase();
  if (!value) return '素材生成失败，请稍后重试';
  if (value.includes('incomplete chunked read') || value.includes('peer closed connection')) {
    return '视觉生成服务连接中断，请稍后刷新状态或重新生成';
  }
  return message;
};
const markImageBroken = asset => { brokenImages[asset.id] = true; };
const chooseModel = () => new Promise(resolve => {
  uni.showActionSheet({
    itemList: modelOptionLabels.value,
    success: res => resolve(modelOptions[res.tapIndex]?.value || form.image_model),
    fail: () => resolve(null)
  });
});

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
      image_model: form.image_model
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
  try {
    kit.value = await http.getBrandKit(kit.value.id);
  } catch (error) {
    stopPolling();
    uni.removeStorageSync('activeBrandKit');
    kit.value = null;
    uni.showToast({ title: '生成失败，额度已退回，请重新生成', icon: 'none' });
  } finally {
    if (!silent) refreshing.value = false;
  }
};
const regenerateAsset = async asset => {
  const imageModel = await chooseModel();
  if (!imageModel || !kit.value?.id) return;
  regeneratingAssets[asset.id] = true;
  try {
    delete brokenImages[asset.id];
    kit.value = await http.regenerateBrandKitAsset(kit.value.id, asset.id, { image_model: imageModel });
    startPolling();
  } finally {
    regeneratingAssets[asset.id] = false;
  }
};
const preview = url => uni.previewImage({ current: url, urls: kit.value.assets.map(assetImageUrl).filter(Boolean) });
const goHome = () => uni.reLaunch({ url: '/pages/home/index' });

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
  if (!kit.value && !draft.name && uni.getStorageSync('token')) {
    const result = await http.getBrandKits(1, 1);
    const latest = result.items?.[0];
    if (latest) {
      kit.value = latest;
      Object.assign(draft, {
        thread_id: `kit_${latest.id}`,
        name: latest.name,
        moral: latest.moral || '',
        industry_hint: latest.industry
      });
      if (!['SUCCESS', 'FAILED'].includes(latest.status)) startPolling();
    }
  }
});
onUnload(stopPolling);
</script>

<style scoped>
.page{min-height:100%;box-sizing:border-box;color:#17243b}.brand-hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#17243b,#24324a);color:#fff;border-radius:12px;padding:44px 36px;margin-bottom:22px;border:1px solid rgba(199,154,75,.28);box-shadow:0 18px 48px rgba(36,50,74,.12)}.brand-hero::after{content:"";position:absolute;right:46px;top:24px;width:150px;height:150px;border:14px solid rgba(199,154,75,.34);border-radius:50%}.hero-eyebrow{font-size:12px;letter-spacing:4px;color:#d7b46a;font-weight:800}.brand-name{font-size:44px;line-height:1.15;font-weight:900;margin-top:20px;color:#f2c978}.brand-moral{max-width:760px;font-size:15px;line-height:1.8;margin-top:14px;color:rgba(255,255,255,.78)}.panel,.empty-state{background:rgba(255,255,255,.96);border:1px solid #e7e0d4;border-radius:12px;padding:26px;margin-bottom:18px;box-shadow:0 18px 48px rgba(36,50,74,.08)}.panel-title,.empty-title{font-size:22px;font-weight:900;color:#24324a}.field-label{font-size:13px;color:#667085;margin:20px 0 8px;font-weight:700}.field{height:44px;width:100%;box-sizing:border-box;padding:0 16px;border:1px solid #e7e0d4;background:#fbfaf7;border-radius:8px;font-size:14px;color:#17243b}.picker{display:flex;align-items:center}.color-dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px;flex-shrink:0}.primary-btn{height:48px;line-height:48px;background:#24324a;color:#f2c978;border-radius:8px;margin-top:24px;font-weight:900}.primary-btn::after,.refresh-btn::after{border:none}.summary-row{display:flex;justify-content:space-between;gap:30rpx;padding:18px 0;border-bottom:1px solid #eee7dc;font-size:14px}.summary-row>text:first-child{color:#667085}.summary-row>text:last-child{text-align:right;color:#17243b;font-weight:800}.summary-color{display:flex;align-items:center;color:#17243b;font-weight:800}.status-head,.material-head{display:flex;align-items:center;justify-content:space-between;gap:20px}.status-copy{font-size:13px;color:#667085;margin-top:8px}.refresh-btn{height:34px;line-height:34px;margin:0;background:#fff;color:#24324a;border:1px solid #e7e0d4;border-radius:999px;font-size:12px;font-weight:800}.progress{height:8px;background:#eceff3;margin-top:22px;overflow:hidden;border-radius:999px}.progress-value{height:100%;background:linear-gradient(90deg,#24324a,#c79a4b);transition:width .3s}.material-count{text-align:center;color:#9b6a20;font-size:13px;margin-top:14px}.filters{display:flex;gap:8px;flex-wrap:wrap}.filters text{font-size:12px;padding:7px 12px;color:#667085;border-radius:999px}.filters .active{background:#f5e6c9;color:#9b6a20;font-weight:900}.material-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:22px}.material-item{background:#fbfaf7;border:1px solid #eee7dc;border-radius:10px;overflow:hidden;min-width:0}.material-image,.material-placeholder{width:100%;height:310rpx}.material-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;background:linear-gradient(145deg,#f7f4ee,#fff)}.card-placeholder{background:linear-gradient(145deg,#24324a 0 48%,#c79a4b 48% 52%,#f7f4ee 52%)}.logo-mark{width:82rpx;height:82rpx;background:#24324a;color:#f2c978;border-radius:18rpx;display:flex;align-items:center;justify-content:center;font-size:36rpx;font-weight:900}.variant-2 .logo-mark{background:#c79a4b;color:#fff;border-radius:50%}.placeholder-name{font-weight:900;font-size:26rpx;margin-top:18rpx;color:#17243b}.card-placeholder .placeholder-name{color:#fff}.placeholder-state{font-size:20rpx;color:#8a92a0;margin-top:6rpx}.material-label{padding:14px 14px 8px;text-align:center;color:#52647f;font-size:13px;font-weight:800}.material-actions{display:flex;justify-content:center;padding:0 12px 12px}.material-actions button{height:30px;line-height:30px;margin:0;background:#fff;color:#24324a;border:1px solid #e7e0d4;border-radius:8px;font-size:12px;font-weight:800}.material-actions button::after{border:none}.asset-error{padding:0 14rpx 14rpx;color:#b42318;font-size:20rpx}.empty-state{text-align:center;padding:80px 30px}@media(min-width:900px){.page{max-width:1180px;margin:0 auto}.material-grid{grid-template-columns:repeat(4,1fr)}.material-image,.material-placeholder{height:220px}}@media(max-width:768px){.brand-hero{padding:34px 24px}.brand-name{font-size:36px}.brand-hero::after{right:18px;top:18px;transform:scale(.75);transform-origin:top right}.material-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:360px){.material-grid{grid-template-columns:1fr}}
</style>
