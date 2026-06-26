<template>
  <DashboardLayout currentMenu="profile">
  <view class="page">
    <view v-if="!token" class="login-panel">
      <view class="login-title">登录后管理会员与数字资产</view>
      <button class="primary" @click="goLogin">登录 / 注册</button>
    </view>

    <template v-else-if="profile">
      <view :class="['identity-card', profile.is_vip ? 'vip-card' : 'free-card']">
        <view class="avatar">{{ profile.username.slice(0, 1) }}</view>
        <view class="identity-main">
          <view class="identity-line"><text class="identity-name">{{ profile.username }}</text><text v-if="profile.is_vip" class="vip-badge">VIP</text></view>
          <view class="identity-email">{{ profile.email }}</view>
          <view class="identity-expiry">{{ profile.is_vip ? `到期：${formatTime(profile.vip_expires_at)}` : '当前为免费用户' }}</view>
        </view>
      </view>

      <view class="section quota-card">
        <view class="section-title">今日额度</view>
        <view class="quota-row">
          <view class="quota-head"><text>智能起名</text><text>{{ profile.naming_quota.used }} / {{ profile.naming_quota.limit }}</text></view>
          <view class="progress"><view class="progress-value" :style="{width: quotaPercent(profile.naming_quota)}"></view></view>
        </view>
        <view class="quota-row">
          <view class="quota-head"><text>视觉生成</text><text>{{ profile.visual_quota.used }} / {{ profile.visual_quota.limit }}</text></view>
          <view class="progress"><view class="progress-value visual-progress" :style="{width: quotaPercent(profile.visual_quota)}"></view></view>
        </view>
        <view class="quota-balance-row">
          <text>购买起名次数余额</text>
          <text>{{ profile.naming_balance || 0 }} 次</text>
        </view>
      </view>

      <view class="section">
        <view class="section-title">个人资料</view>
        <view class="profile-row"><text>昵称</text><text>{{ profile.username }}</text></view>
        <view class="profile-row"><text>邮箱</text><text>{{ profile.email }}</text></view>
        <view class="profile-row"><text>账户类型</text><text>{{ profile.account_type }}</text></view>
        <view class="profile-row"><text>注册时间</text><text>{{ formatTime(profile.created_time) }}</text></view>
        <view class="profile-row profile-bio"><text>个人简介</text><text>{{ profile.bio || '暂未填写' }}</text></view>
        <button class="edit-btn" @click="openEdit">修改个人信息</button>
      </view>

      <view class="section compact-section">
        <view class="section-title">专家身份</view>
        <view v-if="expert" class="expert-status-card">
          <view class="status-head">
            <view>
              <view class="asset-name">{{ expert.display_name }}</view>
              <view class="muted">{{ expertTypeLabel(expert.expert_type) }} · {{ expert.years_experience }} 年经验</view>
            </view>
            <text :class="['status-pill', expert.status]">{{ statusLabel(expert.status) }}</text>
          </view>
          <view v-if="expert.review_note" class="review-note">{{ expert.review_note }}</view>
          <button v-if="expert.status === 'APPROVED'" class="primary" @click="goWorkbench">进入专家工作台</button>
          <button v-else-if="expert.status === 'REJECTED'" class="primary" @click="goExpertApply">重新提交申请</button>
          <view v-else class="muted status-copy">{{ expert.status === 'PENDING' ? '申请已提交，请等待管理员审核。' : '当前专家身份已停用，请联系管理员。' }}</view>
        </view>
        <view v-else class="expert-status-card">
          <view class="asset-name">尚未申请专家身份</view>
          <view class="muted">提交个人简介和专业资历后，管理员审核通过即可接收精批订单。</view>
          <button class="primary" @click="goExpertApply">申请成为专家</button>
        </view>
      </view>

      <button v-if="String(profile.role).toUpperCase() === 'ADMIN'" class="admin-btn" @click="goAdmin">管理员后台</button>
      <button class="logout-btn" @click="logout">退出登录</button>
    </template>

    <view v-if="editing" class="overlay" @click="editing=false">
      <view class="dialog" @click.stop>
        <view class="dialog-title">修改个人信息</view>
        <view class="field-label">昵称</view><input class="form-input" :value="editForm.username" @input="editForm.username=$event.detail.value" />
        <view class="field-label">个人简介</view><textarea class="form-area" :value="editForm.bio" @input="editForm.bio=$event.detail.value" />
        <button class="primary" @click="saveProfile">保存</button>
      </view>
    </view>
  </view>
  </DashboardLayout>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const token=ref(''),profile=ref(null),expert=ref(null),editing=ref(false);
