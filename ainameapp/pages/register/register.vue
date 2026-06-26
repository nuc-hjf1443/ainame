<template>
  <view class="auth-layout">
    <view class="auth-left">
      <view class="auth-header">
        <text class="logo">启名星</text>
      </view>
      
      <view class="form-wrapper">
        <view class="hero-title">加入数万创意者的 启名星</view>
        
        <view class="segmented-control">
          <view class="segment-btn" @click="goLogin">登录</view>
          <view class="segment-btn active">注册</view>
        </view>
        
        <button class="social-btn" @click="showThirdPartyUnavailable"><text class="icon">G</text> 继续使用 Google</button>
        
        <view class="divider"><text class="divider-text">或者</text></view>

        <view class="input-group">
          <text class="label">用户名</text>
          <input class="input-box" v-model="form.username" placeholder="请输入用户名 (至少4个字符)" />
        </view>

        <view class="input-group">
          <text class="label">邮箱</text>
          <input class="input-box" v-model="form.email" placeholder="请输入邮箱地址" />
        </view>
        
        <view class="input-group">
          <text class="label">验证码</text>
          <view class="code-wrapper">
            <input class="input-box" v-model="form.code" placeholder="4位验证码" maxlength="4" />
            <button class="code-btn" :disabled="countdown > 0" @click="sendCode">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </button>
          </view>
        </view>
        
        <view class="input-group">
          <text class="label">密码</text>
          <input class="input-box" v-model="form.password" type="password" placeholder="请输入密码 (至少6位)" />
        </view>

        <view class="input-group">
          <text class="label">确认密码</text>
          <input class="input-box" v-model="form.confirm_password" type="password" placeholder="请再次确认密码" />
        </view>
        
        <button class="submit-btn" :loading="loading" @click="handleRegister">立即注册</button>
        
        <view class="footer-links">
          <text class="muted">已有账号？</text> <text class="link" @click="goLogin">登录</text>
        </view>
        
        <view class="legal-text">
          注册即代表您同意我们的 <text class="link-inline">服务条款</text> 和 <text class="link-inline">隐私政策</text>
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

// 表单数据绑定 (字段名严格对应后端 RegisterIn 的 Schema)
const form = ref({
  username: '',
  email: '',
  code: '',
  password: '',
  confirm_password: ''
});

const loading = ref(false);
const countdown = ref(0); // 倒计时秒数
let timer = null; // 定时器

// --- 发送邮箱验证码 ---
const sendCode = async () => {
  if (!form.value.email.trim()) {
    return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  }
  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailReg.test(form.value.email)) {
    return uni.showToast({ title: '邮箱格式不正确', icon: 'none' });
  }

  uni.showLoading({ title: '发送中...' });
  try {
    // 调用 http.js 中封装的 getEmailCode 接口
    await http.getEmailCode(form.value.email);
    uni.showToast({ title: '验证码已发送至邮箱', icon: 'success' });
    
    // 开启 60 秒倒计时
    countdown.value = 60;
    timer = setInterval(() => {
      if (countdown.value > 0) {
        countdown.value--;
      } else {
        clearInterval(timer);
      }
    }, 1000);
  } catch (error) {
    console.error("验证码发送失败:", error);
  } finally {
    uni.hideLoading();
  }
};

// --- 执行注册 ---
const handleRegister = async () => {
  // 1. 前端基础拦截校验 (与后端 Pydantic 规则保持一致)
  if (form.value.username.length < 4) return uni.showToast({ title: '用户名至少4位', icon: 'none' });
  if (!form.value.email.trim()) return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  if (form.value.code.length !== 4) return uni.showToast({ title: '请输入4位验证码', icon: 'none' });
  if (form.value.password.length < 6) return uni.showToast({ title: '密码至少6位', icon: 'none' });
  if (form.value.password !== form.value.confirm_password) return uni.showToast({ title: '两次密码输入不一致', icon: 'none' });

  loading.value = true;
  uni.showLoading({ title: '注册中...' });

  try {
    // 2. 发起注册网络请求
    await http.register(form.value);
    
    uni.showToast({ title: '注册成功！', icon: 'success' });
    // 3. 延迟跳转回登录页
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/login/login' });
    }, 1500);
    
  } catch (error) {
    console.error("注册报错:", error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

// 跳转到登录页
const goLogin = () => {
  uni.redirectTo({ url: '/pages/login/login' });
};
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

/* Code Wrapper */
.code-wrapper { display: flex; gap: 16rpx; }
.code-wrapper .input-box { flex: 1; }
.code-btn { width: 220rpx; height: 96rpx; display: flex; align-items: center; justify-content: center; background: #F3F4F6; color: #111827; border-radius: 20rpx; font-size: 28rpx; font-weight: 600; padding: 0; }
.code-btn::after { border: none; }
.code-btn[disabled] { opacity: 0.6; }

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
