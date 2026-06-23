<template>
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

      <view class="section">
        <view class="section-title">VIP 套餐</view>
        <view v-for="item in membershipPackages" :key="item.id" class="membership-item">
          <view><view class="membership-name">{{ item.name }}</view><view class="membership-desc">{{ item.description }}</view></view>
          <view class="membership-buy"><text class="membership-price">¥{{ item.price }}</text><button size="mini" @click="buyMembership(item)">购买</button></view>
        </view>
        <view class="membership-note">模拟支付阶段，付款成功后会员立即开通或顺延。</view>
      </view>

      <view class="asset-tabs">
        <view v-for="item in tabs" :key="item.value" :class="['asset-tab', tab === item.value ? 'active' : '']" @click="tab = item.value">{{ item.label }}</view>
      </view>

      <view v-if="tab === 'names'" class="section compact-section">
        <view v-for="item in names" :key="item.id" class="asset-row"><view><text class="asset-name">{{ item.name }}</text><text class="muted">{{ item.category }} · {{ item.moral }}</text></view><button size="mini" class="outline" @click="removeName(item.id)">取消收藏</button></view>
        <view v-if="!names.length" class="empty">还没有收藏名字</view>
      </view>
      <view v-if="tab === 'visuals'" class="visual-grid">
        <view v-for="item in visuals" :key="item.id" class="visual-item"><image v-if="item.image_url" :src="item.image_url" mode="aspectFill"/><view class="asset-name">{{ item.name }}</view><view class="muted">{{ item.status }}</view></view>
        <view v-if="!visuals.length" class="empty">还没有视觉资产</view>
      </view>
      <view v-if="tab === 'orders'" class="section compact-section">
        <view v-for="item in orders" :key="item.id" class="order-item"><view class="order-head"><text>{{ item.asset_name }} · {{ item.expert_name }}</text><text class="teal">{{ item.status }}</text></view><view class="muted">{{ item.package_name }} · 实付 ¥{{ item.amount }}</view><view class="actions"><button v-if="item.status === 'PENDING_PAYMENT'" size="mini" @click="pay(item.id)">模拟支付</button><button v-if="item.status === 'DELIVERED'" size="mini" @click="complete(item.id)">确认完成</button></view><view v-if="item.report" class="report">{{ item.report.conclusion }}</view></view>
        <view v-if="!orders.length" class="empty">还没有专家订单</view>
      </view>
      <view v-if="tab === 'expert'" class="section compact-section">
        <view v-if="expert && expert.status !== 'REJECTED'"><view class="asset-name">{{ expert.display_name }}</view><view class="teal">申请状态：{{ expert.status }}</view><view class="muted">{{ expert.review_note }}</view><button v-if="expert.status === 'APPROVED'" class="primary" @click="goWorkbench">进入专家工作台</button></view>
        <view v-else><view v-if="expert?.status === 'REJECTED'" class="reject-note">上次申请未通过：{{ expert.review_note || '请完善资料后重新提交' }}</view><input class="form-input" :value="apply.display_name" placeholder="专家展示名" @input="apply.display_name=$event.detail.value"/><picker :range="typeLabels" @change="e=>apply.expert_type=types[e.detail.value]"><view class="form-input picker">{{ apply.expert_type === 'CULTURE_MASTER' ? '国学命名专家' : '品牌咨询师' }}</view></picker><textarea class="form-area" :value="apply.bio" placeholder="个人简介（至少20字）" @input="apply.bio=$event.detail.value"/><textarea class="form-area" :value="apply.credentials" placeholder="专业资历（至少10字）" @input="apply.credentials=$event.detail.value"/><input class="form-input" type="number" :value="apply.years_experience" placeholder="从业年限" @input="apply.years_experience=Number($event.detail.value)"/><button class="primary" @click="submitApply">{{ expert?.status === 'REJECTED' ? '重新提交申请' : '提交专家申请' }}</button></view>
      </view>

      <button v-if="profile.expert_status === 'APPROVED'" class="workbench-btn" @click="goWorkbench">进入专家工作台</button>
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
</template>