const editForm=reactive({username:'',bio:''});
const formatTime=value=>value?String(value).replace('T',' ').slice(0,16):'-';
const quotaPercent=quota=>quota.limit?`${Math.min(100,quota.used/quota.limit*100)}%`:'0%';
const expertTypeLabel=value=>value==='CULTURE_MASTER'?'国学命名专家':'品牌咨询师';
const statusLabel=value=>({PENDING:'待审核',APPROVED:'已通过',REJECTED:'已拒绝',SUSPENDED:'已停用'}[value]||value);
const load=async()=>{token.value=uni.getStorageSync('token');if(!token.value)return;profile.value=await http.getMyProfile();uni.setStorageSync('user',{...(uni.getStorageSync('user')||{}),username:profile.value.username,email:profile.value.email,role:profile.value.role,expert_status:profile.value.expert_status});try{expert.value=await http.getMyExpertProfile()}catch(e){expert.value=null}};
const openEdit=()=>{Object.assign(editForm,{username:profile.value.username,bio:profile.value.bio||''});editing.value=true};
const saveProfile=async()=>{profile.value=await http.updateMyProfile({...editForm});editing.value=false};
const goLogin=()=>uni.navigateTo({url:'/pages/login/login'});const goWorkbench=()=>uni.navigateTo({url:'/pages/expert/workbench'});const goExpertApply=()=>uni.navigateTo({url:'/pages/expert/apply'});const goAdmin=()=>uni.navigateTo({url:'/pages/admin/index'});const logout=()=>{uni.removeStorageSync('token');uni.removeStorageSync('user');profile.value=null;token.value=''};
onShow(load);
</script>

