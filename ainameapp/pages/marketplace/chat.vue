<template>
  <DashboardLayout currentMenu="expert">
    <view class="chat-page">
      <view class="thread-panel">
        <view class="panel-head">
          <view class="panel-title">我的咨询</view>
          <button class="small-btn" @click="goExperts">新建咨询</button>
        </view>
        <view class="filters">
          <text :class="statusFilter === '' ? 'active' : ''" @click="statusFilter = ''">全部</text>
          <text :class="statusFilter === 'OPEN' ? 'active' : ''" @click="statusFilter = 'OPEN'">服务中</text>
          <text :class="statusFilter === 'CLOSED' ? 'active' : ''" @click="statusFilter = 'CLOSED'">已完成</text>
        </view>
        <view class="search">搜索订单号、服务名称或专家</view>
        <scroll-view scroll-y class="thread-list">
          <view
            v-for="thread in filteredThreads"
            :key="thread.id"
            :class="['thread-item', activeThreadId === thread.id ? 'active' : '']"
            @click="selectThread(thread.id)"
          >
            <view class="avatar">{{ (thread.expert_name || '专').slice(0, 1) }}</view>
            <view class="thread-copy">
              <view class="thread-title">{{ thread.package_name || '专家咨询' }} <text>{{ statusText(thread.status) }}</text></view>
              <view class="thread-no">THREAD{{ thread.id }}</view>
              <view class="latest">{{ thread.latest_message || '暂无消息' }}</view>
            </view>
            <text class="time">{{ shortTime(thread.last_message_at || thread.created_time) }}</text>
          </view>
          <view v-if="!filteredThreads.length" class="empty">暂无咨询记录</view>
        </scroll-view>
        <button class="record-btn" @click="goAssets">咨询记录</button>
      </view>

      <view class="message-panel">
        <view class="message-head">
          <view class="back" @click="goExperts">‹</view>
          <view>
            <view class="message-title">与{{ detail?.expert_name || '专家' }}沟通</view>
            <view class="message-sub">{{ detail?.package_name || '选择左侧咨询' }}</view>
          </view>
          <button v-if="detail?.order" class="small-btn" @click="goOrder">查看订单</button>
        </view>

        <view v-if="detail" class="order-banner">
          <view class="doc-icon">文</view>
          <view>
            <view class="banner-title">{{ detail.package_name || '专家咨询' }}</view>
            <view class="banner-sub">订单编号：{{ detail.order ? `ORD${detail.order.id}` : '尚未下单' }}</view>
          </view>
          <text>{{ detail.order ? orderStatusText(detail.order.status) : statusText(detail.status) }}</text>
        </view>

        <scroll-view scroll-y class="messages">
          <view v-for="message in messages" :key="message.id" :class="['message', message.sender_user_id === currentUserId ? 'mine' : '']">
            <view class="bubble">
              <view>{{ message.content }}</view>
              <view v-if="message.attachments?.length" class="attachments">
                <view v-for="file in message.attachments" :key="file.id" class="attachment" @click="openAttachment(file)">
                  <text>附件</text>
                  <view>{{ file.file_name }}</view>
                </view>
              </view>
            </view>
          </view>
          <view v-if="detail && !messages.length" class="empty">还没有消息，可以先说明起名背景和关注点。</view>
          <view v-if="!detail" class="empty">请选择一个咨询会话</view>
        </scroll-view>

        <view class="composer">
          <button class="icon-btn" :disabled="!detail" @click="uploadAttachment">+</button>
          <textarea v-model="messageInput" :disabled="!detail" placeholder="输入消息"></textarea>
          <button class="send-btn" :disabled="!detail" :loading="sending" @click="sendMessage">发送</button>
        </view>
      </view>

      <view class="side-panel">
        <view class="side-card">
          <view class="side-title">订单信息</view>
          <view class="info-row"><text>服务名称</text><strong>{{ detail?.package_name || '-' }}</strong></view>
          <view class="info-row"><text>订单编号</text><strong>{{ detail?.order ? `ORD${detail.order.id}` : '-' }}</strong></view>
          <view class="info-row"><text>服务状态</text><strong>{{ detail?.order ? orderStatusText(detail.order.status) : statusText(detail?.status) }}</strong></view>
          <view class="info-row"><text>专家</text><strong>{{ detail?.expert_name || '-' }}</strong></view>
          <button class="outline-full" @click="goOrder">查看订单详情</button>
        </view>

        <view class="side-card">
          <view class="side-title">服务进度</view>
          <view v-for="(step,index) in progressSteps" :key="step.title" :class="['progress-row', index <= currentProgress ? 'done' : '']">
            <view class="dot">{{ index + 1 }}</view>
            <view><text>{{ step.title }}</text><text>{{ step.desc }}</text></view>
          </view>
        </view>

        <view class="side-card">
          <view class="side-title">推荐名字</view>
          <view class="name-chips">
            <text>青岚集</text><text>茶叙记</text><text>云上白</text>
          </view>
        </view>

        <view class="quick-grid">
          <button @click="goOrder">查看订单</button>
          <button @click="uploadAttachment">上传资料</button>
          <button @click="completeOrder">确认完成</button>
          <button @click="goExperts">联系专家</button>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const threads = ref([]);
