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
              <view class="panel-desc">搜索用户并管理账号、VIP 与专家身份</view>
            </view>
            <button size="mini" @click="loadUsers">刷新</button>
          </view>

          <view class="user-search">
            <input class="search-input" :value="userKeyword" placeholder="搜索用户名或邮箱" @input="userKeyword = $event.detail.value" @confirm="searchUsers" />
            <button class="search-btn" @click="searchUsers">搜索</button>
          </view>

          <view v-if="users.loading" class="state">加载中...</view>
          <view v-else-if="!users.items.length" class="state">暂无用户数据</view>
          <view v-else class="user-grid">
            <view class="user-card" v-for="item in users.items" :key="item.id">
              <view class="user-card-head">
                <view><view class="user-name">{{ item.username }}</view><view class="user-email">{{ item.email }}</view></view>
                <text :class="['status-tag', item.is_deleted || item.is_banned ? 'blocked' : 'normal']">{{ item.is_deleted ? '已删除' : item.is_banned ? '已封禁' : '正常' }}</text>
              </view>
              <view class="user-meta">ID {{ item.id }} · {{ roleText(item.role) }} · 注册于 {{ formatTime(item.created_time) }}</view>
              <view class="user-badges"><text v-if="item.is_vip" class="vip-tag">VIP 至 {{ formatTime(item.vip_expires_at) }}</text><text v-if="item.expert_status" class="expert-tag">专家：{{ expertStatusText(item.expert_status) }}</text></view>
              <view class="user-actions">
                <button size="mini" :disabled="item.is_deleted" @click="toggleBan(item)">{{ item.is_banned ? '解封' : '封禁' }}</button>
                <button size="mini" :disabled="item.is_deleted" @click="openResetPassword(item)">重置密码</button>
                <button size="mini" :disabled="item.is_deleted" @click="giftVip(item)">赠送月度 VIP</button>
                <button size="mini" class="delete-btn" :disabled="item.is_deleted" @click="deleteUser(item)">删除</button>
              </view>
            </view>
          </view>
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
              <view class="panel-desc">查看订单状态，并在需要处理的订单行内完成退款审批</view>
            </view>
            <button size="mini" @click="loadOrders">刷新</button>
          </view>

          <view class="order-filters">
            <input class="input filter-input" v-model="orderFilters.keyword" placeholder="搜索订单ID/用户/交易号" @confirm="searchOrders" />
            <picker mode="selector" :range="orderStatusFilterLabels" @change="changeOrderStatus">
              <view class="input filter-picker">财务状态：{{ orderStatusFilterLabel }}</view>
            </picker>
            <picker mode="selector" :range="orderTypeFilterLabels" @change="changeOrderType">
              <view class="input filter-picker">订单类型：{{ orderTypeFilterLabel }}</view>
            </picker>
            <picker mode="selector" :range="paymentProviderFilterLabels" @change="changePaymentProvider">
              <view class="input filter-picker">支付渠道：{{ paymentProviderFilterLabel }}</view>
            </picker>
            <button class="search-btn" @click="searchOrders">筛选</button>
          </view>

          <view v-if="orders.loading" class="state">加载中...</view>
          <view v-else-if="!orders.items.length" class="state">暂无订单数据</view>
          <scroll-view v-else scroll-x class="table-scroll">
            <view class="table min-orders">
              <view class="tr th">
                <text>ID</text>
                <text>用户</text>
                <text>类型/渠道</text>
                <text>金额</text>
                <text>财务状态</text>
                <text>服务状态</text>
                <text>交易号</text>
                <text>退款</text>
                <text>支付时间</text>
                <text>操作</text>
              </view>
              <view class="tr" v-for="item in orders.items" :key="item.id">
                <text>{{ item.id }}</text>
                <text>{{ item.user_id }}</text>
                <text>{{ orderTypeText(item.order_type) }} / {{ paymentProviderText(item.payment_provider) }}</text>
                <text>{{ item.amount }}</text>
                <text>{{ financeStatusText(item.status) }}</text>
                <text>{{ item.service_status ? serviceStatusText(item.service_status) : '-' }}</text>
                <text class="mono">{{ item.out_trade_no || item.provider_trade_no || '-' }}</text>
                <text>{{ item.refund_status ? `#${item.refund_id} ${refundStatusText(item.refund_status)}` : '-' }}</text>
                <text>{{ formatTime(item.paid_time) }}</text>
                <view class="row-actions">
                  <button v-if="canReviewRefund(item)" size="mini" class="primary-btn" :loading="refundLoading" @click="quickReviewRefund(item, 'APPROVED')">通过退款</button>
                  <button v-if="canReviewRefund(item)" size="mini" class="danger" :loading="refundLoading" @click="quickReviewRefund(item, 'REJECTED')">拒绝退款</button>
                  <text v-if="!canReviewRefund(item)" class="muted">-</text>
                </view>
              </view>
            </view>
          </scroll-view>
          <view class="pager">
            <button size="mini" :disabled="orders.page <= 1" @click="prevOrders">上一页</button>
            <text>第 {{ orders.page }} 页 / 共 {{ orders.total }} 条</text>
            <button size="mini" :disabled="orders.page * pageSize >= orders.total" @click="nextOrders">下一页</button>
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
                <text>{{ commonStatusText(item.status) }}</text>
              </view>
              <input class="input" v-model="item.agent_name" placeholder="智能体名称" />
              <input class="input" v-model="item.model_name" placeholder="模型名称" />
              <input class="input" v-model="item.temperature" type="digit" placeholder="Temperature" />
              <picker mode="selector" :range="agentStatusLabels" @change="e => item.status = agentStatusOptions[e.detail.value]">
                <view class="input">状态：{{ commonStatusText(item.status) }}</view>
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
            <picker mode="selector" :range="knowledgeStatusLabels" @change="e => knowledgeForm.status = knowledgeStatusOptions[e.detail.value]">
              <view class="input">状态：{{ commonStatusText(knowledgeForm.status) }}</view>
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

        <view v-if="activeModule === 'expert_reviews'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">专家审核</view>
              <view class="panel-desc">审核专家申请，已通过的专家只能停用，不能再拒绝</view>
            </view>
            <button size="mini" @click="loadMarketGovernance">刷新</button>
          </view>

          <view v-if="!marketExperts.length" class="state">暂无专家申请</view>
          <view v-for="item in marketExperts" :key="item.id" class="market-card clickable-card" @click="openExpertDetail(item)">
            <view class="item-head">
              <text class="item-title">{{ item.display_name }}</text>
              <text :class="['market-status', item.status]">{{ expertStatusText(item.status) }}</text>
            </view>
            <view class="copy">{{ expertTypeText(item.expert_type) }} · {{ item.years_experience }} 年经验</view>
            <view v-if="item.review_note" class="review-note">审核备注：{{ item.review_note }}</view>
            <view class="market-actions">
              <button size="mini" :disabled="item.status === 'APPROVED'" @click.stop="reviewExpert(item, 'APPROVED')">通过</button>
              <button size="mini" class="danger" :disabled="item.status === 'APPROVED' || item.status === 'REJECTED'" @click.stop="reviewExpert(item, 'REJECTED')">拒绝</button>
              <button size="mini" class="outline" :disabled="item.status === 'SUSPENDED'" @click.stop="reviewExpert(item, 'SUSPENDED')">停用</button>
            </view>
          </view>
        </view>

        <view v-if="activeModule === 'service_packages'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">服务套餐</view>
              <view class="panel-desc">新增、上下架或删除未被订单引用的专家服务套餐</view>
            </view>
            <view class="panel-actions">
              <button size="mini" class="primary-btn" @click="openPackageForm">新增套餐</button>
              <button size="mini" @click="loadMarketGovernance">刷新</button>
            </view>
          </view>

          <view v-if="!marketPackages.length" class="state">暂无服务套餐</view>
          <view v-for="item in marketPackages" :key="item.id" class="market-card">
            <view class="item-head"><text class="item-title">{{ item.name }}</text><text>¥{{ item.price }}</text></view>
            <view class="copy">{{ expertTypeText(item.expert_type) }} · {{ item.delivery_days }} 天 · {{ packageStatusText(item.status) }}</view>
            <view class="market-actions">
              <button size="mini" class="outline" @click="togglePackage(item)">{{ item.status === 'ACTIVE' ? '下架' : '上架' }}</button>
              <button size="mini" class="delete-btn" @click="deletePackage(item)">删除</button>
            </view>
          </view>
        </view>

        <view v-if="activeModule === 'community_reports'" class="panel">
          <view class="panel-head">
            <view>
              <view class="panel-title">社区举报</view>
              <view class="panel-desc">处理社区内容举报</view>
            </view>
            <button size="mini" @click="loadMarketGovernance">刷新</button>
          </view>

          <view v-if="!communityReports.length" class="state">暂无待处理举报</view>
          <view v-for="item in communityReports" :key="item.id" class="market-card">
            <view class="item-head"><text>{{ item.target_type }} #{{ item.target_id }}</text><text>{{ item.reason }}</text></view>
            <view class="copy">{{ item.detail }}</view>
            <view class="market-actions">
              <button size="mini" class="danger" @click="moderateReport(item.id, 'HIDE')">隐藏内容</button>
              <button size="mini" class="outline" @click="moderateReport(item.id, 'DISMISS')">驳回举报</button>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="resetDialog" class="dialog-overlay" @click="closeResetPassword">
      <view class="reset-dialog" @click.stop>
        <view class="dialog-title">重置 {{ resetTarget?.username }} 的密码</view>
        <input class="dialog-input" password :value="newPassword" placeholder="输入新密码（至少 3 位）" @input="newPassword = $event.detail.value" />
        <view class="dialog-actions"><button @click="closeResetPassword">取消</button><button class="primary-btn" :loading="resetLoading" @click="submitResetPassword">确认重置</button></view>
      </view>
    </view>

    <view v-if="expertDetailDialog" class="dialog-overlay" @click="closeExpertDetail">
      <view class="detail-dialog" @click.stop>
        <view class="dialog-title">{{ expertDetail?.display_name }}</view>
        <view class="detail-meta">{{ expertTypeText(expertDetail?.expert_type) }} · {{ expertDetail?.years_experience }} 年经验 · {{ expertStatusText(expertDetail?.status) }}</view>
        <view class="info-block"><text>个人简介</text><view>{{ expertDetail?.bio }}</view></view>
        <view class="info-block"><text>资历证明</text><view>{{ expertDetail?.credentials }}</view></view>
        <view v-if="expertDetail?.review_note" class="review-note">审核备注：{{ expertDetail.review_note }}</view>
        <view class="dialog-actions"><button @click="closeExpertDetail">关闭</button></view>
      </view>
    </view>

    <view v-if="packageFormDialog" class="dialog-overlay" @click="closePackageForm">
      <view class="detail-dialog" @click.stop>
        <view class="dialog-title">新增服务套餐</view>
        <view class="field-label">套餐名称</view>
        <input class="input" :value="pkg.name" placeholder="例如：品牌命名基础精批" @input="updatePackageField('name', $event.detail.value)" />
        <view class="field-label">服务专家类型</view>
        <picker :range="typeLabels" @change="changeExpertType">
          <view class="input picker-value">{{ expertTypeLabel }}</view>
        </picker>
        <view class="form-grid">
          <view>
            <view class="field-label">价格（元）</view>
            <input class="input" type="number" :value="pkg.price" placeholder="199" @input="updatePackageField('price', $event.detail.value)" />
          </view>
          <view>
            <view class="field-label">交付天数</view>
            <input class="input" type="number" :value="pkg.delivery_days" placeholder="3" @input="updatePackageField('delivery_days', $event.detail.value)" />
          </view>
        </view>
        <view class="field-label">服务说明</view>
        <textarea class="textarea" :value="pkg.description" placeholder="说明报告内容和服务边界" @input="updatePackageField('description', $event.detail.value)" />
        <view class="dialog-actions"><button @click="closePackageForm">取消</button><button class="primary-btn" :loading="packageSaving" @click="createPackage">新增套餐</button></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import http from '@/http/http.js';

