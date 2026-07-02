<template>
  <DashboardLayout currentMenu="ai_name">
    <view class="content-inner">
      <BrandKitPanel v-if="brandKitDraft" :draft="brandKitDraft" @back="closeBrandKit" />
      
      <template v-else>
      <view class="page-toolbar">
        <view class="scene-tabs">
          <view v-for="item in categories" :key="item" 
                :class="['scene-tab', formData.category === item ? 'active' : '']" 
                @click="switchCategory(item)">
            {{ item }}
          </view>
        </view>
        <button class="primary-action-btn" :loading="loading" @click="handleGenerate">
          + 开始智能起名
        </button>
      </view>

      <view class="upload-section" v-if="formData.category === '企业名'">
        <view class="upload-content">
          <text class="upload-tip">有企业命名规范？让 AI 学习你的专属标准</text>
          <button class="upload-btn" @click="handleUploadDocs">上传专属知识库 (TXT/PDF)</button>
        </view>
      </view>

      <view class="config-card">
        <view class="card-title">起名参数配置</view>
        <view class="form-grid">
          <view class="form-item" v-if="formData.category === '人名'">
            <text class="form-label">姓氏</text>
            <input class="input-box" v-model="formData.surname" placeholder="请输入姓氏 (如: 张)" placeholder-style="color: #9CA3AF;" />
          </view>
          <view class="form-item" v-if="formData.category === '人名'">
            <text class="form-label">性别倾向</text>
            <picker mode="selector" :range="genderOptions" @change="e => formData.gender = genderOptions[e.detail.value]">
              <view class="picker-box">
                <text>{{ formData.gender }}</text>
                <text class="arrow">▼</text>
              </view>
            </picker>
          </view>
          <view class="form-item">
            <text class="form-label">字数要求</text>
            <picker mode="selector" :range="lengthOptions" @change="e => formData.length = lengthOptions[e.detail.value]">
              <view class="picker-box">
                <text>{{ formData.length }}</text>
                <text class="arrow">▼</text>
              </view>
            </picker>
          </view>
          <view class="form-item full-width">
            <text class="form-label">核心诉求 / 行业偏好 (可选)</text>
            <textarea class="textarea-box" v-model="formData.other" placeholder="请输入核心诉求，例如：包含生辰八字喜用神，或者希望企业名有科技感..." placeholder-style="color: #9CA3AF;"></textarea>
          </view>
        </view>
      </view>

      <view class="result-section" v-if="names.length > 0">
        <view class="result-header">
          <text class="result-title">为您生成的专属方案</text>
          <view class="result-actions">
            <button class="clear-btn" @click="clearResults">清空结果</button>
            <button v-if="selectedForPublish.length >= 2" class="publish-btn" @click="publishSelected">
              发布投票 ({{selectedForPublish.length}})
            </button>
          </view>
        </view>
        <view class="project-grid">
          <view class="project-card" v-for="(item, index) in names" :key="index">
            <view class="card-top">
              <text class="name-text">{{ item.name }}</text>
              <text v-if="item.domain && formData.category === '企业名'" :class="['domain-tag', item.domain_status.includes('✅') ? 'domain-success' : 'domain-fail']">
                {{ item.domain }} ({{ item.domain_status }})
              </text>
            </view>
            <view class="card-body">
              <view class="detail-row"><text class="label">出处：</text>{{ item.reference }}</view>
              <view class="detail-row"><text class="label">寓意：</text>{{ item.moral }}</view>
            </view>
            <view class="card-actions">
              <button :class="['action-btn', savedAssets[index] ? 'active-btn' : '']" @click="saveName(item,index)">
                {{savedAssets[index] ? '已收藏' : '收藏'}}
              </button>
              <button class="action-btn" @click="openPrecision(item,index)">精批</button>
              <button :class="['action-btn', selectedForPublish.includes(index) ? 'active-btn' : '']" @click="togglePublish(index)">
                {{selectedForPublish.includes(index) ? '已入选' : '选入投票'}}
              </button>
            </view>
            <button v-if="formData.category === '企业名'" class="brand-kit-btn" @click="openBrandKit(item,index)">生成品牌视觉</button>
          </view>
        </view>

        <view class="feedback-card">
          <text class="card-title">对结果不满意？</text>
          <text class="form-label">输入修改意见，AI 将微调并重新生成</text>
          <textarea class="textarea-box" v-model="feedbackText" placeholder="例如：保留第二个名字，其他换成带水字旁的..."></textarea>
          <button class="btn-secondary" :loading="loading" @click="handleFeedback">基于意见重新生成</button>
        </view>
      </view>
      </template>

      <view v-if="orderOpen" class="order-overlay" @click="closeOrder">
        <view class="order-sheet" @click.stop>
          <view class="order-title">为「{{ orderTarget?.name }}」选择精批专家</view>
          <view class="expert-grid">
            <view v-for="expert in experts" :key="expert.id" :class="['expert-card', selectedExpert?.id === expert.id ? 'selected' : '']" @click="selectExpert(expert)">
              <view class="expert-name">{{ expert.display_name }}</view>
              <view class="expert-meta">{{ labelType(expert.expert_type) }} · {{ expert.years_experience }} 年经验</view>
              <view class="expert-meta">★ {{ Number(expert.average_rating).toFixed(1) }} · {{ expert.review_count }} 条评价</view>
            </view>
          </view>
          <view class="order-label">服务套餐</view>
          <view class="package-list">
            <view v-for="item in selectedPackages" :key="item.id" :class="['package-card', orderForm.package_id === item.id ? 'selected' : '']" @click="orderForm.package_id = item.id">
              <text>{{ item.name }} · {{ item.delivery_days }} 天</text>
              <text>¥{{ payable(item) }}</text>
            </view>
          </view>
          <view class="order-label">精批需求</view>
          <textarea class="order-area" :value="orderForm.requirements" placeholder="说明希望专家重点分析的问题（至少5个字）" @input="orderForm.requirements = $event.detail.value" />
          <button class="submit-order-btn" :loading="submittingOrder" @click="createPrecisionOrder">创建订单并支付</button>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onHide, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import BrandKitPanel from '@/components/BrandKitPanel/BrandKitPanel.vue';

