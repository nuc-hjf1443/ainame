<template>
  <view class="admin-page">
    <view class="topbar">
      <view>
        <view class="title">管理员后台</view>
        <view class="subtitle">运营、AI 配置与审计管理</view>
      </view>
      <view class="top-actions">
        <button class="ghost-btn" size="mini" @click="goHome">起名首页</button>
        <button class="logout-btn" size="mini" @click="logout">退出登录</button>
      </view>
    </view>

    <view class="layout">
      <view class="side-nav">
        <view
          v-for="item in modules"
          :key="item.key"
          :class="['nav-item', activeModule === item.key ? 'active' : '']"
          @click="switchModule(item.key)"
        >
          {{ item.label }}
        </view>
      </view>

      <view class="content">
        <view v-if="activeModule === 'users'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">用户管理</view>
              <view class="panel-desc">查看用户角色和封禁状态</view>
            </view>
            <button size="mini" @click="loadUsers">刷新</button>
          </view>

          <view v-if="users.loading" class="state">加载中...</view>
          <view v-else-if="!users.items.length" class="state">暂无用户数据</view>
          <scroll-view v-else scroll-x class="table-scroll">
            <view class="table min-users">
              <view class="tr th">
                <text>ID</text>
                <text>邮箱</text>
                <text>用户名</text>
                <text>角色</text>
                <text>状态</text>
                <text>操作</text>
              </view>
              <view class="tr" v-for="item in users.items" :key="item.id">
                <text>{{ item.id }}</text>
                <text>{{ item.email }}</text>
                <text>{{ item.username }}</text>
                <text>{{ item.role }}</text>
                <text :class="item.is_banned ? 'danger' : 'success'">
                  {{ item.is_banned ? '已封禁' : '正常' }}
                </text>
                <button size="mini" @click="toggleBan(item)">
                  {{ item.is_banned ? '解封' : '封禁' }}
                </button>
              </view>
            </view>
          </scroll-view>
          <view class="pager">
            <button size="mini" :disabled="users.page <= 1" @click="prevUsers">上一页</button>
            <text>第 {{ users.page }} 页 / 共 {{ users.total }} 条</text>
            <button size="mini" :disabled="users.page * pageSize >= users.total" @click="nextUsers">下一页</button>
          </view>
        </view>

        <view v-if="activeModule === 'orders'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">订单管理</view>
              <view class="panel-desc">查看充值订单，并按退款 ID 审批</view>
            </view>
            <button size="mini" @click="loadOrders">刷新</button>
          </view>

          <view v-if="orders.loading" class="state">加载中...</view>
          <view v-else-if="!orders.items.length" class="state">暂无订单数据</view>
          <scroll-view v-else scroll-x class="table-scroll">
            <view class="table min-orders">
              <view class="tr th">
                <text>ID</text>
                <text>用户ID</text>
                <text>套餐ID</text>
                <text>金额</text>
                <text>状态</text>
                <text>支付时间</text>
              </view>
              <view class="tr" v-for="item in orders.items" :key="item.id">
                <text>{{ item.id }}</text>
                <text>{{ item.user_id }}</text>
                <text>{{ item.package_id || '-' }}</text>
                <text>{{ item.amount }}</text>
                <text>{{ item.status }}</text>
                <text>{{ formatTime(item.paid_time) }}</text>
              </view>
            </view>
          </scroll-view>
          <view class="pager">
            <button size="mini" :disabled="orders.page <= 1" @click="prevOrders">上一页</button>
            <text>第 {{ orders.page }} 页 / 共 {{ orders.total }} 条</text>
            <button size="mini" :disabled="orders.page * pageSize >= orders.total" @click="nextOrders">下一页</button>
          </view>

          <view class="form-box">
            <view class="section-title">退款审批</view>
            <input class="input" v-model="refundForm.refund_id" type="number" placeholder="退款申请 ID" />
            <picker mode="selector" :range="refundStatusOptions" @change="e => refundForm.status = refundStatusOptions[e.detail.value]">
              <view class="input">审批结果：{{ refundForm.status }}</view>
            </picker>
            <textarea class="textarea" v-model="refundForm.review_note" placeholder="审批备注（可选）"></textarea>
            <button class="primary-btn" size="mini" :loading="refundLoading" @click="submitRefund">提交审批</button>
          </view>
        </view>

        <view v-if="activeModule === 'agents'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">AI 配置</view>
              <view class="panel-desc">维护智能体名称、模型参数和 Prompt</view>
            </view>
            <button size="mini" @click="loadAgents">刷新</button>
          </view>

          <view v-if="agents.loading" class="state">加载中...</view>
          <view v-else-if="!agents.items.length" class="state">暂无智能体配置</view>
          <view v-else class="agent-list">
            <view class="agent-item" v-for="item in agents.items" :key="item.id">
              <view class="item-head">
                <text class="item-title">{{ item.agent_key }}</text>
                <text>{{ item.status }}</text>
              </view>
              <input class="input" v-model="item.agent_name" placeholder="智能体名称" />
              <input class="input" v-model="item.model_name" placeholder="模型名称" />
              <input class="input" v-model="item.temperature" type="digit" placeholder="Temperature" />
              <picker mode="selector" :range="agentStatusOptions" @change="e => item.status = agentStatusOptions[e.detail.value]">
                <view class="input">状态：{{ item.status }}</view>
              </picker>
              <textarea class="textarea large" v-model="item.prompt_template" placeholder="Prompt 模板"></textarea>
              <button class="primary-btn" size="mini" @click="saveAgent(item)">保存配置</button>
            </view>
          </view>
        </view>

        <view v-if="activeModule === 'knowledge'" class="panel">
          <view class="panel-title">知识库维护</view>
          <view class="panel-desc">创建或更新知识库文件记录状态</view>
          <view class="form-box">
            <input class="input" v-model="knowledgeForm.knowledge_id" type="number" placeholder="知识库 ID（更新时填写）" />
            <input class="input" v-model="knowledgeForm.file_name" placeholder="文件名" />
            <input class="input" v-model="knowledgeForm.file_path" placeholder="文件路径（可选）" />
            <picker mode="selector" :range="knowledgeStatusOptions" @change="e => knowledgeForm.status = knowledgeStatusOptions[e.detail.value]">
              <view class="input">状态：{{ knowledgeForm.status }}</view>
            </picker>
            <button class="primary-btn" :loading="knowledgeLoading" @click="saveKnowledge">保存知识库记录</button>
          </view>
        </view>

        <view v-if="activeModule === 'audit'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">审计日志</view>
              <view class="panel-desc">敏感词拦截记录</view>
            </view>
            <button size="mini" @click="loadAuditLogs">刷新</button>
          </view>

          <view v-if="audit.loading" class="state">加载中...</view>
          <view v-else-if="!audit.items.length" class="state">暂无审计日志</view>
          <view v-else class="audit-list">
            <view class="audit-item" v-for="item in audit.items" :key="item.id">
              <view class="item-head">
                <text>#{{ item.id }} 用户 {{ item.user_id || '-' }}</text>
                <text>{{ formatTime(item.created_time) }}</text>
              </view>
              <view class="matched">命中：{{ item.matched_words }}</view>
              <view class="audit-text">{{ item.input_text }}</view>
            </view>
          </view>
          <view class="pager">
            <button size="mini" :disabled="audit.page <= 1" @click="prevAudit">上一页</button>
            <text>第 {{ audit.page }} 页 / 共 {{ audit.total }} 条</text>
            <button size="mini" :disabled="audit.page * pageSize >= audit.total" @click="nextAudit">下一页</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import http from '@/http/http.js';