const modules = [
  { key: 'users', label: '用户管理' },
  { key: 'orders', label: '订单管理' },
  { key: 'agents', label: 'AI 配置' },
  { key: 'knowledge', label: '知识库' },
  { key: 'audit', label: '审计日志' },
  { key: 'expert_reviews', label: '专家审核' },
  { key: 'service_packages', label: '服务套餐' },
  { key: 'community_reports', label: '社区举报' }
];

const activeModule = ref('users');
const pageSize = 20;
const currentUser = uni.getStorageSync('user') || {};
const userKeyword = ref('');
const resetDialog = ref(false);
const resetTarget = ref(null);
const newPassword = ref('');
const resetLoading = ref(false);

const users = reactive({ items: [], total: 0, page: 1, loading: false });
const orders = reactive({ items: [], total: 0, page: 1, loading: false });
const orderFilters = reactive({ keyword: '', status: '', order_type: '', payment_provider: '' });
const agents = reactive({ items: [], loading: false });
const audit = reactive({ items: [], total: 0, page: 1, loading: false });
const marketExperts = ref([]);
const marketPackages = ref([]);
const communityReports = ref([]);
const packageSaving = ref(false);
const expertDetailDialog = ref(false);
const expertDetail = ref(null);
const packageFormDialog = ref(false);

