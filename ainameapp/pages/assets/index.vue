<template>
  <DashboardLayout currentMenu="assets">
    <view class="assets-page">
      <view class="page-head">
        <view>
          <view class="title">资产中心</view>
          <view class="sub">管理您的命名资产、品牌方案与专家订单。</view>
        </view>
      </view>

      <view class="layout">
        <view class="main-card">
          <view class="tabs">
            <view v-for="item in tabs" :key="item.key" :class="['tab', activeTab === item.key ? 'active' : '']" @click="activeTab = item.key">{{ item.label }}</view>
          </view>

          <view v-if="activeTab === 'names'" class="toolbar">
            <view class="search">搜索名称、行业或关键词</view>
            <button class="outline" @click="goHome">创建新名称资产</button>
          </view>

          <view v-if="activeTab === 'names'" class="asset-list">
            <view v-for="item in names" :key="item.id" class="name-row">
              <view class="name-cover">{{ item.name.slice(0,1) }}</view>
              <view class="name-main">
                <view><text class="asset-name">{{ item.name }}</text><text class="saved">已保存</text></view>
                <view class="muted">类型：{{ item.category }} ｜ 创建时间：{{ formatTime(item.created_time) }}</view>
                <view class="reference">{{ item.moral || item.reference || '暂无说明' }}</view>
              </view>
              <view class="status-col">
                <text :class="domainOk(item) ? 'ok' : 'warn'">{{ item.domain_status || '-' }}</text>
                <text>{{ brandKitStatus(item) }}</text>
              </view>
              <view class="actions">
                <button @click="viewName(item)">查看详情</button>
                <button @click="goBrand(item)">{{ nameMatchedKit(item) ? '管理品牌' : '生成品牌' }}</button>
                <button @click="publishName(item)">发布投票</button>
                <button @click="downloadReport(item)">导出报告</button>
              </view>
            </view>
            <view v-if="!names.length" class="empty">暂无名称资产</view>
          </view>

          <view v-if="activeTab === 'kits'" class="kit-grid">
            <view v-for="kit in kits" :key="kit.id" class="kit-card" @click="openKit(kit)">
              <view class="kit-head"><view><view class="asset-name">{{ kit.name }}</view><view class="muted">{{ kit.industry }} ｜ {{ kit.design_style }}</view></view><text :class="['tag', kit.status]">{{ statusText(kit.status) }}</text></view>
              <view class="visual-grid">
                <view v-for="asset in kit.assets.slice(0,4)" :key="asset.id" class="visual-tile">
                  <image v-if="assetImageUrl(asset)" :src="assetImageUrl(asset)" mode="aspectFill" />
                  <view v-else>{{ statusText(asset.status) }}</view>
                </view>
              </view>
              <view class="kit-actions">
                <button @click.stop="openKit(kit)">管理素材</button>
                <button @click.stop="deleteKit(kit)">删除方案</button>
              </view>
            </view>
            <view v-if="!kits.length" class="empty">暂无品牌方案</view>
          </view>

          <view v-if="activeTab === 'visuals'" class="kit-grid">
            <view v-for="item in visuals" :key="item.id" class="visual-card">
              <image v-if="assetImageUrl(item)" :src="assetImageUrl(item)" mode="aspectFill" />
              <view v-else class="visual-placeholder">{{ statusText(item.status) }}</view>
              <view class="asset-name small">{{ item.name }}</view>
              <view class="muted">{{ item.slogan || item.category }}</view>
            </view>
            <view v-if="!visuals.length" class="empty">暂无视觉素材</view>
          </view>

          <view v-if="activeTab === 'orders'" class="asset-list">
            <view v-for="order in orders" :key="order.id" class="order-row">
              <view>
                <view class="asset-name">{{ order.package_name }}</view>
                <view class="muted">专家：{{ order.expert_name }} ｜ 名称：{{ order.asset_name }}</view>
                <view class="reference">需求：{{ order.requirements }}</view>
              </view>
              <text class="tag">{{ orderStatusText(order.status) }}</text>
              <view class="actions">
                <button v-if="order.chat_thread_id" @click="openChat(order)">专家聊天</button>
                <button v-if="order.status === 'DELIVERED'" @click="completeOrder(order)">确认完成</button>
              </view>
            </view>
            <view v-if="!orders.length" class="empty">暂无专家订单</view>
          </view>
        </view>

        <view class="side">
          <view class="side-card">
            <view class="side-title">资产概览</view>
            <view class="stat-grid">
              <view><strong>{{ names.length }}</strong><text>名称资产总数</text></view>
              <view><strong>{{ kits.length }}</strong><text>已生成品牌套件</text></view>
              <view><strong>{{ domainAvailableCount }}</strong><text>可注册域名</text></view>
              <view><strong>{{ orders.length }}</strong><text>专家订单</text></view>
            </view>
          </view>
          <view class="side-card">
            <view class="side-title">快捷操作</view>
            <view class="quick" @click="goHome"><text>创建新名称资产</text><text>AI 智能生成好名字</text></view>
            <view class="quick" @click="goMarketplace"><text>专家服务</text><text>购买真人精批服务</text></view>
            <view class="quick" @click="goCommunity"><text>发布投票活动</text><text>邀请用户参与名称投票</text></view>
          </view>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const tabs = [
  { key: 'names', label: '名称资产' },
  { key: 'kits', label: '品牌方案' },
  { key: 'visuals', label: '视觉素材' },
  { key: 'orders', label: '专家订单' }
];
const activeTab = ref('names');
const names = ref([]);
const kits = ref([]);
const visuals = ref([]);
const orders = ref([]);
const domainAvailableCount = computed(() => names.value.filter(domainOk).length);
const assetImageUrl = asset => http.normalizeAssetUrl(asset?.image_url);
const nameMatchedKit = item => kits.value.find(kit =>
  kit.naming_asset_id === item.id
  || (kit.thread_id && kit.thread_id === item.thread_id)
  || (kit.name === item.name && (!kit.moral || !item.moral || kit.moral === item.moral))
);
const brandKitStatus = item => {
  const kit = nameMatchedKit(item);
  if (!kit) return '未生成品牌';
  const map = { PENDING: '品牌待生成', PROCESSING: '品牌生成中', SUCCESS: '品牌已生成', FAILED: '品牌待完善' };
  return map[kit.status] || '品牌已生成';
};