// --- 状态定义 ---
const LEGACY_WORKBENCH_STORAGE_KEY = 'namingWorkbenchState';
const WORKBENCH_STORAGE_PREFIX = 'namingWorkbenchState';
const categories = ['人名', '企业名', '宠物名'];
const genderOptions = ['不限', '男', '女'];
const lengthOptions = ['不限', '单字', '两字', '多字'];

const defaultFormData = () => ({
  category: '人名',
  surname: '',
  gender: '不限',
  length: '不限',
  other: '',
  exclude: []
});
const defaultCategoryState = () => ({
  names: [],
  threadId: '',
  savedAssets: {},
  selectedForPublish: [],
  formData: { surname: '', gender: '不限', length: '不限', other: '', exclude: [] }
});
const defaultCategoryCache = () => ({
  '人名': defaultCategoryState(),
  '企业名': defaultCategoryState(),
  '宠物名': defaultCategoryState()
});

const formData = ref(defaultFormData());

const loading = ref(false);
const names = ref([]);
const threadId = ref('');
const feedbackText = ref('');
const token = ref(uni.getStorageSync('token'));
const savedAssets = ref({});
const selectedForPublish = ref([]);
const brandKitDraft = ref(null);
const experts = ref([]);
const packages = ref([]);
const profile = ref(null);
const orderOpen = ref(false);
const orderTarget = ref(null);
const orderTargetIndex = ref(null);
const selectedExpert = ref(null);
const submittingOrder = ref(false);
const orderForm = reactive({ package_id: null, requirements: '' });
const selectedPackages = computed(() => selectedExpert.value ? packages.value.filter(item => item.expert_type === selectedExpert.value.expert_type) : []);
const labelType = value => value === 'CULTURE_MASTER' ? '国学命名专家' : '品牌咨询师';
const payable = item => profile.value?.is_vip ? (Number(item.price) * 0.9).toFixed(2) : Number(item.price).toFixed(2);

// --- 类别状态缓存 ---
const categoryCache = defaultCategoryCache();

const getWorkbenchStorageKey = () => {
  const currentToken = String(uni.getStorageSync('token') || '').trim();
  const currentUser = uni.getStorageSync('user') || {};
  const userKey = currentUser.id || currentUser.email || currentUser.username;
  if (!currentToken || !userKey) return '';
  return `${WORKBENCH_STORAGE_PREFIX}:${encodeURIComponent(String(userKey))}`;
};