const orderStatusFilterOptions = ['', 'PENDING', 'PAID', 'CANCELLED', 'REFUNDED'];
const orderStatusFilterLabels = ['全部状态', '待支付', '已支付', '已取消', '已退款'];
const orderTypeFilterOptions = ['', 'MEMBERSHIP', 'EXPERT_SERVICE'];
const orderTypeFilterLabels = ['全部类型', '会员/额度', '专家服务'];
const paymentProviderFilterOptions = ['', 'MOCK', 'ALIPAY_SANDBOX'];
const paymentProviderFilterLabels = ['全部渠道', '模拟支付', '支付宝沙箱'];
const agentStatusOptions = ['ACTIVE', 'INACTIVE'];
const agentStatusLabels = ['启用', '停用'];
const knowledgeStatusOptions = ['ACTIVE', 'INACTIVE', 'PROCESSING', 'FAILED'];
const knowledgeStatusLabels = ['启用', '停用', '处理中', '失败'];
const expertTypes = ['CULTURE_MASTER', 'BRAND_CONSULTANT'];
const typeLabels = ['国学命名', '品牌咨询'];

const refundLoading = ref(false);
const knowledgeLoading = ref(false);

const knowledgeForm = reactive({
  knowledge_id: '',
  file_name: '',
  file_path: '',
  status: 'ACTIVE'
});
const pkg = reactive({ name: '', expert_type: 'CULTURE_MASTER', price: '', delivery_days: '3', description: '', status: 'ACTIVE' });
const expertTypeLabel = computed(() => typeLabels[expertTypes.indexOf(pkg.expert_type)] || typeLabels[0]);
const expertTypeText = value => typeLabels[expertTypes.indexOf(value)] || value;
const orderStatusFilterLabel = computed(() => orderStatusFilterLabels[orderStatusFilterOptions.indexOf(orderFilters.status)] || orderStatusFilterLabels[0]);
const orderTypeFilterLabel = computed(() => orderTypeFilterLabels[orderTypeFilterOptions.indexOf(orderFilters.order_type)] || orderTypeFilterLabels[0]);
const paymentProviderFilterLabel = computed(() => paymentProviderFilterLabels[paymentProviderFilterOptions.indexOf(orderFilters.payment_provider)] || paymentProviderFilterLabels[0]);
const statusLabels = {
  ACTIVE: '启用',
  INACTIVE: '停用',
  PENDING: '待处理',
  PROCESSING: '处理中',
  FAILED: '失败',
  SUCCESS: '成功',
  APPROVED: '已通过',
  REJECTED: '已拒绝',
  SUSPENDED: '已停用',
  PENDING_PAYMENT: '待支付',
  WAITING_ACCEPT: '待接单',
  REFUND_PENDING: '退款待审',
  IN_PROGRESS: '进行中',
  DELIVERED: '已交付',
  COMPLETED: '已完成',
  ADMIN: '管理员',
  C_END: '普通用户',
  USER: '普通用户'
};
const commonStatusText = value => statusLabels[value] || value || '-';
const financeStatusText = value => ({
  PENDING: '待支付',
  PAID: '已支付',
  CANCELLED: '已取消',
  REFUNDED: '已退款'
}[value] || commonStatusText(value));
const refundStatusText = commonStatusText;
const serviceStatusText = commonStatusText;
const orderTypeText = value => ({
  MEMBERSHIP: '会员/额度',
  EXPERT_SERVICE: '专家服务'
}[value] || value || '-');
const paymentProviderText = value => ({
  MOCK: '模拟',
  ALIPAY_SANDBOX: '支付宝'
}[value] || value || '-');
const packageStatusText = commonStatusText;
const expertStatusText = value => ({
  PENDING: '待审核',
  APPROVED: '已通过',
  REJECTED: '已拒绝',
  SUSPENDED: '已停用'
}[value] || commonStatusText(value));
const roleText = commonStatusText;

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
  if (['expert_reviews', 'service_packages', 'community_reports'].includes(key)) loadMarketGovernance();
};

