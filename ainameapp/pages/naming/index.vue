<template>
  <DashboardLayout currentMenu="naming">
    <view class="naming-page">
      <view class="back-line" @click="goHome">← 返回起名主页</view>

      <view class="page-head">
        <view>
          <view class="title">{{ categoryLabel }} 起名 结果 <text>第 {{ draft.round || 1 }} 轮结果</text></view>
          <view class="sub">为您精选以下 {{ names.length }} 个优质名称方案，可收藏、复制或生成品牌方案。</view>
        </view>
      </view>

      <view v-if="!names.length" class="empty-card">
        <view class="empty-title">暂无起名结果</view>
        <view class="sub">请先在首页填写需求并生成候选名称。</view>
        <button class="primary" @click="goHome">去起名</button>
      </view>

      <template v-else>
        <view class="summary-bar">
          <view><text>行业</text><strong>{{ draft.form?.industry || draft.form?.petType || draft.form?.surname || '-' }}</strong></view>
          <view><text>关键词</text><strong>{{ draft.form?.keywords || draft.form?.style || '-' }}</strong></view>
          <view><text>需求偏好</text><strong>{{ draft.form?.positioning || draft.form?.other || '简洁易记' }}</strong></view>
          <view><text>本轮生成时间</text><strong>{{ formatTime(draft.createdAt) }}</strong></view>
        </view>

        <view class="content-grid">
          <view class="result-list">
            <view v-for="(item,index) in names" :key="`${item.name}-${index}`" class="result-card">
              <view class="rank">{{ index + 1 }}</view>
              <view class="result-main">
                <view class="name-line">
                  <text class="name">{{ item.name }}</text>
                  <text class="score">推荐度 {{ score(index) }}</text>
                  <text v-if="item.domain && draft.form?.category === '企业名'" :class="['domain', isDomainOk(item) ? 'ok' : 'fail']">.com {{ item.domain_status }}</text>
                </view>
                <view class="detail"><text>寓意</text>{{ item.moral || '-' }}</view>
                <view class="detail"><text>出处</text>{{ item.reference || '-' }}</view>
                <view class="actions">
                  <button class="ghost" @click="saveName(item,index)">{{ savedAssets[index] ? '已收藏' : '收藏' }}</button>
                  <button class="ghost" @click="copyName(item.name)">复制</button>
                  <button class="dark" @click="setFinal(item)">选为最终名称</button>
                  <button v-if="draft.form?.category === '企业名'" class="ghost" @click="goBrand(item,index)">生成品牌方案</button>
                </view>
              </view>
            </view>
          </view>

          <view class="side-stack">
            <view class="side-card">
              <view class="side-title">继续优化，告诉我们你的想法</view>
              <view class="quick-list">
                <text v-for="item in quickFeedback" :key="item" @click="feedback = item">{{ item }}</text>
              </view>
              <textarea v-model="feedback" placeholder="输入你的反馈，AI 将继续优化名称方案"></textarea>
              <button class="primary full" :loading="loading" @click="handleFeedback">继续生成下一轮</button>
            </view>

            <view class="side-card">
              <view class="side-title">本轮信息</view>
              <view class="info-row"><text>当前轮次</text><strong>第 {{ draft.round || 1 }} 轮</strong></view>
              <view class="info-row"><text>已生成方案</text><strong>{{ names.length }} 个</strong></view>
              <view class="info-row"><text>生成时间</text><strong>{{ formatTime(draft.createdAt) }}</strong></view>
              <view v-if="finalName" class="recommend">
                <text>本轮最佳推荐</text>
                <strong>{{ finalName.name }}</strong>
                <view>名称简洁大气，寓意积极向上，适合作为最终候选。</view>
              </view>
            </view>
          </view>
        </view>
      </template>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const RESULT_KEY = 'namingResultDraft';