const load = async () => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  const [nameResult, kitResult, visualResult, orderResult] = await Promise.all([
    http.getNameAssets(),
    http.getBrandKits(),
    http.getVisualAssets(),
    http.getMyExpertOrders()
  ]);
  names.value = nameResult.items || [];
  kits.value = kitResult.items || [];
  visuals.value = visualResult.items || [];
  orders.value = orderResult.items || [];
};
const formatTime = value => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
};
function domainOk(item) {
  return String(item.domain_status || '').includes('可') || String(item.domain_status || '').includes('✅');
}
const statusText = status => ({ PENDING: '等待生成', PROCESSING: '生成中', SUCCESS: '已完成', FAILED: '失败' }[status] || status || '-');
const orderStatusText = status => ({
  PENDING_PAYMENT: '待支付',
  WAITING_PAYMENT: '待支付',
  WAITING_ACCEPT: '待专家接单',
  PAID: '已支付',
  ACCEPTED: '已接单',
  IN_PROGRESS: '服务中',
  DELIVERED: '已交付',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  REJECTED: '已拒单',
  REFUNDING: '退款中',
  REFUNDED: '已退款'
}[status] || status || '-');
const goHome = () => uni.redirectTo({ url: '/pages/home/index' });
const goMarketplace = () => uni.redirectTo({ url: '/pages/marketplace/index' });
const goCommunity = () => uni.redirectTo({ url: '/pages/community/index' });
const viewName = item => uni.showModal({ title: item.name, content: item.moral || item.reference || '暂无说明', showCancel: false });
const goBrand = item => {
  const kit = nameMatchedKit(item);
  if (kit) {
    openKit(kit);
    return;
  }
  uni.setStorageSync('brandKitDraft', {
    naming_asset_id: item.id,
    thread_id: item.thread_id,
    name: item.name,
    moral: item.moral || '',
    industry_hint: item.category === '企业名' ? item.name : ''
  });
  uni.redirectTo({ url: '/pages/brand-kit/index' });
};
const publishName = item => {
  uni.setStorageSync('communityPublishDraft', { item });
  uni.navigateTo({ url: '/pages/community/publish' });
};
const downloadReport = async item => {
  const path = await http.downloadNameReport(item.id);
  uni.showToast({ title: '报告已生成', icon: 'none' });
  if (typeof window !== 'undefined') window.open(path, '_blank');
};
const openKit = kit => {
  uni.setStorageSync('activeBrandKit', { id: kit.id, name: kit.name });
  uni.setStorageSync('brandKitDraft', { naming_asset_id: kit.naming_asset_id, thread_id: `kit_${kit.id}`, name: kit.name, moral: kit.moral || '', industry_hint: kit.industry });
  uni.redirectTo({ url: '/pages/brand-kit/index' });
};
const deleteKit = kit => {
  uni.showModal({
    title: '删除品牌方案',
    content: `确定删除「${kit.name}」的品牌方案和素材吗？`,
    success: async res => {
      if (!res.confirm) return;
      await http.deleteBrandKit(kit.id);
      await load();
    }
  });
};
const openChat = order => uni.navigateTo({ url: `/pages/marketplace/chat?thread_id=${order.chat_thread_id}` });
const completeOrder = async order => {
  await http.completeExpertOrder(order.id);
  await load();
};
onLoad(query => { if (query?.tab) activeTab.value = String(query.tab); });
onShow(load);
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.assets-page { max-width: 1320px; margin: 0 auto; }
.page-head { margin: 28px 0 24px; }
.title { color: $brand-primary; font-size: 40px; font-weight: 900; line-height: 1.1; }
.sub,.muted,.reference { color: $text-secondary; }
.sub { margin-top: 10px; }
.layout { display: grid; grid-template-columns: minmax(0,1fr) 300px; gap: 18px; align-items: start; }
.main-card,.side-card,.name-row,.kit-card,.visual-card,.order-row { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.main-card { padding: 18px; }
.tabs { display: grid; grid-template-columns: repeat(4,1fr); border-bottom: 1px solid #eee7dc; margin-bottom: 20px; }
.tab { min-height: 54px; display: flex; align-items: center; justify-content: center; color: $text-secondary; font-weight: 900; border-bottom: 3px solid transparent; cursor: pointer; }
.tab.active { color: $brand-primary; border-bottom-color: $brand-gold; }
.toolbar { display: flex; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
.search { flex: 1; height: 42px; line-height: 42px; padding: 0 16px; border: 1px solid #e7e0d4; border-radius: 999px; color: #a3a9b5; background: #fbfaf7; }
.outline { margin: 0; height: 42px; line-height: 40px; padding: 0 18px; border-radius: 8px; background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.5); font-weight: 900; }
.outline::after,.actions button::after { border: none; }
.asset-list { display: flex; flex-direction: column; gap: 12px; }
.name-row,.order-row { display: grid; grid-template-columns: 86px minmax(0,1fr) 160px 280px; gap: 16px; align-items: center; padding: 18px; }
.order-row { grid-template-columns: minmax(0,1fr) 120px 220px; }
.name-cover { width: 78px; height: 78px; border-radius: 12px; background: linear-gradient(135deg,#17243b,#24324a); color: #f5d392; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 900; }
.asset-name { color: $brand-primary; font-size: 22px; font-weight: 900; }
.asset-name.small { font-size: 17px; margin: 12px 12px 4px; }
.saved,.tag { display: inline-block; margin-left: 8px; padding: 5px 10px; border-radius: 999px; color: #9b6a20; background: #f5e6c9; font-size: 12px; font-weight: 900; }
.reference { font-size: 13px; line-height: 1.6; margin-top: 8px; }
.status-col { display: grid; gap: 8px; font-weight: 900; font-size: 13px; }
.ok { color: #067647; }
.warn { color: #b54708; }
.actions { display: grid; grid-template-columns: repeat(2,1fr); gap: 8px; }
.actions button { margin: 0; height: 34px; line-height: 34px; border-radius: 8px; background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; font-size: 12px; font-weight: 900; }
.kit-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; }
.kit-card { padding: 18px; cursor: pointer; }
.kit-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 16px; }
.visual-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; }
.visual-tile,.visual-card image,.visual-placeholder { height: 120px; border-radius: 8px; background: #fbfaf7; border: 1px solid #eee7dc; overflow: hidden; display: flex; align-items: center; justify-content: center; color: $text-secondary; font-size: 12px; }
.visual-tile image { width: 100%; height: 100%; }
.kit-actions { display: grid; grid-template-columns: repeat(2,1fr); gap: 8px; margin-top: 12px; }
.kit-actions button { margin: 0; height: 34px; line-height: 34px; border-radius: 8px; background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; font-size: 12px; font-weight: 900; }
.kit-actions button::after { border: none; }
.visual-card { overflow: hidden; padding-bottom: 14px; }
.visual-card image,.visual-placeholder { width: 100%; height: 190px; border-radius: 0; border: none; }
.side-card { padding: 22px; margin-bottom: 14px; }
.side-title { color: $brand-primary; font-size: 18px; font-weight: 900; }
.stat-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 12px; margin-top: 16px; }
.stat-grid view { background: #fbfaf7; border: 1px solid #eee7dc; border-radius: 8px; padding: 16px; }
.stat-grid strong { color: $brand-primary; font-size: 24px; }
.stat-grid text { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }
.quick { padding: 15px 0; border-bottom: 1px solid #eee7dc; cursor: pointer; }
.quick text:first-child { display: block; color: $brand-primary; font-weight: 900; }
.quick text:last-child { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }
.empty { grid-column: 1/-1; text-align: center; color: #8a92a0; padding: 60px 20px; }
@media (max-width: 1160px) { .layout { grid-template-columns: 1fr; } .side { display: none; } }
@media (max-width: 900px) { .name-row,.order-row { grid-template-columns: 1fr; } .kit-grid { grid-template-columns: 1fr; } .tabs { grid-template-columns: repeat(2,1fr); } .toolbar { flex-direction: column; } }
</style>