const modules = [
  { key: 'users', label: '用户管理' },
  { key: 'orders', label: '订单管理' },
  { key: 'agents', label: 'AI 配置' },
  { key: 'knowledge', label: '知识库' },
  { key: 'audit', label: '审计日志' }
];

const activeModule = ref('users');
const pageSize = 20;
const currentUser = uni.getStorageSync('user') || {};

const users = reactive({ items: [], total: 0, page: 1, loading: false });
const orders = reactive({ items: [], total: 0, page: 1, loading: false });
const agents = reactive({ items: [], loading: false });
const audit = reactive({ items: [], total: 0, page: 1, loading: false });

const refundStatusOptions = ['APPROVED', 'REJECTED'];
const agentStatusOptions = ['ACTIVE', 'INACTIVE'];
const knowledgeStatusOptions = ['ACTIVE', 'INACTIVE', 'PROCESSING', 'FAILED'];

const refundLoading = ref(false);
const knowledgeLoading = ref(false);

const refundForm = reactive({
  refund_id: '',
  status: 'APPROVED',
  review_note: ''
});

const knowledgeForm = reactive({
  knowledge_id: '',
  file_name: '',
  file_path: '',
  status: 'ACTIVE'
});

onMounted(async () => {
  if (await ensureAdmin()) {
    loadUsers();
  }
});