const resetWorkbench = () => {
  formData.value = defaultFormData();
  names.value = [];
  threadId.value = '';
  feedbackText.value = '';
  savedAssets.value = {};
  selectedForPublish.value = [];
  brandKitDraft.value = null;
  orderOpen.value = false;
  orderTarget.value = null;
  orderTargetIndex.value = null;
  selectedExpert.value = null;
  Object.assign(categoryCache, defaultCategoryCache());
};

const persistWorkbench = () => {
  const storageKey = getWorkbenchStorageKey();
  if (!storageKey) return;
  uni.setStorageSync(storageKey, {
    formData: formData.value,
    names: names.value,
    threadId: threadId.value,
    feedbackText: feedbackText.value,
    savedAssets: savedAssets.value,
    selectedForPublish: selectedForPublish.value,
    categoryCache,
    brandKitDraft: brandKitDraft.value
  });
};

const restoreWorkbench = () => {
  uni.removeStorageSync(LEGACY_WORKBENCH_STORAGE_KEY);
  const storageKey = getWorkbenchStorageKey();
  if (!storageKey) {
    resetWorkbench();
    return;
  }
  const state = uni.getStorageSync(storageKey);
  if (!state) {
    resetWorkbench();
    return;
  }
  if (state.formData) formData.value = state.formData;
  names.value = state.names || [];
  threadId.value = state.threadId || '';
  feedbackText.value = state.feedbackText || '';
  savedAssets.value = state.savedAssets || {};
  selectedForPublish.value = state.selectedForPublish || [];
  brandKitDraft.value = state.brandKitDraft || null;
  if (state.categoryCache) Object.assign(categoryCache, state.categoryCache);
};

// --- 方法定义 ---
const switchCategory = (cat) => {
  if (formData.value.category === cat) return;
  const currentCat = formData.value.category;
  categoryCache[currentCat] = {
    names: names.value, threadId: threadId.value, savedAssets: savedAssets.value,
    selectedForPublish: selectedForPublish.value, formData: { ...formData.value }
  };
  const nextCatState = categoryCache[cat];
  formData.value = { ...nextCatState.formData, category: cat };
  names.value = nextCatState.names; threadId.value = nextCatState.threadId;
  savedAssets.value = nextCatState.savedAssets; selectedForPublish.value = nextCatState.selectedForPublish;
  persistWorkbench();
};

const redirectToAlipay = payment => {
  // #ifdef H5
  window.location.href = payment.payment_url;
  // #endif
  // #ifndef H5
  uni.showToast({ title: '当前仅 H5 支持支付宝沙箱支付', icon: 'none' });
  // #endif
};

const saveName = async (item, index) => {
  if (!token.value) return uni.navigateTo({ url: '/pages/login/login' });
  if (savedAssets.value[index]) return;
  try {
    const asset = await http.saveNameAsset({ thread_id: threadId.value, name: item.name, category: formData.value.category, moral: item.moral || '', reference: item.reference || '', domain: item.domain || null, domain_status: item.domain_status || null });
    savedAssets.value = { ...savedAssets.value, [index]: asset.id };
    persistWorkbench();
    uni.showToast({ title: '已收藏', icon: 'success' });
  } catch (e) {}
};

const togglePublish = index => {
  const current = [...selectedForPublish.value];
  const position = current.indexOf(index);
  if (position >= 0) current.splice(position, 1);
  else if (current.length < 5) current.push(index);
  else return uni.showToast({ title: '最多选择5个名字', icon: 'none' });
  selectedForPublish.value = current;
  persistWorkbench();
};

const publishSelected = () => {
  const candidates = selectedForPublish.value.map(index => ({ ...names.value[index], category: formData.value.category }));
  uni.setStorageSync('publishCandidates', candidates);
  uni.navigateTo({ url: '/pages/community/publish' });
};

const clearResults = () => {
  uni.showModal({
    title: '清空生成结果',
    content: '确认清空当前分类下已生成的名字？起名参数会保留。',
    success: result => {
      if (!result.confirm) return;
      names.value = [];
      threadId.value = '';
      feedbackText.value = '';
      savedAssets.value = {};
      selectedForPublish.value = [];
      categoryCache[formData.value.category] = {
        names: [],
        threadId: '',
        savedAssets: {},
        selectedForPublish: [],
        formData: { ...formData.value }
      };
      persistWorkbench();
    }
  });
};

