<template>
  <DashboardLayout currentMenu="expert_workbench">
    <view class="page">
      <view v-if="forbidden" class="empty-card">
        <view class="title">暂不能访问专家工作台</view>
        <view class="sub">只有审核通过的专家可以处理精批订单。</view>
        <button class="primary" @click="goProfile">返回个人中心</button>
      </view>

      <template v-else>
        <view class="header"><view><text class="title">专家工作台</text><text class="sub">接单、分析并交付专业报告</text></view></view>
        <view class="filters"><view v-for="item in filters" :key="item.value" :class="['chip',status===item.value?'active':'']" @click="changeStatus(item.value)">{{item.label}}</view></view>
        <view v-if="!orders.length" class="empty">当前没有相关订单</view>
        <view v-for="order in orders" :key="order.id" class="order compact-order" @click="openOrderDetail(order)">
          <view class="order-head">
            <view class="order-main">
              <text class="name">{{order.asset_name}}</text>
              <text class="meta">订单 #{{order.id}} · {{order.package_name}}</text>
            </view>
            <text class="status">{{orderStatusText(order.status)}}</text>
          </view>
          <view class="summary-row"><text>需求</text><text>{{order.requirements || '-'}}</text></view>
          <view class="summary-row"><text>操作</text><text>点击查看详情</text></view>
          <view v-if="order.status==='WAITING_ACCEPT'" class="actions" @click.stop>
            <button size="mini" @click="accept(order.id)">接受</button>
            <button size="mini" class="outline" @click="reject(order.id)">拒绝</button>
          </view>
        </view>

        <view v-if="detailOpen && selectedOrder" class="overlay" @click="closeOrderDetail">
          <view class="sheet" @click.stop>
            <view class="sheet-head">
              <view>
                <view class="sheet-title">{{selectedOrder.asset_name}}</view>
                <view class="meta">订单 #{{selectedOrder.id}} · {{selectedOrder.package_name}}</view>
              </view>
              <text class="status">{{orderStatusText(selectedOrder.status)}}</text>
            </view>
            <view class="detail-grid">
              <view><text>订单状态</text><text>{{orderStatusText(selectedOrder.status)}}</text></view>
              <view><text>服务套餐</text><text>{{selectedOrder.package_name || '-'}}</text></view>
              <view><text>客户需求</text><text>{{selectedOrder.requirements || '-'}}</text></view>
            </view>
            <view v-if="selectedOrder.status==='WAITING_ACCEPT'" class="actions">
              <button size="mini" @click="accept(selectedOrder.id)">接受</button>
              <button size="mini" class="outline" @click="reject(selectedOrder.id)">拒绝</button>
            </view>
            <view v-if="selectedOrder.status==='IN_PROGRESS' || selectedOrder.status==='DELIVERED' || selectedOrder.status==='COMPLETED'" class="editor">
              <button v-if="selectedOrder.status==='IN_PROGRESS'" size="mini" class="draft" @click="draft(selectedOrder)">AI 生成草稿</button>
              <view v-for="field in reportFields" :key="field.key">
                <view class="label">{{field.label}}</view>
                <textarea v-if="selectedOrder.status==='IN_PROGRESS'" v-model="reports[selectedOrder.id][field.key]" class="area"/>
                <view v-else class="report-text">{{reports[selectedOrder.id]?.[field.key] || '-'}}</view>
              </view>
              <view v-if="selectedOrder.status==='IN_PROGRESS'" class="actions">
                <button size="mini" @click="save(selectedOrder)">保存</button>
                <button size="mini" class="submit" @click="submit(selectedOrder)">提交报告</button>
              </view>
            </view>
            <button class="primary close-btn" @click="closeOrderDetail">关闭</button>
          </view>
        </view>
      </template>
    </view>
  </DashboardLayout>