const ensureAdmin = async () => {
  const token = uni.getStorageSync('token');
  if (!token) {
    uni.showToast({ title: '无管理员权限或登录已过期', icon: 'none' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 800);
    return false;
  }
  if (String(currentUser.role || '').trim().toUpperCase() === 'ADMIN') return true;

  try {
    await http.checkAdminAccess();
    uni.setStorageSync('user', { ...currentUser, role: 'ADMIN' });
    return true;
  } catch (e) {
    uni.showToast({ title: '无管理员权限或登录已过期', icon: 'none' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 800);
    return false;
  }
};

const switchModule = (key) => {
  activeModule.value = key;
  if (key === 'users' && !users.items.length) loadUsers();
  if (key === 'orders' && !orders.items.length) loadOrders();
  if (key === 'agents' && !agents.items.length) loadAgents();
  if (key === 'audit' && !audit.items.length) loadAuditLogs();
};

const formatTime = (value) => {
  if (!value) return '-';
  return String(value).replace('T', ' ').slice(0, 19);
};

const loadUsers = async () => {
  users.loading = true;
  try {
    const res = await http.getAdminUsers(users.page, pageSize);
    users.items = res.items || [];
    users.total = res.total || 0;
  } catch (e) {
    console.error(e);
  } finally {
    users.loading = false;
  }
};

const toggleBan = async (item) => {
  try {
    await http.toggleUserBan(item.id);
    uni.showToast({ title: '状态已更新' });
    await loadUsers();
  } catch (e) {
    console.error(e);
  }
};

const prevUsers = () => {
  if (users.page <= 1) return;
  users.page -= 1;
  loadUsers();
};

const nextUsers = () => {
  if (users.page * pageSize >= users.total) return;
  users.page += 1;
  loadUsers();
};

const loadOrders = async () => {
  orders.loading = true;
  try {
    const res = await http.getAdminOrders(orders.page, pageSize);
    orders.items = res.items || [];
    orders.total = res.total || 0;
  } catch (e) {
    console.error(e);
  } finally {
    orders.loading = false;
  }
};

const prevOrders = () => {
  if (orders.page <= 1) return;
  orders.page -= 1;
  loadOrders();
};

const nextOrders = () => {
  if (orders.page * pageSize >= orders.total) return;
  orders.page += 1;
  loadOrders();
};

const submitRefund = async () => {
  if (!refundForm.refund_id) {
    return uni.showToast({ title: '请输入退款申请 ID', icon: 'none' });
  }
  refundLoading.value = true;
  try {
    await http.reviewRefund(refundForm.refund_id, {
      status: refundForm.status,
      review_note: refundForm.review_note || null
    });
    uni.showToast({ title: '审批已提交' });
    refundForm.review_note = '';
  } catch (e) {
    console.error(e);
  } finally {
    refundLoading.value = false;
  }
};

const loadAgents = async () => {
  agents.loading = true;
  try {
    agents.items = await http.getAdminAgents();
  } catch (e) {
    console.error(e);
  } finally {
    agents.loading = false;
  }
};

const saveAgent = async (item) => {
  try {
    await http.updateAdminAgent(item.id, {
      agent_name: item.agent_name,
      prompt_template: item.prompt_template,
      model_name: item.model_name,
      temperature: Number(item.temperature),
      status: item.status
    });
    uni.showToast({ title: '配置已保存' });
    await loadAgents();
  } catch (e) {
    console.error(e);
  }
};

const saveKnowledge = async () => {
  if (!knowledgeForm.file_name.trim()) {
    return uni.showToast({ title: '请输入文件名', icon: 'none' });
  }
  knowledgeLoading.value = true;
  const data = {
    file_name: knowledgeForm.file_name,
    file_path: knowledgeForm.file_path || null,
    status: knowledgeForm.status
  };
  if (knowledgeForm.knowledge_id) data.knowledge_id = Number(knowledgeForm.knowledge_id);

  try {
    await http.upsertKnowledge(data);
    uni.showToast({ title: '知识库记录已保存' });
  } catch (e) {
    console.error(e);
  } finally {
    knowledgeLoading.value = false;
  }
};

const loadAuditLogs = async () => {
  audit.loading = true;
  try {
    const res = await http.getSensitiveLogs(audit.page, pageSize);
    audit.items = res.items || [];
    audit.total = res.total || 0;
  } catch (e) {
    console.error(e);
  } finally {
    audit.loading = false;
  }
};

const prevAudit = () => {
  if (audit.page <= 1) return;
  audit.page -= 1;
  loadAuditLogs();
};

const nextAudit = () => {
  if (audit.page * pageSize >= audit.total) return;
  audit.page += 1;
  loadAuditLogs();
};

const goHome = () => uni.reLaunch({ url: '/pages/index/index' });

const logout = () => {
  uni.removeStorageSync('token');
  uni.removeStorageSync('user');
  uni.reLaunch({ url: '/pages/login/login' });
};
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #f4f6f8;
  color: #1f2933;
}
.topbar {
  height: 112rpx;
  padding: 0 32rpx;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title {
  font-size: 36rpx;
  font-weight: 700;
}
.subtitle {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #6b7280;
}
.ghost-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #334155;
}
.top-actions {
  display: flex;
  gap: 12rpx;
  flex-shrink: 0;
}
.logout-btn {
  background: #ffffff;
  border: 1px solid #fecaca;
  color: #b91c1c;
}
.layout {
  display: flex;
  min-height: calc(100vh - 112rpx);
}
.side-nav {
  width: 220rpx;
  background: #111827;
  padding: 24rpx 0;
  flex-shrink: 0;
}
.nav-item {
  padding: 24rpx 28rpx;
  color: #cbd5e1;
  font-size: 26rpx;
}
.nav-item.active {
  color: #ffffff;
  background: #2563eb;
}
.content {
  flex: 1;
  padding: 28rpx;
  min-width: 0;
}
.panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8rpx;
  padding: 28rpx;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}
