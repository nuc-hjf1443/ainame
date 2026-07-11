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
        <view class="workbench-grid">
          <view class="wallet-card">
            <view class="card-title">专家钱包</view>
            <view class="balance-grid">
              <view><text>可提现</text><strong>¥{{ wallet?.available_balance || '0.00' }}</strong></view>
              <view><text>提现中</text><strong>¥{{ wallet?.withdrawing_balance || '0.00' }}</strong></view>
              <view><text>累计收入</text><strong>¥{{ wallet?.total_income || '0.00' }}</strong></view>
              <view><text>累计提现</text><strong>¥{{ wallet?.total_withdrawn || '0.00' }}</strong></view>
            </view>
            <view class="withdraw-form">
              <input class="mini-input" type="digit" :value="withdrawalForm.amount" placeholder="提现金额" @input="withdrawalForm.amount = $event.detail.value" />
              <input class="mini-input" :value="withdrawalForm.alipay_account" placeholder="支付宝账号" @input="withdrawalForm.alipay_account = $event.detail.value" />
              <input class="mini-input" :value="withdrawalForm.real_name" placeholder="真实姓名" @input="withdrawalForm.real_name = $event.detail.value" />
              <button class="primary" :loading="withdrawing" @click="createWithdrawal">申请提现</button>
            </view>
            <view v-for="item in withdrawals.slice(0, 3)" :key="item.id" class="withdraw-row">
              <text>¥{{ item.amount }}</text><text>{{ withdrawalStatusText(item.status) }}</text>
            </view>
          </view>

          <view class="wallet-card">
            <view class="card-title">客户咨询</view>
            <view v-for="thread in chatThreads.slice(0, 5)" :key="thread.id" class="thread-row" @click="openChatThread(thread)">
              <view>
                <text class="thread-name">{{ thread.customer_name || '客户' }}</text>
                <text class="sub">{{ thread.package_name || '-' }}</text>
              </view>
              <text v-if="thread.expert_unread_count" class="badge">{{ thread.expert_unread_count }}</text>
            </view>
            <view v-if="!chatThreads.length" class="sub">暂无客户咨询</view>
          </view>
        </view>
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
          <view v-if="order.chat_thread_id" class="actions" @click.stop>
            <button size="mini" class="outline" @click="openOrderChat(order)">专家聊天</button>
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
            <view v-if="selectedOrder.chat_thread_id" class="actions">
              <button size="mini" class="outline" @click="openOrderChat(selectedOrder)">专家聊天</button>
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

        <view v-if="chatOpen" class="overlay" @click="closeChat">
          <view class="sheet chat-sheet" @click.stop>
            <view class="sheet-head">
              <view>
                <view class="sheet-title">客户咨询</view>
                <view class="meta">{{ activeThread?.customer_name || activeThread?.asset_name || '客户' }} · {{ activeThread?.package_name || '-' }}</view>
              </view>
              <text class="status" @click="closeChat">关闭</text>
            </view>
            <scroll-view class="chat-messages" scroll-y>
              <view v-for="message in chatMessages" :key="message.id" :class="['chat-message', message.sender_user_id === currentUserId ? 'mine' : '']">
                <view class="bubble">{{ message.content }}</view>
              </view>
              <view v-if="!chatMessages.length" class="empty">暂无聊天记录</view>
            </scroll-view>
            <view class="chat-compose">
              <textarea class="chat-input" :value="chatInput" placeholder="输入回复" @input="chatInput = $event.detail.value" />
              <button class="primary" :loading="chatSending" @click="sendChatMessage">发送</button>
            </view>
          </view>
        </view>
      </template>
    </view>
  </DashboardLayout>
