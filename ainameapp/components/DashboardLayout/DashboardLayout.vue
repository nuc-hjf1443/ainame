<template>
  <view class="app-shell">
    <view class="top-nav">
      <view class="brand" @click="switchMenu('home', '/pages/home/index')">
        <view class="seal">启名</view>
        <view>
          <view class="brand-name">AI起名</view>
          <view class="brand-sub">国学与品牌智能体</view>
        </view>
      </view>

      <view class="desktop-nav">
        <view
          v-for="item in menus"
          :key="item.key"
          :class="['nav-link', currentMenu === item.key ? 'active' : '']"
          @click="switchMenu(item.key, item.url)"
        >
          {{ item.label }}
        </view>
      </view>

      <view class="top-actions">
        <button class="member-btn" @click="switchMenu('recharge', '/pages/recharge/index')">开通会员</button>
        <view class="bell">⌕</view>
        <view v-if="token" class="profile" @click="switchMenu('profile', '/pages/profile/index')">
          <view class="avatar">{{ avatarText }}</view>
          <view class="profile-copy">
            <text>{{ user.username || user.email || '用户' }}</text>
            <text>{{ versionText }}</text>
          </view>
          <text class="chevron">⌄</text>
        </view>
        <button v-else class="login-btn" @click="navTo('/pages/login/login')">登录</button>
      </view>
    </view>

    <scroll-view scroll-y class="content-scroll">
      <view class="ink-bg">
        <slot></slot>
      </view>
    </scroll-view>

    <view class="mobile-tabbar">
      <view
        v-for="item in mobileMenus"
        :key="item.key"
        :class="['mobile-tab', currentMenu === item.key ? 'active' : '']"
        @click="switchMenu(item.key, item.url)"
      >
        <text class="tab-icon">{{ item.icon }}</text>
        <text>{{ item.label }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const props = defineProps({
  currentMenu: { type: String, default: 'home' }
});

const token = ref(uni.getStorageSync('token'));
const user = ref(uni.getStorageSync('user') || {});
const isAdmin = computed(() => String(user.value.role || '').toUpperCase() === 'ADMIN');
const isExpert = computed(() => String(user.value.expert_status || '').toUpperCase() === 'APPROVED');
const avatarText = computed(() => String(user.value.username || user.value.email || 'U').slice(0, 1).toUpperCase());
const versionText = computed(() => isAdmin.value ? '管理员' : isExpert.value ? '专家版' : '企业版');

const menus = [
  { key: 'home', label: '首页', url: '/pages/home/index' },
  { key: 'naming', label: 'AI起名', url: '/pages/naming/index' },
  { key: 'brand', label: '品牌工作台', url: '/pages/brand-kit/index' },
  { key: 'community', label: '灵感社区', url: '/pages/community/index' },
  { key: 'expert', label: '专家服务', url: '/pages/marketplace/index' },
  { key: 'assets', label: '资产中心', url: '/pages/assets/index' }
];
const mobileMenus = [
  { key: 'home', label: '首页', icon: '⌂', url: '/pages/home/index' },
  { key: 'naming', label: '起名', icon: '名', url: '/pages/naming/index' },
  { key: 'community', label: '灵感', icon: '◇', url: '/pages/community/index' },
  { key: 'expert', label: '专家', icon: '◎', url: '/pages/marketplace/index' },
  { key: 'assets', label: '资产', icon: '□', url: '/pages/assets/index' }
];

const navTo = url => uni.navigateTo({ url });
const switchMenu = (key, url) => {
  if (props.currentMenu === key) return;
  uni.redirectTo({ url });
};

const refreshUser = async () => {
  token.value = uni.getStorageSync('token');
  user.value = uni.getStorageSync('user') || {};
  if (!token.value) return;
  try {
    const profile = await http.getMyProfile();
    user.value = { ...user.value, username: profile.username, email: profile.email, role: profile.role, expert_status: profile.expert_status };
    uni.setStorageSync('user', user.value);
  } catch (error) {}
};

onShow(refreshUser);
</script>

<style lang="scss" scoped>
@import "@/uni.scss";

.app-shell {
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  color: $text-main;
  background: #f8f4ec;
}
.top-nav {
  height: 72px;
  padding: 0 34px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 28px;
  background: rgba(255,255,255,.9);
  border-bottom: 1px solid rgba(199,154,75,.24);
  backdrop-filter: blur(14px);
  position: relative;
  z-index: 20;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex-shrink: 0;
}
.seal {
  width: 42px;
  height: 42px;
  border: 2px solid $brand-primary;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  writing-mode: vertical-rl;
  color: $brand-primary;
  font-size: 12px;
  font-weight: 900;
  line-height: 1.05;
}
.brand-name {
  font-size: 26px;
  font-weight: 900;
  color: $brand-primary;
}
.brand-sub {
  margin-top: 2px;
  color: $text-secondary;
  font-size: 12px;
}
.desktop-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  gap: 20px;
}
.nav-link {
  height: 72px;
  display: flex;
  align-items: center;
  color: $brand-primary;
  font-size: 16px;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
}
.nav-link::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  border-radius: 999px;
  background: transparent;
}
.nav-link.active {
  font-weight: 900;
}
.nav-link.active::after {
  background: $brand-gold;
}
.top-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.member-btn,
.login-btn {
  height: 36px;
  line-height: 34px;
  margin: 0;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid rgba(199,154,75,.55);
  background: #fff;
  color: #b68136;
  font-size: 13px;
  font-weight: 900;
}
.login-btn {
  background: $brand-primary;
  color: #f5d392;
  border-color: $brand-primary;
}
.member-btn::after,
.login-btn::after {
  border: none;
}
.bell {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $brand-primary;
  border-radius: 50%;
}
.profile {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $brand-primary;
  color: #f5d392;
  font-weight: 900;
}
.profile-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}
.profile-copy text:first-child {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 900;
}
.profile-copy text:last-child {
  color: $text-secondary;
  font-size: 12px;
}
.chevron {
  color: $text-secondary;
}
.content-scroll {
  height: calc(100vh - 72px);
  height: calc(100dvh - 72px);
  box-sizing: border-box;
}
.ink-bg {
  min-height: calc(100vh - 72px);
  min-height: calc(100dvh - 72px);
  box-sizing: border-box;
  padding: 30px 32px 46px;
  background:
    radial-gradient(circle at 75% 48px, rgba(199,154,75,.22), transparent 150px),
    linear-gradient(180deg, rgba(255,255,255,.35), rgba(255,255,255,0) 360px),
    #f8f4ec;
  position: relative;
}
.ink-bg::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 260px;
  pointer-events: none;
  opacity: .58;
  background:
    radial-gradient(ellipse at 10% 60%, rgba(36,50,74,.14), transparent 130px),
    radial-gradient(ellipse at 78% 70%, rgba(36,50,74,.12), transparent 160px),
    radial-gradient(circle at 82% 18%, rgba(199,154,75,.22) 0 52px, transparent 54px);
}
.ink-bg :deep(> *) {
  position: relative;
  z-index: 1;
}
.mobile-tabbar {
  display: none;
}