const openBrandKit = (item, index) => {
  if (!token.value) return uni.navigateTo({ url: '/pages/login/login' });
  if (!threadId.value) return uni.showToast({ title: '请先完成一次企业起名', icon: 'none' });
  brandKitDraft.value = {
    naming_asset_id: savedAssets.value[index] || null,
    thread_id: threadId.value,
    name: item.name,
    moral: item.moral || '',
    reference: item.reference || '',
    industry_hint: formData.value.other || ''
  };
  persistWorkbench();
};

const closeBrandKit = () => {
  brandKitDraft.value = null;
  persistWorkbench();
};

const handleUploadDocs = () => {
  const currentToken = String(uni.getStorageSync('token') || '').trim();
  if (!currentToken) return uni.navigateTo({ url: '/pages/login/login' });
  uni.chooseFile({
    count: 1, type: 'all', extension: ['.txt', '.pdf'],
    success: async (res) => {
      const tempFilePath = res.tempFiles[0].path;
      uni.showLoading({ title: '解析中...' });
      let toast = { title: '上传成功', icon: 'success' };
      try { await http.uploadKnowledge(tempFilePath); } 
      catch (error) { toast = { title: error?.data?.detail || '上传失败', icon: 'none' }; } 
      finally { uni.hideLoading(); uni.showToast(toast); }
    }
  });
};

const loadOrderOptions = async () => {
  if (experts.value.length && packages.value.length && profile.value) return;
  const [expertResult, packageResult, profileResult] = await Promise.all([http.getExperts(1, ''), http.getExpertPackages(), http.getMyProfile()]);
  experts.value = expertResult.items || [];
  packages.value = packageResult || [];
  profile.value = profileResult;
};

const openPrecision = async (item, index) => {
  if (!token.value) return uni.navigateTo({ url: '/pages/login/login' });
  orderTarget.value = item;
  orderTargetIndex.value = index;
  selectedExpert.value = null;
  Object.assign(orderForm, { package_id: null, requirements: `请对「${item.name}」进行专业精批，重点分析寓意、传播感和使用风险。` });
  await loadOrderOptions();
  if (experts.value.length) selectExpert(experts.value[0]);
  orderOpen.value = true;
};

const selectExpert = expert => {
  selectedExpert.value = expert;
  orderForm.package_id = packages.value.find(item => item.expert_type === expert.expert_type)?.id || null;
};

const closeOrder = () => {
  orderOpen.value = false;
  orderTarget.value = null;
  orderTargetIndex.value = null;
  selectedExpert.value = null;
};

const createPrecisionOrder = async () => {
  if (!selectedExpert.value) return uni.showToast({ title: '请选择专家', icon: 'none' });
  if (!orderForm.package_id) return uni.showToast({ title: '请选择服务套餐', icon: 'none' });
  if (orderForm.requirements.trim().length < 5) return uni.showToast({ title: '请填写至少 5 个字的需求', icon: 'none' });
  const payload = { expert_id: selectedExpert.value.id, package_id: orderForm.package_id, requirements: orderForm.requirements.trim() };
  const assetId = savedAssets.value[orderTargetIndex.value];
  if (assetId) payload.naming_asset_id = assetId;
  else Object.assign(payload, {
    name: orderTarget.value.name,
    category: formData.value.category,
    moral: orderTarget.value.moral || null
  });
  submittingOrder.value = true;
  try {
    const order = await http.createExpertOrder(payload);
    orderOpen.value = false;
    uni.showModal({
      title: '订单已创建',
      content: `实付 ¥${order.amount}，是否前往支付宝沙箱支付？`,
      success: async result => {
        if (result.confirm) {
          const payment = await http.startExpertAlipay(order.id);
          redirectToAlipay(payment);
        } else {
          uni.redirectTo({ url: '/pages/assets/index?tab=orders' });
        }
      }
    });
  } finally {
    submittingOrder.value = false;
  }
};

const handleGenerate = async () => {
  if (!token.value) return uni.navigateTo({ url: '/pages/login/login' });
  if (formData.value.category === '人名' && !formData.value.surname.trim()) return uni.showToast({ title: '请填写姓氏', icon: 'none' });
  loading.value = true;
  uni.showLoading({ title: 'AI思考中...' });
  try {
    const res = await http.generateName(formData.value);
    names.value = res.names; threadId.value = res.thread_id; feedbackText.value = ''; savedAssets.value = {}; selectedForPublish.value = [];
    persistWorkbench();
  } catch (e) { console.error(e); } finally { loading.value = false; uni.hideLoading(); }
};