.panel-title {
  font-size: 32rpx;
  font-weight: 700;
}
.panel-desc {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #64748b;
}
.state {
  padding: 60rpx 0;
  text-align: center;
  color: #64748b;
}
.table-scroll {
  width: 100%;
}
.table {
  display: table;
  width: 100%;
  border-collapse: collapse;
}
.min-users {
  min-width: 980rpx;
}
.min-orders {
  min-width: 980rpx;
}
.tr {
  display: grid;
  grid-template-columns: 90rpx 1.8fr 1.2fr 150rpx 150rpx 160rpx;
  align-items: center;
  min-height: 78rpx;
  border-bottom: 1px solid #eef2f7;
  column-gap: 16rpx;
  font-size: 24rpx;
}
.min-orders .tr {
  grid-template-columns: 90rpx 140rpx 140rpx 140rpx 160rpx 260rpx;
}
.th {
  color: #475569;
  font-weight: 700;
  background: #f8fafc;
}
.success {
  color: #15803d;
}
.danger {
  color: #b91c1c;
}
.form-box {
  margin-top: 28rpx;
  padding-top: 24rpx;
  border-top: 1px solid #e5e7eb;
}
.section-title {
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 18rpx;
}
.input {
  min-height: 74rpx;
  padding: 0 18rpx;
  margin-bottom: 18rpx;
  background: #f8fafc;
  border: 1px solid #dbe3ef;
  border-radius: 8rpx;
  font-size: 26rpx;
  box-sizing: border-box;
}
.textarea {
  width: 100%;
  min-height: 150rpx;
  padding: 18rpx;
  margin-bottom: 18rpx;
  background: #f8fafc;
  border: 1px solid #dbe3ef;
  border-radius: 8rpx;
  font-size: 26rpx;
  box-sizing: border-box;
}
.textarea.large {
  min-height: 260rpx;
}
.primary-btn {
  background: #2563eb;
  color: #ffffff;
}
.agent-list,
.audit-list {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}
.agent-item,
.audit-item {
  border: 1px solid #e5e7eb;
  border-radius: 8rpx;
  padding: 22rpx;
  background: #ffffff;
}
.item-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 16rpx;
  color: #64748b;
  font-size: 24rpx;
}
.item-title {
  color: #111827;
  font-weight: 700;
}
.matched {
  color: #b91c1c;
  font-size: 24rpx;
  margin-bottom: 12rpx;
}
.audit-text {
  font-size: 26rpx;
  line-height: 1.6;
  color: #334155;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18rpx;
  margin-top: 24rpx;
  color: #64748b;
  font-size: 24rpx;
}

@media screen and (max-width: 768px) {
  .layout {
    display: block;
  }
  .side-nav {
    width: auto;
    display: flex;
    overflow-x: auto;
    padding: 0;
  }
  .nav-item {
    white-space: nowrap;
  }
  .content {
    padding: 20rpx;
  }
  .panel-head {
    align-items: flex-start;
    gap: 16rpx;
  }
}
</style>