<style scoped>
.page { padding: 48rpx 32rpx 120rpx; background: #F9FAFB; min-height: 100%; box-sizing: border-box; color: #111827; }
.login-panel, .section { background: #FFFFFF; border-radius: 24rpx; padding: 48rpx; margin-bottom: 48rpx; box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #E5E7EB; }
.login-panel { text-align: center; padding: 100rpx 30rpx; }
.login-title, .section-title { font-size: 40rpx; font-weight: 600; color: #111827; margin-bottom: 32rpx; }
.identity-card { display: flex; align-items: center; gap: 32rpx; padding: 48rpx; border-radius: 24rpx; color: #fff; margin-bottom: 48rpx; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.vip-card { background: linear-gradient(110deg, #1D4ED8, #6D28D9); }
.free-card { background: #2563EB; }
.avatar { width: 112rpx; height: 112rpx; border-radius: 50%; background: rgba(255,255,255,.2); display: flex; align-items: center; justify-content: center; font-size: 46rpx; font-weight: 700; flex-shrink: 0; }
.identity-main { min-width: 0; }
.identity-line { display: flex; gap: 14rpx; align-items: center; }
.identity-name { font-size: 40rpx; font-weight: 700; }
.vip-badge { background: #F59E0B; color: #fff; padding: 4rpx 16rpx; border-radius: 999px; font-size: 24rpx; font-weight: 600; }
.identity-email, .identity-expiry { font-size: 28rpx; margin-top: 12rpx; opacity: .9; }
.quota-row { margin-top: 32rpx; }
.quota-head { display: flex; justify-content: space-between; color: #4B5563; font-size: 28rpx; margin-bottom: 12rpx; }
.quota-balance-row { display: flex; justify-content: space-between; align-items: center; margin-top: 32rpx; padding: 24rpx; border-radius: 16rpx; background: #EEF2FF; color: #1D4ED8; font-size: 28rpx; font-weight: 700; }
.progress { height: 16rpx; background: #E5E7EB; border-radius: 8rpx; overflow: hidden; }
.progress-value { height: 100%; background: #2563EB; border-radius: 8rpx; }
.visual-progress { background: #7C3AED; }
.profile-row { display: flex; justify-content: space-between; gap: 30rpx; padding: 24rpx 0; border-bottom: 1px solid #E5E7EB; color: #6B7280; font-size: 28rpx; }
.profile-row text:last-child { color: #111827; text-align: right; }
.profile-bio { display: block; }
.profile-bio text { display: block; text-align: left !important; margin-bottom: 8rpx; }
.edit-btn { background: #FFFFFF; color: #4B5563; border: 1px solid #D1D5DB; margin-top: 32rpx; border-radius: 16rpx; font-size: 28rpx; font-weight: 500; }
.muted { display: block; color: #6B7280; font-size: 24rpx; margin-top: 8rpx; }
.asset-tabs { display: flex; gap: 16rpx; overflow-x: auto; margin: 32rpx 0; }
.asset-tab { background: #FFFFFF; padding: 16rpx 32rpx; border-radius: 16rpx; white-space: nowrap; font-size: 28rpx; color: #4B5563; border: 1px solid #E5E7EB; }
.asset-tab.active { background: #DBEAFE; color: #1D4ED8; border-color: #DBEAFE; font-weight: 600; }
.asset-row, .order-head { display: flex; justify-content: space-between; gap: 18rpx; align-items: center; }
.asset-row, .order-item { padding: 24rpx 0; border-bottom: 1px solid #E5E7EB; }
.asset-name { display: block; font-size: 32rpx; font-weight: 600; color: #111827; }
.visual-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24rpx; margin-top: 24rpx; }
.visual-item { background: #FFFFFF; padding: 16rpx; border-radius: 16rpx; box-shadow: 0 2px 4px rgba(0,0,0,0.03); border: 1px solid #E5E7EB; }
.visual-item image { width: 100%; height: 230rpx; border-radius: 12rpx; }
.actions { display: flex; gap: 16rpx; margin-top: 20rpx; }
.actions button { margin: 0; border-radius: 12rpx; font-size: 24rpx; }
.report { background: #F9FAFB; padding: 24rpx; margin-top: 16rpx; border-radius: 12rpx; font-size: 28rpx; color: #4B5563; }
.teal { color: #2563EB; font-size: 28rpx; }
.outline { background: #FFFFFF; color: #4B5563; border: 1px solid #D1D5DB; }
.primary, .workbench-btn { background: #2563EB; color: #fff; border-radius: 16rpx; margin-top: 32rpx; font-size: 32rpx; font-weight: 500; }
.admin-btn { background: #1D4ED8; color: #fff; border-radius: 16rpx; margin-top: 24rpx; font-weight: 500; }
.logout-btn { background: #FFFFFF; color: #EF4444; border: 1px solid #FEE2E2; border-radius: 16rpx; margin-top: 24rpx; height: 96rpx; line-height: 96rpx; font-size: 32rpx; font-weight: 500; }
.reject-note { background: #FEE2E2; color: #EF4444; padding: 24rpx; margin-bottom: 24rpx; border-radius: 12rpx; font-size: 28rpx; }
.expert-status-card { background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 16rpx; padding: 28rpx; }
.status-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 24rpx; }
.status-pill { padding: 8rpx 18rpx; border-radius: 999px; font-size: 24rpx; color: #2563EB; background: #DBEAFE; white-space: nowrap; }
.status-pill.APPROVED { color: #059669; background: #D1FAE5; }
.status-pill.REJECTED, .status-pill.SUSPENDED { color: #DC2626; background: #FEE2E2; }
.review-note { background: #FFF7ED; color: #C2410C; padding: 20rpx; border-radius: 12rpx; margin-top: 22rpx; font-size: 26rpx; }
.status-copy { margin-top: 22rpx; }
.form-input, .form-area { width: 100%; box-sizing: border-box; border: 1px solid #D1D5DB; background: #FFFFFF; border-radius: 12rpx; font-size: 28rpx; color: #111827; }
.form-input { height: 88rpx; padding: 0 24rpx; margin-bottom: 24rpx; }
.picker { display: flex; align-items: center; }
.form-area { height: 160rpx; padding: 24rpx; margin-bottom: 24rpx; }
.overlay { position: fixed; inset: 0; background: rgba(17, 24, 39, 0.5); display: flex; align-items: center; justify-content: center; padding: 40rpx; z-index: 20; }
.dialog { width: min(640rpx, 100%); background: #FFFFFF; border-radius: 24rpx; padding: 48rpx; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
.dialog-title { font-size: 36rpx; font-weight: 700; margin-bottom: 32rpx; color: #111827; }
.field-label { font-size: 28rpx; color: #4B5563; margin: 16rpx 0 12rpx; font-weight: 500; }
.empty { text-align: center; padding: 80rpx; color: #9CA3AF; grid-column: 1/-1; font-size: 28rpx; }
@media(min-width: 900px){ .page{max-width: 900px; margin: 0 auto;} .visual-grid{grid-template-columns: repeat(3, 1fr);} }
</style>