const handleFeedback = async () => {
  if (!feedbackText.value.trim()) return uni.showToast({ title: '请输入修改意见', icon: 'none' });
  loading.value = true;
  uni.showLoading({ title: '微调中...' });
  try {
    const res = await http.feedbackName({ thread_id: threadId.value, category: formData.value.category, feedback: feedbackText.value });
    names.value = res.names; feedbackText.value = ''; 
    persistWorkbench();
  } catch (e) { console.error(e); } finally { loading.value = false; uni.hideLoading(); }
};

onShow(() => {
  token.value = uni.getStorageSync('token');
  restoreWorkbench();
});
onHide(persistWorkbench);
</script>

<style lang="scss" scoped>
/* 核心内容区限制宽度，避免大屏拉伸 */
.content-inner {
  max-width: 1200px;
  margin: 0 auto;
}

/* --- 页面内操作栏：Tabs 和 大按钮 --- */
.page-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 48rpx;
  background: #FFFFFF;
  padding: 24rpx 32rpx;
  border-radius: 24rpx;
  border: 1px solid #E5E7EB;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);

  .scene-tabs {
    display: flex;
    background: #F3F4F6;
    border-radius: 16rpx;
    padding: 8rpx;

    .scene-tab {
      padding: 16rpx 48rpx;
      font-size: 28rpx;
      font-weight: 600;
      color: #6B7280;
      border-radius: 12rpx;
      cursor: pointer;
      transition: all 0.2s;

      &.active {
        background: #FFFFFF;
        color: #4F46E5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      }
    }
  }

  .primary-action-btn {
    background-color: #4F46E5;
    color: #FFFFFF;
    border-radius: 16rpx;
    font-size: 28rpx;
    font-weight: 600;
    padding: 0 48rpx;
    height: 88rpx;
    line-height: 88rpx;
    margin: 0;
    border: none;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
    transition: all 0.2s;
    &::after { border: none; }
    &:active { transform: translateY(2rpx); box-shadow: none; }
  }
}