const detail = ref(null);
const messages = ref([]);
const activeThreadId = ref(null);
const statusFilter = ref('');
const messageInput = ref('');
const sending = ref(false);
let timer = null;

const currentUserId = computed(() => Number((uni.getStorageSync('user') || {}).id || 0));
const filteredThreads = computed(() => statusFilter.value ? threads.value.filter(item => item.status === statusFilter.value) : threads.value);
const progressSteps = [
  { title: '需求沟通', desc: '已了解命名信息与偏好' },
  { title: '命名分析中', desc: '专家正在分析方案' },
  { title: '方案输出', desc: '预计按服务周期交付' },
  { title: '方案确认', desc: '确认最终方案并交付报告' }
];
const currentProgress = computed(() => {
  const status = detail.value?.order?.status;
  if (['COMPLETED'].includes(status)) return 3;
  if (['DELIVERED'].includes(status)) return 2;
  if (['IN_PROGRESS', 'WAITING_ACCEPT', 'PAID'].includes(status)) return 1;
  return 0;
});

const statusText = status => ({
  OPEN: '咨询中',
  CLOSED: '已关闭'
}[status] || status || '-');
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
const shortTime = value => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
};
const clearTimer = () => {
  if (timer) clearInterval(timer);
  timer = null;
};
const startTimer = () => {
  clearTimer();
  timer = setInterval(loadMessages, 5000);
};
const loadThreads = async () => {
  if (!uni.getStorageSync('token')) {
    uni.navigateTo({ url: '/pages/login/login' });
    return;
  }
  const result = await http.getMyExpertChatThreads(1, 50);
  threads.value = result.items || [];
  if (!activeThreadId.value && threads.value.length) activeThreadId.value = threads.value[0].id;
  if (activeThreadId.value) await selectThread(activeThreadId.value);
};
const selectThread = async id => {
  activeThreadId.value = Number(id);
  detail.value = await http.getExpertChatThread(activeThreadId.value);
  await loadMessages();
  startTimer();
};
const loadMessages = async () => {
  if (!activeThreadId.value) return;
  const result = await http.getExpertChatMessages(activeThreadId.value, 1, 100);
  messages.value = result.items || [];
  await http.markExpertChatRead(activeThreadId.value).catch(() => {});
};
const sendMessage = async () => {
  const content = messageInput.value.trim();
  if (!content || !activeThreadId.value) return;
  sending.value = true;
  try {
    messageInput.value = '';
    await http.sendExpertChatMessage(activeThreadId.value, content);
    await loadMessages();
    await loadThreads();
  } finally {
    sending.value = false;
  }
};
const uploadAttachment = () => {
  if (!activeThreadId.value) return;
  uni.chooseFile({
    count: 1,
    success: async result => {
      const file = result.tempFiles?.[0] || result.tempFilePaths?.[0];
      const path = file.path || file;
      await http.uploadExpertChatAttachment(activeThreadId.value, path);
      await loadMessages();
      await loadThreads();
    }
  });
};
const openAttachment = file => {
  if (file.file_url) {
    uni.showToast({ title: file.file_name, icon: 'none' });
  }
};
const goExperts = () => uni.redirectTo({ url: '/pages/marketplace/index' });
const goAssets = () => uni.redirectTo({ url: '/pages/assets/index?tab=orders' });
const goOrder = () => {
  if (detail.value?.order) uni.redirectTo({ url: '/pages/assets/index?tab=orders' });
};
const completeOrder = async () => {
  if (!detail.value?.order?.id) return uni.showToast({ title: '暂无可完成订单', icon: 'none' });
  await http.completeExpertOrder(detail.value.order.id);
  await selectThread(activeThreadId.value);
};

