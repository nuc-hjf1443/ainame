<template>
  <view class="login-page">
    <view class="topbar">
      <view class="brand" @click="goHome"><view class="seal">启名</view><text>AI起名</text></view>
      <view class="links"><text @click="goHome">返回首页</text><text>帮助中心</text><text>隐私政策</text></view>
    </view>

    <view class="login-body">
      <view class="promo">
        <view class="promo-title">登录 AI起名，开启你的专属命名之旅</view>
        <view class="promo-copy">AI 结合国学文化与现代审美，为个人、品牌与企业提供更有文化感的好名字。</view>
        <view class="feature-row">
          <view><view class="feature-icon">云</view><strong>智能起名</strong><text>快速生成高分好名</text></view>
          <view><view class="feature-icon">屏</view><strong>品牌工作台</strong><text>品牌资产统一管理</text></view>
          <view><view class="feature-icon">专</view><strong>专家服务</strong><text>真人专家精批方案</text></view>
        </view>
        <view class="stats">
          <view><strong>10,521,648+</strong><text>已生成名称</text></view>
          <view><strong>98.7%</strong><text>用户满意度</text></view>
          <view><strong>安全可靠</strong><text>隐私保护</text></view>
        </view>
      </view>

      <view class="login-card">
        <view class="card-title">欢迎回来</view>
        <view class="card-sub">登录后继续使用 AI起名平台</view>
        <view class="mode-tabs">
          <view :class="mode === 'password' ? 'active' : ''" @click="mode = 'password'">密码登录</view>
          <view :class="mode === 'code' ? 'active' : ''" @click="mode = 'code'">验证码登录</view>
        </view>
        <input v-model="email" placeholder="邮箱 / 手机号" />
        <input v-if="mode === 'password'" v-model="password" password placeholder="请输入密码" />
        <view v-else class="code-row">
          <input v-model="code" placeholder="请输入验证码" />
          <button :loading="sendingCode" @click="sendCode">获取验证码</button>
        </view>
        <view class="option-row"><label><checkbox :checked="remember" @click="remember = !remember" />记住我</label><text>忘记密码？</text></view>
        <button class="login-btn" :loading="loading" @click="login">立即登录</button>
        <button class="register-btn" @click="goRegister">注册新账号</button>
        <view class="safe-tip">数据加密传输，保障账号安全</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/http/http.js';

const email = ref('');
const password = ref('');
const code = ref('');
const mode = ref('password');
const remember = ref(false);
const loading = ref(false);
const sendingCode = ref(false);

