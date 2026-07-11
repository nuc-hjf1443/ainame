<template>
  <DashboardLayout currentMenu="expert">
    <view class="market-page">
      <view class="page-head">
        <view>
          <view class="title">专家服务</view>
          <view class="sub">连接国学命名与品牌咨询专家，为重要名称提供人工精批。</view>
        </view>
        <button class="primary" @click="goChat">我的咨询</button>
      </view>

      <view class="filters">
        <view v-for="item in types" :key="item.value" :class="['chip', type === item.value ? 'active' : '']" @click="setType(item.value)">
          {{ item.label }}
        </view>
      </view>

      <view v-if="loading" class="state-card">正在加载专家列表...</view>
      <view v-else-if="!experts.length" class="state-card">暂无已认证专家</view>

      <view v-else class="expert-grid">
        <view v-for="expert in experts" :key="expert.id" class="expert-card">
          <view class="expert-hero" @click="openDetail(expert.id)">
            <view class="avatar">{{ expert.display_name.slice(0,1) }}</view>
            <view class="expert-main">
              <view class="name-row">
                <text class="expert-name">{{ expert.display_name }}</text>
                <text class="badge">资深命名专家</text>
              </view>
              <view class="rating">★ {{ Number(expert.average_rating || 0).toFixed(1) }} 分 ｜ 已完成 {{ expert.review_count || 0 }} 单</view>
              <view class="tags">
                <text>{{ labelType(expert.expert_type) }}</text>
                <text>{{ expert.years_experience }}年经验</text>
                <text>{{ levelText(expert.expert_level) }}</text>
              </view>
            </view>
          </view>
          <view class="bio">{{ expert.bio }}</view>
          <view class="card-foot">
            <view>
              <text class="price">¥ {{ primaryPackage(expert)?.price || '-' }}</text>
              <text class="muted">起 服务透明</text>
            </view>
            <view class="actions">
              <button class="outline" :disabled="!primaryPackage(expert)" @click="startChat(expert)">先咨询</button>
              <button class="dark" :disabled="!primaryPackage(expert)" @click="openDetail(expert.id)">立即下单</button>
            </view>
          </view>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const experts = ref([]);
const packages = ref([]);
const loading = ref(false);
const type = ref('');
const types = [
  { label: '全部专家', value: '' },
  { label: '国学命名', value: 'CULTURE_MASTER' },
  { label: '品牌咨询', value: 'BRAND_CONSULTANT' }
];
const labelType = value => value === 'CULTURE_MASTER' ? '国学命名' : '品牌咨询';
const levelText = value => ({ STANDARD: '专业版', SENIOR: '资深版', MASTER: '大师版' }[value] || '专业版');
const packageMatchesExpert = (item, expert) => item.expert_type === expert.expert_type && (item.expert_level || 'STANDARD') === (expert.expert_level || 'STANDARD');
const primaryPackage = expert => packages.value.find(item => packageMatchesExpert(item, expert));

const load = async () => {
  loading.value = true;
  try {
    const [expertResult, packageResult] = await Promise.all([http.getExperts(1, type.value), http.getExpertPackages()]);
    experts.value = expertResult.items || [];
    packages.value = packageResult || [];
  } finally {
    loading.value = false;
  }
};
const setType = value => {
  type.value = value;
  load();
};
const openDetail = id => uni.navigateTo({ url: `/pages/marketplace/detail?id=${id}` });
const startChat = async expert => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  const pack = primaryPackage(expert);
  if (!pack) return;
  const thread = await http.createExpertChatThread({ expert_id: expert.id, package_id: pack.id });
  uni.navigateTo({ url: `/pages/marketplace/chat?thread_id=${thread.id}` });
};
const goChat = () => uni.navigateTo({ url: '/pages/marketplace/chat' });

onShow(load);
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.market-page { max-width: 1320px; margin: 0 auto; }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 24px; margin: 28px 0; }
.title { font-size: 40px; font-weight: 900; color: $brand-primary; line-height: 1.1; }
.sub { color: $text-secondary; font-size: 15px; margin-top: 10px; }
.primary,.outline,.dark { margin: 0; border-radius: 8px; font-weight: 900; }
.primary { height: 42px; line-height: 42px; padding: 0 22px; background: $brand-primary; color: #f5d392; }
.primary::after,.outline::after,.dark::after { border: none; }
.filters { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 22px; }
.chip { padding: 10px 18px; border-radius: 999px; background: #fff; border: 1px solid #e7e0d4; color: $text-secondary; font-size: 14px; cursor: pointer; }
.chip.active { background: $brand-primary; color: #f5d392; border-color: $brand-primary; font-weight: 900; }
.state-card,.expert-card { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.state-card { padding: 80px 30px; text-align: center; color: $text-secondary; }
.expert-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 18px; }
.expert-card { padding: 24px; }
.expert-hero { display: flex; gap: 18px; align-items: center; padding: 24px; border-radius: 10px; background: linear-gradient(135deg,#17243b,#24324a); color: #fff; cursor: pointer; }
.avatar { width: 84px; height: 84px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.14); border: 2px solid rgba(199,154,75,.8); color: #f5d392; font-size: 34px; font-weight: 900; flex-shrink: 0; }
.expert-main { min-width: 0; }
.name-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.expert-name { font-size: 30px; font-weight: 900; }
.badge { padding: 6px 12px; border-radius: 999px; background: #f5d392; color: $brand-primary; font-size: 12px; font-weight: 900; }
.rating { margin-top: 10px; color: rgba(255,255,255,.86); font-size: 15px; }
.tags { margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }
.tags text { padding: 6px 12px; border: 1px solid rgba(255,255,255,.32); border-radius: 999px; color: rgba(255,255,255,.9); font-size: 12px; }
.bio { min-height: 68px; margin: 18px 0; color: #52647f; font-size: 14px; line-height: 1.7; }
.card-foot { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; border-top: 1px solid #eee7dc; padding-top: 18px; }
.price { color: $brand-primary; font-size: 30px; font-weight: 900; }
.muted { display: inline-block; margin-left: 8px; color: $text-secondary; font-size: 13px; }
.actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.outline,.dark { height: 40px; line-height: 40px; padding: 0 18px; font-size: 14px; }
.outline { background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; }
.dark { background: $brand-primary; color: #f5d392; }
@media (max-width: 980px) {
  .expert-grid { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .page-head,.card-foot { flex-direction: column; align-items: stretch; }
  .expert-hero { align-items: flex-start; flex-direction: column; }
  .actions button { flex: 1; }
}
</style>
