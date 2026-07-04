<template>
  <view class="dashboard-layout">
    <!-- 左侧边栏 -->
    <view class="sidebar" :class="{ 'sidebar-mobile-open': isMobileSidebarOpen }">
      <view class="sidebar-header">
        <text class="logo-icon">✨</text>
        <text class="logo-text">启名星</text>
      </view>

      <scroll-view scroll-y class="sidebar-nav">
        <view class="nav-group">
          <!-- 动态判断 currentMenu -->
          <view :class="['nav-item', currentMenu === 'ai_name' ? 'active' : '']" @click="switchMenu('ai_name', '/pages/index/index')">
            <text class="nav-icon">🧭</text> 起名工作台
          </view>
          <view :class="['nav-item', currentMenu === 'community' ? 'active' : '']" @click="switchMenu('community', '/pages/community/index')">
            <text class="nav-icon">💡</text> 灵感广场
          </view>
          <view :class="['nav-item', currentMenu === 'expert' ? 'active' : '']" @click="switchMenu('expert', '/pages/marketplace/index')">
            <text class="nav-icon">🤝</text> 专家服务
          </view>
          <view :class="['nav-item', currentMenu === 'recharge' ? 'active' : '']" @click="switchMenu('recharge', '/pages/recharge/index')">
            <text class="nav-icon">💳</text> 充值中心
          </view>
          <view :class="['nav-item', currentMenu === 'orders' ? 'active' : '']" @click="switchMenu('orders', '/pages/orders/index')">
            <text class="nav-icon">📋</text> 我的订单
          </view>
          <view v-if="isExpert" :class="['nav-item', currentMenu === 'expert_workbench' ? 'active' : '']" @click="switchMenu('expert_workbench', '/pages/expert/workbench')">
            <text class="nav-icon">🧑‍🏫</text> 专家工作台
          </view>
        </view>
      </scroll-view>

      <view class="sidebar-footer">
        <view :class="['nav-item', currentMenu === 'assets' ? 'active' : '']" @click="switchMenu('assets', '/pages/assets/index')">
          <text class="nav-icon">📦</text> 资产中心
        </view>
      </view>
    </view>

    <!-- 移动端侧边栏遮罩 -->
    <view class="sidebar-mask" v-if="isMobileSidebarOpen" @click="toggleMobileSidebar"></view>

    <!-- 右侧主内容区 -->
    <view class="main-container">
      <!-- 顶部导航 -->
      <view class="topbar">
        <!-- 移动端菜单按钮 -->
        <view class="mobile-menu-btn" @click="toggleMobileSidebar">
          <text class="menu-icon">☰</text>
        </view>

        <!-- 搜索框 (可根据需求接入真实搜索逻辑) -->
        <!-- 右上角：真实的账号操作区 -->
        <view class="topbar-actions" v-if="token">
          <text v-if="isAdmin" class="action-text" @click="goAdmin">后台管理</text>
          <text class="action-text text-danger" @click="logout">退出</text>
          <view class="action-icon" @click="switchMenu('profile', '/pages/profile/index')">
            <view class="avatar">{{ (user.username || user.email || 'U')[0].toUpperCase() }}</view>
          </view>
        </view>
        <view class="topbar-actions" v-else>
          <text class="action-text login-text" @click="navTo('/pages/login/login')">登录 / 注册</text>
        </view>
      </view>

      <!-- 页面插槽内容 -->
      <scroll-view scroll-y class="content-scroll">
        <view class="page-content">
          <slot></slot>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

// 接收父页面传进来的当前菜单标识
const props = defineProps({
  currentMenu: {
    type: String,
    default: 'ai_name'
  }
});

// 用户状态逻辑
const token = ref(uni.getStorageSync('token'));
const user = ref(uni.getStorageSync('user') || {});
const isAdmin = computed(() => String(user.value.role || '').trim().toUpperCase() === 'ADMIN');
const isExpert = computed(() => String(user.value.expert_status || '').trim().toUpperCase() === 'APPROVED');
const isMobileSidebarOpen = ref(false);

const toggleMobileSidebar = () => {
  isMobileSidebarOpen.value = !isMobileSidebarOpen.value;
};