const formatTime = (value) => {
  if (!value) return '-';
  return String(value).replace('T', ' ').slice(0, 19);
};

const loadUsers = async () => {
  users.loading = true;
  try {
    const res = await http.getAdminUsers(users.page, pageSize, userKeyword.value.trim());
    users.items = res.items || [];
    users.total = res.total || 0;
  } catch (e) {
    console.error(e);
  } finally {
    users.loading = false;
  }
};

const searchUsers = () => {
  users.page = 1;
  loadUsers();
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

const openResetPassword = item => {
  resetTarget.value = item;
  newPassword.value = '';
  resetDialog.value = true;
};
const closeResetPassword = () => {
  resetDialog.value = false;
  resetTarget.value = null;
  newPassword.value = '';
};
const submitResetPassword = async () => {
  if (newPassword.value.length < 3) return uni.showToast({ title: '密码至少 3 位', icon: 'none' });
  resetLoading.value = true;
  try {
    await http.resetAdminUserPassword(resetTarget.value.id, newPassword.value);
    closeResetPassword();
    uni.showToast({ title: '密码已重置' });
  } finally {
    resetLoading.value = false;
  }
};
const giftVip = item => uni.showModal({ title: '赠送月度 VIP', content: `为 ${item.username} 增加 30 天 VIP？`, success: async result => {
  if (!result.confirm) return;
  await http.giftAdminUserVip(item.id);
  uni.showToast({ title: 'VIP 已赠送' });
  await loadUsers();
}});
const deleteUser = item => uni.showModal({ title: '删除用户', content: `将软删除 ${item.username}，其历史数据会保留。`, confirmColor: '#dc2626', success: async result => {
  if (!result.confirm) return;
  await http.deleteAdminUser(item.id);
  uni.showToast({ title: '用户已删除' });
  await loadUsers();
}});

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
    const res = await http.getAdminOrders(orders.page, pageSize, orderFilters);
    orders.items = res.items || [];
    orders.total = res.total || 0;
  } catch (e) {
    console.error(e);
  } finally {
    orders.loading = false;
  }
};