@media (max-width: 980px) {
  .desktop-nav {
    gap: 12px;
  }
  .nav-link {
    font-size: 14px;
  }
  .profile-copy,
  .bell {
    display: none;
  }
}
@media (max-width: 768px) {
  .top-nav {
    height: 68px;
    padding: 0 18px;
    justify-content: space-between;
  }
  .desktop-nav,
  .brand-sub,
  .member-btn,
  .chevron {
    display: none;
  }
  .brand-name {
    font-size: 24px;
  }
  .content-scroll {
    height: calc(100vh - 68px - 66px);
    height: calc(100dvh - 68px - 66px);
  }
  .ink-bg {
    min-height: calc(100vh - 68px - 66px);
    min-height: calc(100dvh - 68px - 66px);
    padding: 16px 14px 28px;
  }
  .mobile-tabbar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 30;
    height: 66px;
    padding-bottom: env(safe-area-inset-bottom);
    background: rgba(255,255,255,.94);
    border-top: 1px solid rgba(199,154,75,.24);
    display: grid;
    grid-template-columns: repeat(5, 1fr);
  }
  .mobile-tab {
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    font-size: 12px;
    color: #8a92a0;
  }
  .mobile-tab.active {
    color: $brand-primary;
    font-weight: 900;
  }
  .tab-icon {
    font-size: 19px;
  }
}
</style>