const quickFeedback = ['更现代', '更国际化', '更简洁', '避免生僻字', '文化感更强', '换一批'];
const draft = ref({});
const names = ref([]);
const feedback = ref('');
const loading = ref(false);
const savedAssets = ref({});
const finalName = ref(null);
const categoryLabel = computed(() => draft.value.form?.category || 'AI');

const loadDraft = () => {
  draft.value = uni.getStorageSync(RESULT_KEY) || {};
  names.value = draft.value.names || [];
  savedAssets.value = draft.value.savedAssets || {};
  finalName.value = draft.value.finalName || names.value[0] || null;
};
const persist = () => {
  uni.setStorageSync(RESULT_KEY, {
    ...draft.value,
    names: names.value,
    savedAssets: savedAssets.value,
    finalName: finalName.value
  });
};
const score = index => Math.max(88, 95 - index * 3);
const isDomainOk = item => String(item.domain_status || '').includes('可') || String(item.domain_status || '').includes('✅');
const formatTime = value => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
};
const saveName = async (item, index) => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  if (savedAssets.value[index]) return;
  const asset = await http.saveNameAsset({
    thread_id: draft.value.threadId || `local_${Date.now()}`,
    name: item.name,
    category: draft.value.form?.category || '企业名',
    moral: item.moral || null,
    reference: item.reference || null,
    domain: item.domain || null,
    domain_status: item.domain_status || null
  });
  savedAssets.value = { ...savedAssets.value, [index]: asset.id };
  persist();
  uni.showToast({ title: '已收藏', icon: 'success' });
};
const copyName = name => {
  uni.setClipboardData({ data: name });
};
const setFinal = item => {
  finalName.value = item;
  persist();
  uni.showToast({ title: '已设为最终名称', icon: 'none' });
};
const goBrand = async (item, index) => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  if (!savedAssets.value[index]) {
    await saveName(item, index);
  }
  uni.setStorageSync('brandKitDraft', {
    naming_asset_id: savedAssets.value[index] || null,
    thread_id: draft.value.threadId || `local_${Date.now()}`,
    name: item.name,
    moral: item.moral || '',
    industry_hint: draft.value.form?.industry || draft.value.form?.product || ''
  });
  uni.redirectTo({ url: '/pages/brand-kit/index' });
};
const handleFeedback = async () => {
  if (!feedback.value.trim()) return uni.showToast({ title: '请输入反馈意见', icon: 'none' });
  if (!draft.value.threadId) return uni.showToast({ title: '缺少会话信息，请重新起名', icon: 'none' });
  loading.value = true;
  try {
    const result = await http.feedbackName({
      thread_id: draft.value.threadId,
      category: draft.value.form?.category || '企业名',
      feedback: feedback.value.trim()
    });
    names.value = result.names || [];
    draft.value = {
      ...draft.value,
      names: names.value,
      threadId: result.thread_id || draft.value.threadId,
      round: (draft.value.round || 1) + 1,
      createdAt: new Date().toISOString()
    };
    feedback.value = '';
    savedAssets.value = {};
    finalName.value = names.value[0] || null;
    persist();
  } finally {
    loading.value = false;
  }
};
const goHome = () => uni.redirectTo({ url: '/pages/home/index' });