const searchOrders = () => {
  orders.page = 1;
  loadOrders();
};

const changeOrderStatus = event => {
  orderFilters.status = orderStatusFilterOptions[Number(event.detail.value)] || '';
  searchOrders();
};

const changeOrderType = event => {
  orderFilters.order_type = orderTypeFilterOptions[Number(event.detail.value)] || '';
  searchOrders();
};

const changePaymentProvider = event => {
  orderFilters.payment_provider = paymentProviderFilterOptions[Number(event.detail.value)] || '';
  searchOrders();
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

const reviewRefundById = async (refundId, status, note = null) => {
  refundLoading.value = true;
  try {
    await http.reviewRefund(refundId, { status, review_note: note });
    uni.showToast({ title: '审批已提交' });
    await loadOrders();
  } finally {
    refundLoading.value = false;
  }
};

const canReviewRefund = item => item.refund_id && item.refund_status === 'PENDING';

const quickReviewRefund = async (item, status) => {
  if (!canReviewRefund(item)) return;
  await reviewRefundById(item.refund_id, status, status === 'APPROVED' ? '同意退款' : '拒绝退款');
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

const loadMarketGovernance = async () => {
  try {
    const [expertResult, packageResult, reportResult] = await Promise.all([
      http.getAdminExperts(),
      http.getAdminServicePackages(),
      http.getAdminCommunityReports()
    ]);
    marketExperts.value = expertResult.items || [];
    marketPackages.value = packageResult || [];
    communityReports.value = reportResult.items || [];
  } catch (e) {
    console.error(e);
  }
};

const reviewExpert = async (item, status) => {
  if (item.status === status) return;
  const title = status === 'APPROVED' ? '通过专家申请' : (status === 'REJECTED' ? '拒绝专家申请' : '停用专家身份');
  uni.showModal({
    title,
    content: status === 'APPROVED' ? `确认通过「${item.display_name}」的专家申请？` : '',
    editable: status !== 'APPROVED',
    placeholderText: status === 'REJECTED' ? '填写拒绝原因' : '填写停用原因',
    success: async result => {
      if (!result.confirm) return;
      if (status !== 'APPROVED' && !String(result.content || '').trim()) return uni.showToast({ title: '请填写审核原因', icon: 'none' });
      await http.reviewAdminExpert(item.id, { status, review_note: String(result.content || '').trim() || null });
      await loadMarketGovernance();
      await loadUsers();
    }
  });
};

const openExpertDetail = item => {
  expertDetail.value = item;
  expertDetailDialog.value = true;
};
const closeExpertDetail = () => {
  expertDetailDialog.value = false;
  expertDetail.value = null;
};

const resetPackageForm = () => Object.assign(pkg, { name: '', expert_type: 'CULTURE_MASTER', price: '', delivery_days: '3', description: '', status: 'ACTIVE' });
const openPackageForm = () => {
  resetPackageForm();
  packageFormDialog.value = true;
};
const closePackageForm = () => {
  packageFormDialog.value = false;
};
const updatePackageField = (field, value) => { pkg[field] = value; };
const changeExpertType = event => { pkg.expert_type = expertTypes[Number(event.detail.value)]; };
const createPackage = async () => {
  const price = Number(pkg.price);
  const deliveryDays = Number(pkg.delivery_days);
  if (!pkg.name.trim() || !pkg.description.trim() || !Number.isFinite(price) || price <= 0 || !Number.isInteger(deliveryDays) || deliveryDays <= 0) {
    return uni.showToast({ title: '请完整填写套餐名称、价格、天数和说明', icon: 'none' });
  }
  packageSaving.value = true;
  try {
    await http.createAdminServicePackage({ ...pkg, price, delivery_days: deliveryDays });
    resetPackageForm();
    closePackageForm();
    marketPackages.value = await http.getAdminServicePackages();
    uni.showToast({ title: '套餐已添加', icon: 'success' });
  } finally {
    packageSaving.value = false;
  }
};
const togglePackage = async item => {
  await http.updateAdminServicePackage(item.id, { status: item.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' });
  marketPackages.value = await http.getAdminServicePackages();
};
const deletePackage = item => uni.showModal({
  title: '删除服务套餐',
  content: `确认删除「${item.name}」？已有订单引用的套餐不能删除，只能下架。`,
  confirmColor: '#dc2626',
  success: async result => {
    if (!result.confirm) return;
    await http.deleteAdminServicePackage(item.id);
    uni.showToast({ title: '套餐已删除' });
    marketPackages.value = await http.getAdminServicePackages();
  }
});
const moderateReport = async (id, action) => {
  await http.moderateAdminReport(id, { action, resolution: action === 'HIDE' ? '内容已隐藏' : '举报不成立' });
  communityReports.value = (await http.getAdminCommunityReports()).items || [];
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
.panel-actions {
  display: flex;
  gap: 12rpx;
  flex-shrink: 0;
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
.user-search{display:flex;gap:14rpx;margin-bottom:24rpx}.search-input{height:78rpx;flex:1;min-width:0;padding:0 20rpx;background:#f8fafc;border:1px solid #dbe3ef;border-radius:8rpx;box-sizing:border-box}.search-btn{width:150rpx;background:#2563eb;color:#fff;border-radius:8rpx}.user-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18rpx}.user-card{border:1px solid #e5e7eb;border-radius:8rpx;padding:22rpx}.user-card-head{display:flex;justify-content:space-between;gap:18rpx}.user-name{font-size:30rpx;font-weight:700}.user-email,.user-meta{color:#64748b;font-size:23rpx;margin-top:6rpx}.status-tag,.vip-tag,.expert-tag{font-size:21rpx;padding:5rpx 12rpx;border-radius:20rpx;white-space:nowrap}.status-tag.normal{background:#ecfdf5;color:#15803d}.status-tag.blocked{background:#fff1f2;color:#be123c}.user-badges{display:flex;gap:10rpx;flex-wrap:wrap;margin-top:16rpx}.vip-tag{background:#fff7ed;color:#c2410c}.expert-tag{background:#ecfeff;color:#0f766e}.user-actions{display:flex;gap:10rpx;flex-wrap:wrap;margin-top:20rpx}.user-actions button{margin:0}.delete-btn{color:#dc2626!important}.dialog-overlay{position:fixed;inset:0;background:rgba(15,23,42,.5);display:flex;align-items:center;justify-content:center;padding:30rpx;z-index:100}.reset-dialog{width:min(620rpx,100%);background:#fff;border-radius:8rpx;padding:28rpx;box-sizing:border-box}.dialog-title{font-size:30rpx;font-weight:700}.dialog-input{height:82rpx;border:1px solid #cbd5e1;background:#f8fafc;border-radius:8rpx;padding:0 18rpx;margin:24rpx 0;box-sizing:border-box}.dialog-actions{display:flex;justify-content:flex-end;gap:12rpx}.dialog-actions button{margin:0}
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
  min-width: 1900rpx;
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
  grid-template-columns: 90rpx 120rpx 240rpx 140rpx 160rpx 170rpx 320rpx 180rpx 240rpx 240rpx;
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
.order-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  align-items: stretch;
  margin-bottom: 22rpx;
}
.filter-input {
  width: 300rpx;
  margin-bottom: 0;
}
.filter-picker {
  min-width: 230rpx;
  margin-bottom: 0;
  display: flex;
  align-items: center;
}
.mono {
  font-family: Consolas, Monaco, monospace;
  word-break: break-all;
}
.row-actions {
  display: flex;
  gap: 8rpx;
  flex-wrap: wrap;
  align-items: center;
}
.row-actions button {
  margin: 0;
  min-width: 96rpx;
  padding: 0 12rpx;
}
.muted {
  color: #94a3b8;
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
.market-card {
  border: 1px solid #e5e7eb;
  border-radius: 8rpx;
  padding: 20rpx 22rpx;
  margin-bottom: 18rpx;
  background: #ffffff;
}
.clickable-card {
  cursor: pointer;
}
.clickable-card:hover {
  border-color: #bfdbfe;
  background: #f8fbff;
}
.copy {
  color: #64748b;
  font-size: 24rpx;
  margin: 12rpx 0;
}
.info-block {
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8rpx;
  padding: 16rpx;
  margin-top: 12rpx;
}
.info-block text {
  display: block;
  color: #64748b;
  font-size: 23rpx;
  margin-bottom: 8rpx;
}
.info-block view {
  font-size: 25rpx;
  line-height: 1.6;
}
.review-note {
  background: #fff7ed;
  color: #c2410c;
  border-radius: 8rpx;
  padding: 14rpx;
  margin-top: 12rpx;
  font-size: 24rpx;
}
.market-actions {
  display: flex;
  gap: 10rpx;
  flex-wrap: wrap;
  margin-top: 16rpx;
}
.market-actions button {
  margin: 0;
}
.market-status {
  font-size: 22rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #eef2ff;
  color: #3730a3;
}
.market-status.APPROVED {
  background: #ecfdf5;
  color: #15803d;
}
.market-status.REJECTED,
.market-status.SUSPENDED {
  background: #fff1f2;
  color: #be123c;
}
.field-label {
  font-size: 24rpx;
  color: #475569;
  margin: 16rpx 0 8rpx;
}
.picker-value {
  display: flex;
  align-items: center;
}
.package-form {
  margin-top: 0;
  margin-bottom: 24rpx;
}
.detail-dialog {
  width: min(760rpx, 100%);
  max-height: 86vh;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 8rpx;
  padding: 28rpx;
  box-sizing: border-box;
}
.detail-meta {
  color: #64748b;
  font-size: 24rpx;
  margin-top: 10rpx;
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
  .user-grid{grid-template-columns:1fr}.user-search{align-items:stretch}.search-btn{width:130rpx}
}
</style>
