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
        <view v-for="order in orders" :key="order.id" class="order">
          <view class="order-head"><view><text class="name">{{order.asset_name}}</text><text class="meta">{{order.package_name}} · {{order.requirements}}</text></view><text class="status">{{order.status}}</text></view>
          <view v-if="order.status==='WAITING_ACCEPT'" class="actions"><button size="mini" @click="accept(order.id)">接受</button><button size="mini" class="outline" @click="reject(order.id)">拒绝</button></view>
          <view v-if="order.status==='IN_PROGRESS' || order.status==='DELIVERED'" class="editor">
            <button v-if="order.status==='IN_PROGRESS'" size="mini" class="draft" @click="draft(order)">AI 生成草稿</button>
            <view v-for="field in reportFields" :key="field.key"><view class="label">{{field.label}}</view><textarea v-model="reports[order.id][field.key]" class="area"/></view>
            <view v-if="order.status==='IN_PROGRESS'" class="actions"><button size="mini" @click="save(order)">保存</button><button size="mini" class="submit" @click="submit(order)">提交报告</button></view>
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
const accept = async id => { await http.acceptExpertOrder(id); load(); };
const reject = id => uni.showModal({
  title: '拒绝订单',
  editable: true,
  placeholderText: '说明拒绝原因',
  success: async result => {
    if (result.confirm && result.content) {
      await http.rejectExpertOrder(id, result.content);
      load();
    }
  }
});
const draft = async order => { reports[order.id] = await http.generateReportDraft(order.id); };
const save = async order => { await http.saveExpertReport(order.id, reports[order.id]); uni.showToast({ title: '已保存' }); };
const submit = async order => { await http.submitExpertReport(order.id, reports[order.id]); load(); };
const goProfile = () => uni.redirectTo({ url: '/pages/profile/index' });

onShow(load);
</script>
<style scoped>
.page{min-height:100%;box-sizing:border-box}.title{font-size:40rpx;font-weight:700;display:block}.sub,.meta{font-size:24rpx;color:#64748b;display:block;margin-top:8rpx}.filters{display:flex;gap:10rpx;overflow-x:auto;margin:26rpx 0}.chip{padding:12rpx 20rpx;background:#fff;border-radius:8rpx;white-space:nowrap}.chip.active{background:#2563eb;color:#fff}.order,.empty-card{background:#fff;border:1px solid #e2e8f0;border-radius:8rpx;padding:28rpx;margin-bottom:20rpx}.order-head{display:flex;justify-content:space-between;gap:20rpx}.name{font-size:34rpx;font-weight:700}.status{color:#2563eb}.actions{display:flex;gap:14rpx;margin-top:18rpx}.actions button{margin:0}.outline,.draft{background:#fff;color:#2563eb;border:1px solid #bfdbfe}.submit,.primary{background:#2563eb;color:#fff}.primary{border-radius:8rpx;margin-top:24rpx}.editor{margin-top:24rpx;border-top:1px solid #eef2f7;padding-top:20rpx}.label{font-weight:700;margin:18rpx 0 8rpx}.area{width:100%;height:130rpx;box-sizing:border-box;background:#f8fafc;padding:16rpx;border-radius:8rpx}.empty{text-align:center;padding:100rpx;color:#94a3b8}
</style>
