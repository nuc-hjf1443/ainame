<template>
  <view class="auth-layout">
    <view class="auth-left">
      <view class="auth-header">
        <text class="logo">启名星</text>
      </view>
      
      <view class="form-wrapper">
        <view class="hero-title">加入数万创意者的 启名星</view>
        
        <view class="segmented-control">
          <view class="segment-btn active">登录</view>
          <view class="segment-btn" @click="goRegister">注册</view>
        </view>
        
        <button class="social-btn" @click="showThirdPartyUnavailable"><text class="icon">G</text> 继续使用 Google</button>
        
        <view class="divider"><text class="divider-text">或者</text></view>

        <view class="input-group">
          <text class="label">邮箱</text>
          <input class="input-box" v-model="form.email" placeholder="请输入邮箱地址" />
        </view>
        
        <view class="input-group">
          <text class="label">密码</text>
          <input class="input-box" v-model="form.password" type="password" placeholder="请输入密码" />
        </view>
        
        <button class="submit-btn" :loading="loading" @click="handleLogin">登录</button>
        
        <view class="footer-links">
          <text class="muted">还没有账号？</text> <text class="link" @click="goRegister">立即注册</text>
        </view>
        
        <view class="legal-text">
          登录即代表您同意我们的 <text class="link-inline">服务条款</text> 和 <text class="link-inline">隐私政策</text>
        </view>
      </view>
    </view>
    
    <view class="auth-right">
      <view class="showcase">
        <view class="col">
          <image class="showcase-img img-short" src="https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?q=80&w=600&auto=format&fit=crop" mode="aspectFill"></image>
          <image class="showcase-img img-tall" src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop" mode="aspectFill"></image>
        </view>
        <view class="col">
          <image class="showcase-img img-tall" src="https://images.unsplash.com/photo-1634152962476-4b8a00e1915c?q=80&w=600&auto=format&fit=crop" mode="aspectFill"></image>
          <image class="showcase-img img-short" src="https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?q=80&w=600&auto=format&fit=crop" mode="aspectFill"></image>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/http/http.js';

const form = ref({ email: '', password: '' });
const loading = ref(false);

const isAdminRole = (user) => String(user?.role || '').trim().toUpperCase() === 'ADMIN';

const resolveNextUrl = async (user) => {
  if (isAdminRole(user)) return '/pages/admin/index';

  try {
    await http.checkAdminAccess();
    uni.setStorageSync('user', { ...user, role: 'ADMIN' });
    return '/pages/admin/index';
  } catch (e) {
    return '/pages/index/index';
  }
};

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) return uni.showToast({ title: '请填写完整', icon: 'none' });
  loading.value = true;
  try {
    const res = await http.login(form.value);
    uni.setStorageSync('token', res.token);
    uni.setStorageSync('user', res.user);
    const nextUrl = await resolveNextUrl(res.user);
    uni.showToast({ title: '登录成功' });
    setTimeout(() => uni.reLaunch({ url: nextUrl }), 1000);
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

const goRegister = () => uni.navigateTo({ url: '/pages/register/register' });
const showThirdPartyUnavailable = () => uni.showToast({ title: '暂未接入 Google 登录', icon: 'none' });
</script>

<style scoped>
.auth-layout { display: flex; min-height: 100vh; background: #ffffff; color: #111827; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
.auth-left { flex: 1; display: flex; flex-direction: column; padding: 48rpx; max-width: 100%; box-sizing: border-box; overflow-y: auto; }
@media (min-width: 900px) { .auth-left { max-width: 50%; padding: 80rpx 120rpx; } }
.auth-right { display: none; flex: 1; background: #ffffff; padding: 48rpx; box-sizing: border-box; height: 100vh; overflow: hidden; position: sticky; top: 0; }
@media (min-width: 900px) { .auth-right { display: flex; flex-direction: column; justify-content: center; } }

/* Logo */
.auth-header { margin-bottom: 80rpx; }
.logo { font-size: 40rpx; font-weight: 800; color: #2563EB; }

/* Form wrapper */
.form-wrapper { width: 100%; max-width: 720rpx; margin: 0 auto; }
.hero-title { font-size: 56rpx; font-weight: 700; color: #111827; margin-bottom: 64rpx; text-align: center; letter-spacing: -0.02em; line-height: 1.3; }

/* Segmented Control */
.segmented-control { display: flex; background: #E0E7FF; border-radius: 20rpx; padding: 8rpx; margin-bottom: 48rpx; }
.segment-btn { flex: 1; text-align: center; padding: 24rpx 0; font-size: 30rpx; font-weight: 600; color: #4B5563; border-radius: 16rpx; cursor: pointer; transition: all 0.2s; }
.segment-btn.active { background: #FFFFFF; color: #111827; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

/* Social button */
.social-btn { width: 100%; background: #FFFFFF; border: 1px solid #D1D5DB; color: #111827; border-radius: 20rpx; height: 100rpx; font-size: 30rpx; font-weight: 600; margin-bottom: 48rpx; display: flex; justify-content: center; align-items: center; cursor: pointer; }
.social-btn::after { border: none; }
.social-btn .icon { font-size: 36rpx; font-weight: 800; background: conic-gradient(from 180deg at 50% 50%, #4285F4 0deg, #34A853 90deg, #FBBC05 180deg, #EA4335 270deg, #4285F4 360deg); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-right: 16rpx; }

/* Divider */
.divider { display: flex; align-items: center; margin-bottom: 48rpx; }
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #E5E7EB; }
.divider-text { padding: 0 32rpx; color: #6B7280; font-size: 28rpx; }

/* Inputs */
.input-group { margin-bottom: 32rpx; }
.label { display: block; font-size: 28rpx; color: #4B5563; margin-bottom: 16rpx; font-weight: 500; text-align: left;}
.input-box { width: 100%; height: 96rpx; background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 20rpx; padding: 0 32rpx; font-size: 30rpx; color: #111827; box-sizing: border-box; transition: all 0.2s; }
.input-box:focus { border-color: #2563EB; box-shadow: 0 0 0 2px rgba(37,99,235,0.2); outline: none; }

/* Submit Button */
.submit-btn { width: 100%; height: 100rpx; background: #0047FF; color: #FFFFFF; border-radius: 20rpx; font-size: 32rpx; font-weight: 600; margin-top: 24rpx; display: flex; justify-content: center; align-items: center; border: none; cursor: pointer; }
.submit-btn::after { border: none; }

/* Footer Links */
.footer-links { text-align: center; margin-top: 48rpx; font-size: 28rpx; }
.muted { color: #6B7280; }
.link { color: #0047FF; font-weight: 600; cursor: pointer; }

/* Legal text */
.legal-text { text-align: center; margin-top: 48rpx; font-size: 24rpx; color: #9CA3AF; line-height: 1.6; }
.link-inline { text-decoration: underline; cursor: pointer; }

/* Right Panel Showcase Grid */
.showcase { display: grid; grid-template-columns: 1fr 1fr; gap: 32rpx; height: 100%; }
.col { display: flex; flex-direction: column; gap: 32rpx; height: 100%; }
.showcase-img { width: 100%; border-radius: 32rpx; object-fit: cover; background: #E5E7EB; }
.img-short { flex: 0.4; }
.img-tall { flex: 0.6; }
</style>