<script setup>
import { reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const token=ref(''),profile=ref(null),names=ref([]),visuals=ref([]),orders=ref([]),expert=ref(null),membershipPackages=ref([]),tab=ref('names'),editing=ref(false);
const tabs=[{label:'名字资产',value:'names'},{label:'Logo',value:'visuals'},{label:'专家订单',value:'orders'},{label:'专家身份',value:'expert'}];
const types=['CULTURE_MASTER','BRAND_CONSULTANT'],typeLabels=['国学命名专家','品牌咨询师'];
const apply=reactive({display_name:'',expert_type:'CULTURE_MASTER',bio:'',credentials:'',years_experience:0});
const editForm=reactive({username:'',bio:''});
const formatTime=value=>value?String(value).replace('T',' ').slice(0,16):'-';
const quotaPercent=quota=>quota.limit?`${Math.min(100,quota.used/quota.limit*100)}%`:'0%';
const load=async()=>{token.value=uni.getStorageSync('token');if(!token.value)return;[profile.value,membershipPackages.value,names.value,visuals.value,orders.value]=[await http.getMyProfile(),await http.getMembershipPackages(),(await http.getNameAssets()).items,(await http.getVisualAssets()).items,(await http.getMyExpertOrders()).items];uni.setStorageSync('user',{...(uni.getStorageSync('user')||{}),username:profile.value.username,email:profile.value.email,role:profile.value.role});try{expert.value=await http.getMyExpertProfile();if(expert.value.status==='REJECTED')Object.assign(apply,{display_name:expert.value.display_name,expert_type:expert.value.expert_type,bio:expert.value.bio,credentials:expert.value.credentials,years_experience:expert.value.years_experience})}catch(e){expert.value=null}};
const buyMembership=async item=>{const order=await http.createMembershipOrder(item.id);uni.showModal({title:`购买${item.name}`,content:`模拟支付 ¥${item.price}，确认后立即生效`,success:async result=>{if(result.confirm){profile.value=await http.payMembershipOrder(order.id);uni.showToast({title:'VIP 已开通',icon:'success'})}}})};
const openEdit=()=>{Object.assign(editForm,{username:profile.value.username,bio:profile.value.bio||''});editing.value=true};
const saveProfile=async()=>{profile.value=await http.updateMyProfile({...editForm});editing.value=false};
const removeName=async id=>{await http.deleteNameAsset(id);await load()};const pay=async id=>{await http.payExpertOrder(id);await load()};const complete=async id=>{await http.completeExpertOrder(id);await load()};const submitApply=async()=>{expert.value=await http.applyExpert({...apply});await load()};
const goLogin=()=>uni.navigateTo({url:'/pages/login/login'});const goWorkbench=()=>uni.navigateTo({url:'/pages/expert/workbench'});const goAdmin=()=>uni.navigateTo({url:'/pages/admin/index'});const logout=()=>{uni.removeStorageSync('token');uni.removeStorageSync('user');profile.value=null;token.value=''};
onShow(load);
</script>

<style scoped>
.page{padding:28rpx;background:#f3f5f8;min-height:100vh;box-sizing:border-box;color:#172033}.login-panel,.section{background:#fff;border-radius:8rpx;padding:28rpx;margin-bottom:22rpx}.login-panel{text-align:center;padding:100rpx 30rpx}.login-title,.section-title{font-size:34rpx;font-weight:700}.identity-card{display:flex;align-items:center;gap:24rpx;padding:36rpx;border-radius:8rpx;color:#fff;margin-bottom:22rpx}.vip-card{background:linear-gradient(110deg,#172554,#6d28d9)}.free-card{background:#0f766e}.avatar{width:112rpx;height:112rpx;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:46rpx;font-weight:700;flex-shrink:0}.identity-main{min-width:0}.identity-line{display:flex;gap:14rpx;align-items:center}.identity-name{font-size:40rpx;font-weight:700}.vip-badge{background:#f59e0b;color:#fff;padding:5rpx 14rpx;border-radius:20rpx;font-size:22rpx}.identity-email,.identity-expiry{font-size:25rpx;margin-top:8rpx;opacity:.92}.quota-row{margin-top:24rpx}.quota-head{display:flex;justify-content:space-between;color:#334155}.progress{height:14rpx;background:#e2e8f0;border-radius:7rpx;margin-top:10rpx;overflow:hidden}.progress-value{height:100%;background:#0f766e}.visual-progress{background:#7c3aed}.profile-row{display:flex;justify-content:space-between;gap:30rpx;padding:22rpx 0;border-bottom:1px solid #eef2f7;color:#64748b}.profile-row text:last-child{color:#172033;text-align:right}.profile-bio{display:block}.profile-bio text{display:block;text-align:left!important;margin-bottom:8rpx}.edit-btn{background:#eef2ff;color:#4338ca;margin-top:22rpx}.membership-item{display:flex;justify-content:space-between;gap:20rpx;padding:24rpx 0;border-bottom:1px solid #eef2f7}.membership-name{font-weight:700;font-size:28rpx}.membership-desc,.muted{display:block;color:#64748b;font-size:23rpx;margin-top:7rpx}.membership-buy{text-align:right}.membership-price{display:block;color:#ea580c;font-weight:700;margin-bottom:8rpx}.membership-note{color:#b45309;font-size:23rpx;margin-top:20rpx}.asset-tabs{display:flex;gap:8rpx;overflow-x:auto;margin:26rpx 0}.asset-tab{background:#fff;padding:14rpx 20rpx;border-radius:8rpx;white-space:nowrap}.asset-tab.active{background:#172554;color:#fff}.asset-row,.order-head{display:flex;justify-content:space-between;gap:18rpx}.asset-row,.order-item{padding:18rpx 0;border-bottom:1px solid #eef2f7}.asset-name{display:block;font-size:30rpx;font-weight:700}.visual-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16rpx}.visual-item{background:#fff;padding:14rpx;border-radius:8rpx}.visual-item image{width:100%;height:230rpx}.actions{display:flex;gap:10rpx;margin-top:14rpx}.actions button{margin:0}.report{background:#f8fafc;padding:14rpx;margin-top:12rpx}.teal{color:#0f766e}.outline{background:#fff;color:#64748b}.primary,.workbench-btn{background:#0f766e;color:#fff;border-radius:8rpx;margin-top:20rpx}.admin-btn{background:#1d4ed8;color:#fff}.logout-btn{background:#fff;color:#dc2626;border:1px solid #fecaca}.reject-note{background:#fff1f2;color:#be123c;padding:18rpx;margin-bottom:16rpx}.form-input,.form-area{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;background:#f8fafc;border-radius:8rpx;font-size:27rpx}.form-input{height:84rpx;padding:0 18rpx;margin-bottom:14rpx}.picker{display:flex;align-items:center}.form-area{height:140rpx;padding:18rpx;margin-bottom:14rpx}.overlay{position:fixed;inset:0;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;padding:30rpx;z-index:20}.dialog{width:min(640rpx,100%);background:#fff;border-radius:8rpx;padding:28rpx}.dialog-title{font-size:32rpx;font-weight:700;margin-bottom:18rpx}.field-label{font-size:24rpx;color:#64748b;margin:12rpx 0 8rpx}.empty{text-align:center;padding:60rpx;color:#94a3b8;grid-column:1/-1}@media(min-width:900px){.page{max-width:900px;margin:0 auto}.visual-grid{grid-template-columns:repeat(3,1fr)}}
</style>