/* --- 通用卡片及内部样式 --- */
.config-card, .feedback-card {
  background: #FFFFFF;
  border-radius: 24rpx;
  padding: 48rpx;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  margin-bottom: 48rpx;
  border: 1px solid #E5E7EB;

  .card-title { font-size: 32rpx; font-weight: 700; color: #111827; margin-bottom: 32rpx; display: block; }
}

.upload-section {
  background: #EEF2FF;
  border: 2rpx dashed #A5B4FC;
  border-radius: 24rpx;
  padding: 48rpx;
  margin-bottom: 48rpx;
  display: flex; justify-content: center; align-items: center;
  .upload-content { text-align: center; }
  .upload-tip { font-size: 28rpx; color: #4F46E5; font-weight: 600; display: block; margin-bottom: 24rpx; }
  .upload-btn { background: #FFFFFF; color: #4F46E5; border-radius: 999px; font-size: 26rpx; font-weight: 600; padding: 16rpx 48rpx; border: 1px solid #C7D2FE; line-height: 1.5; }
  .upload-btn::after { border: none; }
}

/* 表单内部布局 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32rpx;
}
.form-item.full-width { grid-column: span 2; }
.form-label { display: block; font-size: 28rpx; color: #374151; margin-bottom: 16rpx; font-weight: 600; }
.input-box, .picker-box { width: 100%; height: 96rpx; background: #F9FAFB; border: 1px solid #D1D5DB; border-radius: 16rpx; padding: 0 32rpx; font-size: 28rpx; color: #111827; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; transition: border-color 0.2s; }
.input-box:focus { border-color: #4F46E5; outline: none; background: #FFFFFF; }
.textarea-box { width: 100%; height: 200rpx; background: #F9FAFB; border: 1px solid #D1D5DB; border-radius: 16rpx; padding: 24rpx 32rpx; box-sizing: border-box; font-size: 28rpx; color: #111827; transition: border-color 0.2s; line-height: 1.6; }
.textarea-box:focus { border-color: #4F46E5; outline: none; background: #FFFFFF; }

/* 结果区 */
.result-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 32rpx;
  .result-title { font-size: 36rpx; font-weight: 700; color: #111827; }
  .result-actions { display: flex; gap: 16rpx; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
  .clear-btn { background: #FFFFFF; color: #6B7280; border-radius: 999px; font-size: 26rpx; padding: 12rpx 32rpx; font-weight: 600; border: 1px solid #D1D5DB; line-height: 1.5; margin: 0; }
  .clear-btn::after { border: none; }
  .publish-btn { background: #EEF2FF; color: #4F46E5; border-radius: 999px; font-size: 26rpx; padding: 12rpx 32rpx; font-weight: 600; border: none; line-height: 1.5; margin: 0; }
  .publish-btn::after { border: none; }
}

/* 卡片网格瀑布流 */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 32rpx;
  margin-bottom: 48rpx;
}

.project-card {
  background: #FFFFFF;
  border-radius: 24rpx;
  padding: 40rpx;
  border: 1px solid #E5E7EB;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex; flex-direction: column;

  &:hover { transform: translateY(-4rpx); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }

  .card-top {
    display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24rpx; border-bottom: 1px solid #F3F4F6; padding-bottom: 24rpx;
    .name-text { font-size: 48rpx; font-weight: 800; color: #4F46E5; }
    .domain-tag { font-size: 22rpx; padding: 6rpx 16rpx; border-radius: 8rpx; font-weight: 600; }
    .domain-success { background: #D1FAE5; color: #059669; }
    .domain-fail { background: #FEE2E2; color: #DC2626; }
  }

  .card-body {
    flex: 1; margin-bottom: 32rpx;
    .detail-row { font-size: 26rpx; color: #4B5563; line-height: 1.6; margin-bottom: 16rpx; }
    .label { font-weight: 600; color: #111827; }
  }

  .card-actions {
    display: flex; gap: 16rpx; margin-bottom: 16rpx;
    .action-btn { flex: 1; height: 72rpx; border-radius: 12rpx; font-size: 26rpx; font-weight: 600; display: flex; justify-content: center; align-items: center; background: #F9FAFB; color: #4B5563; border: 1px solid #D1D5DB; padding: 0; line-height: 1; }
    .action-btn::after { border: none; }
    .active-btn { background: #EEF2FF; color: #4F46E5; border-color: #C7D2FE; }
  }

  .brand-kit-btn { width: 100%; height: 72rpx; background: #111827; color: #FFFFFF; border-radius: 12rpx; font-size: 26rpx; font-weight: 600; display: flex; justify-content: center; align-items: center; border: none; line-height: 1; }
  .brand-kit-btn::after { border: none; }
}

.order-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(17, 24, 39, 0.48);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}
.order-sheet {
  width: min(920rpx, 100%);
  max-height: 86vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 16rpx;
  padding: 36rpx;
}
.order-title {
  font-size: 34rpx;
  font-weight: 800;
  margin-bottom: 24rpx;
}
.expert-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}
.expert-card, .package-card {
  border: 1px solid #E5E7EB;
  border-radius: 12rpx;
  padding: 20rpx;
}
.expert-card.selected, .package-card.selected {
  border-color: #4F46E5;
  background: #EEF2FF;
}
.expert-name {
  font-weight: 800;
  font-size: 28rpx;
}
.expert-meta {
  color: #6B7280;
  font-size: 23rpx;
  margin-top: 6rpx;
}
.order-label {
  font-size: 24rpx;
  color: #6B7280;
  margin: 24rpx 0 12rpx;
}
.package-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.package-card {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
  font-size: 26rpx;
}
.order-area {
  width: 100%;
  height: 160rpx;
  box-sizing: border-box;
  border: 1px solid #D1D5DB;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 27rpx;
}
.submit-order-btn {
  background: #4F46E5;
  color: #fff;
  border-radius: 12rpx;
  margin-top: 24rpx;
}
.submit-order-btn::after { border: none; }

.feedback-card {
  .btn-secondary { width: 100%; height: 96rpx; background: #FFFFFF; color: #111827; border: 1px solid #D1D5DB; border-radius: 16rpx; margin-top: 32rpx; font-size: 28rpx; font-weight: 600; line-height: 96rpx; transition: all 0.2s; }
  .btn-secondary::after { border: none; }
  .btn-secondary:active { background: #F3F4F6; }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .page-toolbar { flex-direction: column; gap: 32rpx; align-items: stretch; }
  .page-toolbar .scene-tabs { justify-content: center; }
  .form-grid { grid-template-columns: 1fr; }
  .form-item.full-width { grid-column: span 1; }
  .project-grid { grid-template-columns: 1fr; }
  .expert-grid { grid-template-columns: 1fr; }
  .project-card .card-actions { flex-wrap: wrap; }
  .project-card .card-actions .action-btn { min-width: 30%; }
}
</style>