</template>
<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const orders = ref([]);
const status = ref('');
const forbidden = ref(false);
const detailOpen = ref(false);
const selectedOrder = ref(null);
const wallet = ref(null);
const withdrawals = ref([]);
const withdrawing = ref(false);
const chatThreads = ref([]);
const chatOpen = ref(false);
const activeThread = ref(null);
const chatMessages = ref([]);
const chatInput = ref('');
const chatSending = ref(false);
const chatTimer = ref(null);
const reports = reactive({});
const withdrawalForm = reactive({ amount: '', alipay_account: '', real_name: '' });
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
const withdrawalStatusText = value => ({
  PENDING: '待审核',
  APPROVED: '已通过',
  REJECTED: '已驳回'
}[value] || value || '-');
const currentUserId = computed(() => Number((uni.getStorageSync('user') || {}).id || 0));
const emptyReport = () => Object.fromEntries(reportFields.map(item => [item.key, '']));
const loadWalletAndChats = async () => {
  const [walletResult, withdrawalResult, threadResult] = await Promise.allSettled([
    http.getExpertWallet(),
    http.getExpertWithdrawals(1, 20),
    http.getExpertChatThreads(1, 50)
  ]);
  if (walletResult.status === 'fulfilled') wallet.value = walletResult.value;
  if (withdrawalResult.status === 'fulfilled') withdrawals.value = withdrawalResult.value.items || [];
  if (threadResult.status === 'fulfilled') chatThreads.value = threadResult.value.items || [];
};
const load = async () => {
  try {
    forbidden.value = false;
    const res = await http.getExpertWorkOrders(status.value);
    orders.value = res.items;
    orders.value.forEach(order => {
      reports[order.id] = { ...emptyReport(), ...(order.report || {}) };
    });
    await loadWalletAndChats();
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
const createWithdrawal = async () => {
  const amount = Number(withdrawalForm.amount);
  if (!Number.isFinite(amount) || amount < 1) return uni.showToast({ title: '提现金额至少 1 元', icon: 'none' });
  if (!withdrawalForm.alipay_account.trim() || !withdrawalForm.real_name.trim()) return uni.showToast({ title: '请填写支付宝账号和真实姓名', icon: 'none' });
  withdrawing.value = true;
  try {
    await http.createExpertWithdrawal({
      amount,
      alipay_account: withdrawalForm.alipay_account.trim(),
      real_name: withdrawalForm.real_name.trim()
    });
    Object.assign(withdrawalForm, { amount: '', alipay_account: '', real_name: '' });
    uni.showToast({ title: '提现申请已提交', icon: 'none' });
    await loadWalletAndChats();
  } finally {
    withdrawing.value = false;
  }
};
const clearChatTimer = () => {
  if (chatTimer.value) clearInterval(chatTimer.value);
  chatTimer.value = null;
};
const loadChatMessages = async () => {
  if (!activeThread.value?.id) return;
  const result = await http.getExpertChatMessages(activeThread.value.id, 1, 50);
  chatMessages.value = result.items || [];
  await http.markExpertChatRead(activeThread.value.id).catch(() => {});
};
const openChatThread = async thread => {
  activeThread.value = thread;
  chatOpen.value = true;
  await loadChatMessages();
  clearChatTimer();
  chatTimer.value = setInterval(loadChatMessages, 5000);
};
const openOrderChat = order => {
  closeOrderDetail();
  openChatThread({
    id: order.chat_thread_id,
    customer_name: order.customer_name,
    asset_name: order.asset_name,
    package_name: order.package_name
  });
};
const closeChat = () => {
  chatOpen.value = false;
  activeThread.value = null;
  chatMessages.value = [];
  chatInput.value = '';
  clearChatTimer();
};
const sendChatMessage = async () => {
  const content = chatInput.value.trim();
  if (!content || !activeThread.value?.id) return;
  chatSending.value = true;
  try {
    chatInput.value = '';
    await http.sendExpertChatMessage(activeThread.value.id, content);
    await loadChatMessages();
    await loadWalletAndChats();
  } finally {
    chatSending.value = false;
  }
};

onShow(load);
onBeforeUnmount(clearChatTimer);
</script>
<style scoped>
.page{min-height:100%;box-sizing:border-box}.title{font-size:40rpx;font-weight:700;display:block}.sub,.meta{font-size:24rpx;color:#64748b;display:block;margin-top:8rpx}.filters{display:flex;gap:10rpx;overflow-x:auto;margin:26rpx 0}.chip{padding:12rpx 20rpx;background:#fff;border-radius:8rpx;white-space:nowrap}.chip.active{background:#24324a;color:#fff}.order,.empty-card,.wallet-card{background:#fff;border:1px solid #e2e8f0;border-radius:8rpx;padding:28rpx;margin-bottom:20rpx}.workbench-grid{display:grid;grid-template-columns:1.4fr 1fr;gap:20rpx;margin-top:24rpx}.card-title{font-size:30rpx;font-weight:700;margin-bottom:18rpx}.balance-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14rpx}.balance-grid view{background:#f8fafc;border-radius:8rpx;padding:16rpx}.balance-grid text{display:block;color:#64748b;font-size:23rpx}.balance-grid strong{display:block;margin-top:8rpx;font-size:30rpx;color:#0f172a}.withdraw-form{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12rpx;margin-top:18rpx}.mini-input{height:72rpx;background:#f8fafc;border:1px solid #cbd5e1;border-radius:8rpx;padding:0 16rpx;box-sizing:border-box}.withdraw-form .primary{margin-top:0}.withdraw-row,.thread-row{display:flex;justify-content:space-between;gap:16rpx;border-top:1px solid #eef2f7;padding-top:14rpx;margin-top:14rpx;font-size:25rpx}.thread-row{cursor:pointer;align-items:center}.thread-name{font-weight:700}.badge{background:#ef4444;color:#fff;border-radius:999px;min-width:34rpx;height:34rpx;line-height:34rpx;text-align:center;font-size:22rpx}.compact-order{cursor:pointer;transition:border-color .2s,box-shadow .2s}.compact-order:hover{border-color:#ead6ad;box-shadow:0 10rpx 30rpx rgba(199,154,75,.14)}.order-head,.sheet-head{display:flex;justify-content:space-between;gap:20rpx;align-items:flex-start}.order-main{min-width:0}.name{font-size:34rpx;font-weight:700}.status{color:#24324a;white-space:nowrap}.summary-row{display:flex;justify-content:space-between;gap:30rpx;border-top:1px solid #eef2f7;padding-top:16rpx;margin-top:16rpx;font-size:25rpx}.summary-row text:first-child,.detail-grid text:first-child{color:#64748b;flex-shrink:0}.summary-row text:last-child{text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.actions{display:flex;gap:14rpx;margin-top:18rpx;flex-wrap:wrap}.actions button{margin:0}.outline,.draft{background:#fff;color:#24324a;border:1px solid #ead6ad}.submit,.primary{background:#24324a;color:#fff}.primary{border-radius:8rpx;margin-top:24rpx}.editor{margin-top:24rpx;border-top:1px solid #eef2f7;padding-top:20rpx}.label{font-weight:700;margin:18rpx 0 8rpx}.area{width:100%;height:130rpx;box-sizing:border-box;background:#f8fafc;padding:16rpx;border-radius:8rpx}.report-text{background:#f8fafc;border-radius:8rpx;padding:18rpx;line-height:1.7;color:#334155;white-space:pre-wrap}.empty{text-align:center;padding:100rpx;color:#94a3b8}.overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:200;display:flex;align-items:center;justify-content:center;padding:36rpx}.sheet{width:min(980rpx,100%);max-height:86vh;overflow-y:auto;background:#fff;border-radius:8rpx;padding:34rpx}.sheet-title{font-size:36rpx;font-weight:700}.detail-grid{display:grid;gap:16rpx;border-top:1px solid #eef2f7;border-bottom:1px solid #eef2f7;margin-top:24rpx;padding:20rpx 0}.detail-grid view{display:flex;gap:24rpx;font-size:26rpx;line-height:1.6}.close-btn{margin-left:0}.chat-sheet{width:min(880rpx,100%)}.chat-messages{height:48vh;background:#f8fafc;border:1px solid #eef2f7;border-radius:8rpx;padding:20rpx;box-sizing:border-box}.chat-message{display:flex;margin-bottom:16rpx}.chat-message.mine{justify-content:flex-end}.bubble{max-width:76%;background:#fff;border:1px solid #e2e8f0;border-radius:8rpx;padding:16rpx 20rpx;font-size:26rpx;line-height:1.6;white-space:pre-wrap}.chat-message.mine .bubble{background:#f5e6c9;border-color:#ead6ad}.chat-compose{display:flex;gap:14rpx;margin-top:18rpx;align-items:flex-end}.chat-input{flex:1;height:110rpx;border:1px solid #cbd5e1;border-radius:8rpx;padding:18rpx;box-sizing:border-box}.chat-compose button{width:150rpx;margin:0}
@media(max-width:900px){.workbench-grid,.balance-grid,.withdraw-form{grid-template-columns:1fr}.chat-compose{flex-direction:column;align-items:stretch}.chat-compose button{width:100%}}
</style>