</template>
<script setup>
import { reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const orders = ref([]);
const status = ref('');
const forbidden = ref(false);
const detailOpen = ref(false);
const selectedOrder = ref(null);
const reports = reactive({});
const filters = [
  { label: '全部', value: '' },
  { label: '待接单', value: 'WAITING_ACCEPT' },
  { label: '进行中', value: 'IN_PROGRESS' },
  { label: '已交付', value: 'DELIVERED' },
  { label: '已完成', value: 'COMPLETED' }
];
const reportFields = [
  { key: 'overview', label: '名字概览' },
  { key: 'professional_analysis', label: '专业分析' },
  { key: 'phonetic_semantic_analysis', label: '音形义分析' },
  { key: 'communication_advantages', label: '传播优势' },
  { key: 'risk_notes', label: '风险提示' },
  { key: 'recommendations', label: '优化建议' },
  { key: 'conclusion', label: '结论' }
];
const orderStatusText = value => ({
  WAITING_ACCEPT: '待接单',
  IN_PROGRESS: '进行中',
  DELIVERED: '已交付',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  PENDING_PAYMENT: '待支付'
}[value] || value || '-');
const emptyReport = () => Object.fromEntries(reportFields.map(item => [item.key, '']));
const load = async () => {
  try {
    forbidden.value = false;
    const res = await http.getExpertWorkOrders(status.value);
    orders.value = res.items;
    orders.value.forEach(order => {
      reports[order.id] = { ...emptyReport(), ...(order.report || {}) };
    });
  } catch (e) {
    forbidden.value = true;
    orders.value = [];
  }
};
const changeStatus = value => { status.value = value; load(); };
const openOrderDetail = order => {
  if (!reports[order.id]) reports[order.id] = { ...emptyReport(), ...(order.report || {}) };
  selectedOrder.value = order;
  detailOpen.value = true;
};
const closeOrderDetail = () => {
  detailOpen.value = false;
  selectedOrder.value = null;
};
const accept = async id => { await http.acceptExpertOrder(id); closeOrderDetail(); load(); };
const reject = id => uni.showModal({
  title: '拒绝订单',
  editable: true,
  placeholderText: '说明拒绝原因',
  success: async result => {
    if (result.confirm && result.content) {
      await http.rejectExpertOrder(id, result.content);
      closeOrderDetail();
      load();
    }
  }
});
const draft = async order => { reports[order.id] = await http.generateReportDraft(order.id); };
const save = async order => { await http.saveExpertReport(order.id, reports[order.id]); uni.showToast({ title: '已保存' }); };
const submit = async order => { await http.submitExpertReport(order.id, reports[order.id]); closeOrderDetail(); load(); };
const goProfile = () => uni.redirectTo({ url: '/pages/profile/index' });

onShow(load);
</script>
<style scoped>
.page{min-height:100%;box-sizing:border-box}.title{font-size:40rpx;font-weight:700;display:block}.sub,.meta{font-size:24rpx;color:#64748b;display:block;margin-top:8rpx}.filters{display:flex;gap:10rpx;overflow-x:auto;margin:26rpx 0}.chip{padding:12rpx 20rpx;background:#fff;border-radius:8rpx;white-space:nowrap}.chip.active{background:#2563eb;color:#fff}.order,.empty-card{background:#fff;border:1px solid #e2e8f0;border-radius:8rpx;padding:28rpx;margin-bottom:20rpx}.compact-order{cursor:pointer;transition:border-color .2s,box-shadow .2s}.compact-order:hover{border-color:#bfdbfe;box-shadow:0 10rpx 30rpx rgba(37,99,235,.08)}.order-head,.sheet-head{display:flex;justify-content:space-between;gap:20rpx;align-items:flex-start}.order-main{min-width:0}.name{font-size:34rpx;font-weight:700}.status{color:#2563eb;white-space:nowrap}.summary-row{display:flex;justify-content:space-between;gap:30rpx;border-top:1px solid #eef2f7;padding-top:16rpx;margin-top:16rpx;font-size:25rpx}.summary-row text:first-child,.detail-grid text:first-child{color:#64748b;flex-shrink:0}.summary-row text:last-child{text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.actions{display:flex;gap:14rpx;margin-top:18rpx;flex-wrap:wrap}.actions button{margin:0}.outline,.draft{background:#fff;color:#2563eb;border:1px solid #bfdbfe}.submit,.primary{background:#2563eb;color:#fff}.primary{border-radius:8rpx;margin-top:24rpx}.editor{margin-top:24rpx;border-top:1px solid #eef2f7;padding-top:20rpx}.label{font-weight:700;margin:18rpx 0 8rpx}.area{width:100%;height:130rpx;box-sizing:border-box;background:#f8fafc;padding:16rpx;border-radius:8rpx}.report-text{background:#f8fafc;border-radius:8rpx;padding:18rpx;line-height:1.7;color:#334155;white-space:pre-wrap}.empty{text-align:center;padding:100rpx;color:#94a3b8}.overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:200;display:flex;align-items:center;justify-content:center;padding:36rpx}.sheet{width:min(980rpx,100%);max-height:86vh;overflow-y:auto;background:#fff;border-radius:8rpx;padding:34rpx}.sheet-title{font-size:36rpx;font-weight:700}.detail-grid{display:grid;gap:16rpx;border-top:1px solid #eef2f7;border-bottom:1px solid #eef2f7;margin-top:24rpx;padding:20rpx 0}.detail-grid view{display:flex;gap:24rpx;font-size:26rpx;line-height:1.6}.close-btn{margin-left:0}
</style>