onShow(loadDraft);
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.naming-page { max-width: 1280px; margin: 0 auto; }
.back-line { display: inline-flex; align-items: center; margin: 4px 0 18px; color: $brand-primary; font-size: 14px; cursor: pointer; }
.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 22px; }
.title { font-size: 38px; line-height: 1.15; font-weight: 900; color: $brand-primary; }
.title text { margin-left: 12px; padding: 6px 12px; border: 1px solid rgba(199,154,75,.5); border-radius: 999px; color: #9b6a20; font-size: 14px; vertical-align: middle; }
.sub { display: block; margin-top: 8px; color: $text-secondary; font-size: 15px; line-height: 1.6; }
.empty-card,.summary-bar,.result-card,.side-card { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.empty-card { padding: 80px 30px; text-align: center; }
.empty-title { font-size: 24px; font-weight: 900; color: $brand-primary; }
.primary,.ghost,.dark { margin: 0; border-radius: 8px; font-weight: 900; }
.primary { height: 44px; line-height: 44px; padding: 0 28px; background: $brand-primary; color: #f5d392; margin-top: 18px; }
.primary.full { width: 100%; margin-top: 14px; }
.primary::after,.ghost::after,.dark::after { border: none; }
.summary-bar { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; margin-bottom: 16px; overflow: hidden; }
.summary-bar view { padding: 18px 22px; border-right: 1px solid #eee7dc; }
.summary-bar view:last-child { border-right: none; }
.summary-bar text { display: block; color: $text-secondary; font-size: 12px; }
.summary-bar strong { display: block; margin-top: 4px; color: $brand-primary; font-size: 14px; }
.content-grid { display: grid; grid-template-columns: minmax(0,1fr) 360px; gap: 18px; align-items: start; }
.result-list { display: flex; flex-direction: column; gap: 14px; }
.result-card { display: grid; grid-template-columns: 70px minmax(0,1fr); gap: 20px; padding: 24px 26px; }
.rank { width: 50px; height: 58px; border-radius: 999px 999px 8px 8px; background: linear-gradient(180deg,#d6b064,#b68136); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 900; }
.name-line { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding-bottom: 16px; border-bottom: 1px solid #eee7dc; }
.name { color: $brand-primary; font-size: 34px; font-weight: 900; line-height: 1.2; }
.score,.domain { padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 900; }
.score { color: #9b6a20; background: #fff5df; border: 1px solid #ead6ad; }
.domain.ok { color: #067647; background: #ecfdf3; }
.domain.fail { color: #b42318; background: #fff1f3; }
.detail { margin-top: 12px; color: #52647f; font-size: 14px; line-height: 1.7; }
.detail text { color: $brand-primary; font-weight: 900; margin-right: 8px; }
.actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.ghost,.dark { height: 38px; line-height: 38px; padding: 0 18px; font-size: 13px; }
.ghost { background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; }
.dark { background: $brand-primary; color: #f5d392; }
.side-stack { display: flex; flex-direction: column; gap: 14px; }
.side-card { padding: 22px; }
.side-title { color: $brand-primary; font-size: 17px; font-weight: 900; }
.quick-list { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0; }
.quick-list text { padding: 7px 12px; background: #fbfaf7; border: 1px solid #e7e0d4; border-radius: 999px; color: $brand-primary; font-size: 12px; cursor: pointer; }
textarea { width: 100%; box-sizing: border-box; min-height: 96px; padding: 14px 16px; border: 1px solid #e7e0d4; border-radius: 8px; background: #fbfaf7; color: $text-main; font-size: 14px; line-height: 1.6; }
.info-row { display: flex; justify-content: space-between; gap: 16px; padding: 14px 0; border-bottom: 1px solid #eee7dc; }
.info-row text { color: $text-secondary; font-size: 13px; }
.info-row strong { color: $brand-primary; font-size: 13px; text-align: right; }
.recommend { margin-top: 16px; padding: 18px; border: 1px solid #ead6ad; border-radius: 10px; background: #fffbf2; }
.recommend text { color: $text-secondary; font-size: 12px; }
.recommend strong { display: block; margin-top: 8px; color: $brand-primary; font-size: 24px; }
.recommend view { margin-top: 8px; color: #52647f; font-size: 13px; line-height: 1.6; }
@media (max-width: 1100px) {
  .content-grid { grid-template-columns: 1fr; }
  .summary-bar { grid-template-columns: repeat(2,1fr); }
}
@media (max-width: 768px) {
  .title { font-size: 30px; }
  .summary-bar { grid-template-columns: 1fr; }
  .summary-bar view { border-right: none; border-bottom: 1px solid #eee7dc; }
  .result-card { grid-template-columns: 1fr; padding: 20px; }
  .rank { width: 44px; height: 50px; }
  .name { font-size: 28px; }
}
</style>