const login = async () => {
  if (!email.value.trim()) return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  if (mode.value !== 'password') return uni.showToast({ title: '验证码登录暂用于注册，请使用密码登录', icon: 'none' });
  if (!password.value) return uni.showToast({ title: '请输入密码', icon: 'none' });
  loading.value = true;
  try {
    const result = await http.login({ email: email.value.trim(), password: password.value });
    uni.setStorageSync('token', result.token);
    uni.setStorageSync('user', result.user);
    uni.reLaunch({ url: '/pages/home/index' });
  } finally {
    loading.value = false;
  }
};
const sendCode = async () => {
  if (!email.value.trim()) return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  sendingCode.value = true;
  try {
    await http.getEmailCode(email.value.trim());
    uni.showToast({ title: '验证码已发送', icon: 'none' });
  } finally {
    sendingCode.value = false;
  }
};
const goHome = () => uni.reLaunch({ url: '/pages/home/index' });
const goRegister = () => uni.navigateTo({ url: '/pages/register/register' });
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.login-page { min-height: 100vh; background: radial-gradient(circle at 44% 28%, rgba(199,154,75,.24), transparent 170px), linear-gradient(135deg,#fbf7ef,#fff); color: $brand-primary; overflow: hidden; }
.topbar { height: 72px; padding: 0 38px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(199,154,75,.24); background: rgba(255,255,255,.72); }
.brand { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.seal { width: 42px; height: 42px; border: 2px solid $brand-primary; border-radius: 8px; writing-mode: vertical-rl; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 12px; }
.brand text { font-size: 28px; font-weight: 900; }
.links { display: flex; gap: 28px; color: $brand-primary; }
.login-body { min-height: calc(100vh - 72px); display: grid; grid-template-columns: minmax(0,1fr) 520px; gap: 58px; align-items: center; max-width: 1360px; margin: 0 auto; padding: 46px 42px; box-sizing: border-box; }
.promo { min-height: 620px; display: flex; flex-direction: column; justify-content: center; position: relative; }
.promo::before { content: ""; position: absolute; inset: 10% -10% 0 -8%; opacity: .18; background: radial-gradient(ellipse at 20% 80%, #24324a 0 8%, transparent 45%), radial-gradient(ellipse at 70% 78%, #24324a 0 11%, transparent 50%); }
.promo-title { position: relative; font-size: 46px; line-height: 1.32; font-weight: 900; max-width: 720px; }
.promo-copy { position: relative; margin-top: 22px; color: #52647f; font-size: 20px; line-height: 1.8; max-width: 680px; }
.feature-row { position: relative; display: grid; grid-template-columns: repeat(3,1fr); gap: 24px; margin-top: 50px; max-width: 700px; }
.feature-row view view { margin: 0 auto 12px; }
.feature-row>view { text-align: center; border-right: 1px solid #e7e0d4; }
.feature-row>view:last-child { border-right: none; }
.feature-icon { width: 58px; height: 58px; border-radius: 50%; border: 1px solid rgba(199,154,75,.6); color: #b68136; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.feature-row strong { display: block; }
.feature-row text { display: block; color: $text-secondary; margin-top: 8px; font-size: 13px; line-height: 1.5; }
.stats { position: relative; margin-top: 54px; max-width: 700px; display: grid; grid-template-columns: repeat(3,1fr); gap: 0; background: rgba(255,255,255,.78); border: 1px solid #e7e0d4; border-radius: 10px; padding: 22px; box-shadow: $shadow-soft; }
.stats view { text-align: center; border-right: 1px solid #e7e0d4; }
.stats view:last-child { border-right: none; }
.stats strong { display: block; font-size: 22px; }
.stats text { color: $text-secondary; font-size: 13px; }
.login-card { background: rgba(255,255,255,.94); border: 1px solid #e7e0d4; border-radius: 18px; padding: 42px; box-shadow: 0 28px 80px rgba(36,50,74,.12); }
.card-title { text-align: center; font-size: 28px; font-weight: 900; }
.card-sub { text-align: center; color: $text-secondary; margin-top: 10px; }
.mode-tabs { display: grid; grid-template-columns: 1fr 1fr; margin: 30px 0 22px; border-bottom: 1px solid #e7e0d4; }
.mode-tabs view { text-align: center; padding: 14px 0; color: $text-secondary; border-bottom: 3px solid transparent; cursor: pointer; }
.mode-tabs .active { color: $brand-primary; border-bottom-color: $brand-primary; font-weight: 900; }
input { width: 100%; height: 52px; box-sizing: border-box; border: 1px solid #d8dde6; border-radius: 8px; background: #fff; margin-bottom: 18px; padding: 0 16px; font-size: 15px; }
.code-row { display: grid; grid-template-columns: minmax(0,1fr) 120px; gap: 10px; }
.code-row button { height: 52px; line-height: 52px; margin: 0; border-radius: 8px; background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.5); font-size: 13px; }
.code-row button::after { border: none; }
.option-row { display: flex; justify-content: space-between; align-items: center; color: $text-secondary; font-size: 14px; margin-bottom: 22px; }
.login-btn,.register-btn { width: 100%; height: 52px; line-height: 52px; border-radius: 8px; font-size: 17px; font-weight: 900; margin: 0 0 16px; }
.login-btn { background: $brand-primary; color: #f5d392; }
.register-btn { background: #fff; color: #b68136; border: 1px solid rgba(199,154,75,.58); }
.login-btn::after,.register-btn::after { border: none; }
.safe-tip { margin-top: 22px; padding-top: 18px; border-top: 1px solid #eee7dc; color: $text-secondary; text-align: center; font-size: 13px; }
@media (max-width: 980px) { .login-body { grid-template-columns: 1fr; } .promo { min-height: auto; } }
@media (max-width: 640px) { .topbar { padding: 0 18px; } .links { display: none; } .login-body { padding: 24px 16px; } .promo-title { font-size: 34px; } .feature-row,.stats { grid-template-columns: 1fr; } .feature-row>view,.stats view { border-right: none; border-bottom: 1px solid #e7e0d4; padding-bottom: 18px; } .login-card { padding: 26px 18px; } }
</style>