const navTo = (url) => {
  uni.navigateTo({ url });
};

// 左侧菜单切换逻辑：平滑跳转，避免白屏
const switchMenu = (menuKey, url) => {
  if (props.currentMenu === menuKey) return; // 点自己不跳转
  uni.redirectTo({ url });
};

const goAdmin = () => uni.reLaunch({ url: '/pages/admin/index' });
const logout = () => {
  uni.removeStorageSync('token');
  uni.removeStorageSync('user');
  uni.reLaunch({ url: '/pages/login/login' });
};

const refreshUser = async () => {
  token.value = uni.getStorageSync('token');
  user.value = uni.getStorageSync('user') || {};
  if (!token.value) return;
  try {
    const profile = await http.getMyProfile();
    user.value = { ...user.value, username: profile.username, email: profile.email, role: profile.role, expert_status: profile.expert_status };
    uni.setStorageSync('user', user.value);
  } catch (e) {}
};

onShow(refreshUser);
</script>

<style scoped lang="scss">
@import "@/uni.scss";
.dashboard-layout {
  display: flex;
  height: 100vh;
  height: 100dvh;
  width: 100vw;
  background-color: $bg-app;
  overflow: hidden;
  box-sizing: border-box;
}

/* Sidebar Styles */
.sidebar {
  width: 260px;
  flex: 0 0 260px;
  box-sizing: border-box;
  background-color: #FFFFFF;
  border-right: 1px solid #F3F4F6;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 100;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  box-sizing: border-box;
}
.logo-icon {
  font-size: 24px;
  margin-right: 12px;
}
.logo-text {
  font-size: 20px;
  font-weight: 800;
  color: $text-main;
  letter-spacing: -0.5px;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  padding: 12px 12px;
  overflow: hidden;
}
.nav-item {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 12px 16px;
  border-radius: $radius-base;
  color: $text-secondary;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.nav-item:hover {
  background-color: #F3F4F6;
  color: $text-main;
}
.nav-item.active {
  background-color: $brand-secondary;
  color: $brand-primary;
  font-weight: 600;
}
.nav-icon {
  margin-right: 12px;
  font-size: 18px;
  flex-shrink: 0;
}

.sidebar-footer {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 12px;
  border-top: 1px solid #F3F4F6;
  flex-shrink: 0;
  overflow: hidden;
}

/* Main Container */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

/* Topbar */
.topbar {
  height: 56px;
  background-color: $bg-app;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  box-sizing: border-box;
  flex-shrink: 0;
  border-bottom: 1px solid #F3F4F6;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-left: auto;
}

.action-text {
  font-size: 14px;
  color: $text-secondary;
  cursor: pointer;
  transition: color 0.2s;
  font-weight: 500;
}
.action-text:hover { color: $text-main; }
.text-danger:hover { color: #DC2626; }
.login-text { color: $brand-primary; font-weight: 600; }

.action-icon {
  font-size: 20px;
  color: $text-secondary;
  cursor: pointer;
}
.avatar {
  width: 36px;
  height: 36px;
  background-color: $brand-primary;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #FFFFFF;
  font-weight: bold;
  font-size: 16px;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.2);
}

/* Content Area */
.content-scroll {
  flex: 1;
  min-height: 0;
  height: calc(100vh - 56px);
  height: calc(100dvh - 56px);
  overflow: hidden;
  box-sizing: border-box;
}
.page-content {
  width: 100%;
  box-sizing: border-box;
  padding: 28px 32px 56px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Mobile Adjustments */
.mobile-menu-btn {
  display: none;
  font-size: 24px;
  color: $text-main;
  cursor: pointer;
}
.sidebar-mask {
  display: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    transform: translateX(-100%);
  }
  .sidebar.sidebar-mobile-open {
    transform: translateX(0);
  }
  .sidebar-mask {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 90;
  }
  .topbar {
    padding: 0 20px;
    height: 52px;
  }
  .mobile-menu-btn {
    display: block;
  }
  .page-content {
    padding: 18px 16px 40px;
  }
  .content-scroll {
    height: calc(100vh - 52px);
    height: calc(100dvh - 52px);
  }
}
</style>