onLoad(query => {
  if (query?.thread_id) activeThreadId.value = Number(query.thread_id);
});
onShow(loadThreads);
onBeforeUnmount(clearTimer);
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.chat-page { height: calc(100vh - 132px); min-height: 680px; display: grid; grid-template-columns: 320px minmax(0,1fr) 320px; gap: 14px; max-width: 1500px; margin: 0 auto; }
.thread-panel,.message-panel,.side-panel { min-height: 0; }
.thread-panel,.message-panel,.side-card,.quick-grid { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.thread-panel { padding: 20px; display: flex; flex-direction: column; }
.panel-head,.message-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.panel-title,.message-title,.side-title { color: $brand-primary; font-weight: 900; }
.panel-title { font-size: 20px; }
.small-btn { height: 34px; line-height: 32px; margin: 0; padding: 0 16px; border: 1px solid #e7e0d4; background: #fff; color: $brand-primary; border-radius: 999px; font-size: 13px; font-weight: 900; }
.small-btn::after,.record-btn::after,.send-btn::after,.outline-full::after,.quick-grid button::after,.icon-btn::after { border: none; }
.filters { display: flex; gap: 18px; margin: 22px 0; color: $text-secondary; font-size: 13px; }
.filters text { cursor: pointer; padding-bottom: 8px; border-bottom: 2px solid transparent; }
.filters .active { color: $brand-primary; border-bottom-color: $brand-primary; font-weight: 900; }
.search { height: 40px; line-height: 40px; border: 1px solid #e7e0d4; border-radius: 999px; padding: 0 16px; color: #a3a9b5; font-size: 13px; background: #fbfaf7; margin-bottom: 12px; }
.thread-list { flex: 1; min-height: 0; }
.thread-item { display: grid; grid-template-columns: 42px minmax(0,1fr) auto; gap: 12px; padding: 14px 12px; border-radius: 10px; cursor: pointer; }
.thread-item.active { background: #f7f1e7; }
.avatar { width: 42px; height: 42px; border-radius: 50%; background: $brand-primary; color: #f5d392; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.thread-copy { min-width: 0; }
.thread-title { color: $brand-primary; font-weight: 900; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.thread-title text { margin-left: 6px; color: #9b6a20; background: #f5e6c9; border-radius: 999px; padding: 3px 7px; font-size: 11px; }
.thread-no,.latest,.time { color: $text-secondary; font-size: 12px; margin-top: 5px; }
.latest { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.record-btn { height: 42px; line-height: 42px; margin: 16px 0 0; background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.45); border-radius: 8px; font-weight: 900; }
.message-panel { padding: 18px; display: flex; flex-direction: column; min-width: 0; }
.back { color: $brand-primary; font-size: 34px; line-height: 1; cursor: pointer; }
.message-sub { margin-top: 4px; color: $text-secondary; font-size: 13px; }
.order-banner { margin: 18px 0; padding: 22px 28px; border-radius: 10px; background: linear-gradient(135deg,#17243b,#24324a); color: #fff; display: grid; grid-template-columns: 48px minmax(0,1fr) auto; gap: 16px; align-items: center; overflow: hidden; }
.doc-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.14); color: #f5d392; font-weight: 900; }
.banner-title { font-size: 22px; font-weight: 900; }
.banner-sub { margin-top: 6px; color: rgba(255,255,255,.7); font-size: 13px; }
.order-banner>text { color: #f5d392; font-weight: 900; }
.messages { flex: 1; min-height: 0; padding: 8px 6px; box-sizing: border-box; }
.message { display: flex; margin-bottom: 14px; }
.message.mine { justify-content: flex-end; }
.bubble { max-width: 72%; padding: 12px 16px; border-radius: 10px; background: #fff; border: 1px solid #e7e0d4; color: $text-main; font-size: 14px; line-height: 1.7; white-space: pre-wrap; box-shadow: 0 10px 24px rgba(36,50,74,.06); }
.message.mine .bubble { background: $brand-primary; border-color: $brand-primary; color: #fff; }
.attachments { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.attachment { padding: 10px; border-radius: 8px; background: rgba(255,255,255,.12); border: 1px solid rgba(199,154,75,.34); }
.attachment text { color: #d6b064; font-size: 12px; }
.attachment view { margin-top: 2px; font-weight: 900; }
.composer { display: grid; grid-template-columns: 44px minmax(0,1fr) 94px; gap: 12px; align-items: end; border-top: 1px solid #eee7dc; padding-top: 16px; }
.icon-btn,.send-btn { margin: 0; height: 46px; line-height: 46px; border-radius: 999px; font-weight: 900; }
.icon-btn { background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; }
.send-btn { background: $brand-primary; color: #f5d392; }
textarea { height: 46px; min-height: 46px; box-sizing: border-box; padding: 12px 16px; border: 1px solid #e7e0d4; background: #fbfaf7; border-radius: 999px; font-size: 14px; }
.side-panel { display: flex; flex-direction: column; gap: 14px; }
.side-card { padding: 22px; }
.info-row { display: flex; justify-content: space-between; gap: 12px; padding: 13px 0; }
.info-row text { color: $text-secondary; font-size: 13px; }
.info-row strong { color: $brand-primary; font-size: 13px; text-align: right; }
.outline-full { width: 100%; height: 40px; line-height: 40px; margin: 14px 0 0; background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.5); border-radius: 8px; font-weight: 900; }
.progress-row { display: grid; grid-template-columns: 28px minmax(0,1fr); gap: 10px; padding: 12px 0; }
.dot { width: 24px; height: 24px; border-radius: 50%; border: 1px solid #d8dde6; color: #8a92a0; display: flex; align-items: center; justify-content: center; font-size: 12px; }
.progress-row.done .dot { background: $brand-gold; border-color: $brand-gold; color: #fff; }
.progress-row text:first-child { display: block; color: $brand-primary; font-weight: 900; font-size: 13px; }
.progress-row text:last-child { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }
.name-chips { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.name-chips text { padding: 10px 16px; border-radius: 8px; background: #fffbf2; border: 1px solid #ead6ad; color: #b68136; font-weight: 900; }
.quick-grid { padding: 18px; display: grid; grid-template-columns: repeat(2,1fr); gap: 12px; }
.quick-grid button { height: 58px; line-height: 58px; margin: 0; background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; border-radius: 8px; font-size: 13px; }
.empty { padding: 46px 10px; text-align: center; color: #8a92a0; }
@media (max-width: 1180px) {
  .chat-page { grid-template-columns: 280px minmax(0,1fr); }
  .side-panel { display: none; }
}
@media (max-width: 760px) {
  .chat-page { height: auto; min-height: 0; grid-template-columns: 1fr; }
  .thread-panel { max-height: 330px; }
  .message-panel { min-height: 620px; }
  .bubble { max-width: 86%; }
}
</style>
