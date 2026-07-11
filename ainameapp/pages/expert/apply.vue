<template>
  <DashboardLayout currentMenu="profile">
    <view class="apply-page">
      <view v-if="!token" class="panel login-panel">
        <view class="page-title">专家申请</view>
        <view class="muted">登录后可提交专家身份申请。</view>
        <button class="primary" @click="goLogin">登录 / 注册</button>
      </view>

      <template v-else>
        <view class="page-head">
          <view>
            <view class="page-title">专家申请</view>
            <view class="muted">填写专业简介和资历证明，通过审核后即可处理精批订单。</view>
          </view>
          <button class="outline-btn" @click="goProfile">返回个人中心</button>
        </view>

        <view v-if="expert && expert.status === 'PENDING'" class="panel">
          <view class="status-title">申请已提交，等待审核</view>
          <view class="readonly-row"><text>展示名</text><text>{{ expert.display_name }}</text></view>
          <view class="readonly-row"><text>专家类型</text><text>{{ expertTypeLabel(expert.expert_type) }}</text></view>
          <view class="readonly-row"><text>从业年限</text><text>{{ expert.years_experience }} 年</text></view>
          <view class="readonly-block"><text>个人简介</text><view>{{ expert.bio }}</view></view>
          <view class="readonly-block"><text>资历证明</text><view>{{ expert.credentials }}</view></view>
          <view class="muted status-copy">管理员审核后，结果会同步显示在个人中心。</view>
        </view>

        <view v-else-if="expert && expert.status === 'APPROVED'" class="panel">
          <view class="status-title">你已是认证专家</view>
          <view class="muted">{{ expert.display_name }} · {{ expertTypeLabel(expert.expert_type) }}</view>
          <button class="primary" @click="goWorkbench">进入专家工作台</button>
        </view>

        <view v-else-if="expert && expert.status === 'SUSPENDED'" class="panel">
          <view class="status-title">专家身份已停用</view>
          <view class="muted">{{ expert.review_note || '请联系管理员了解停用原因。' }}</view>
        </view>

        <view v-else class="panel">
          <view v-if="expert?.status === 'REJECTED'" class="reject-note">上次申请未通过：{{ expert.review_note || '请完善资料后重新提交' }}</view>
          <view class="field-label">专家展示名</view>
          <input class="form-input" :value="form.display_name" placeholder="例如：小猴老师" @input="form.display_name = $event.detail.value" />

          <view class="field-label">专家类型</view>
          <picker :range="typeLabels" @change="event => form.expert_type = types[Number(event.detail.value)]">
            <view class="form-input picker">{{ expertTypeLabel(form.expert_type) }}</view>
          </picker>

          <view class="field-label">个人简介</view>
          <textarea class="form-area" :value="form.bio" placeholder="至少 20 字，说明你的命名/品牌咨询经验" @input="form.bio = $event.detail.value" />

          <view class="field-label">专业资历/证明</view>
          <textarea class="form-area large" :value="form.credentials" placeholder="至少 10 字，可填写证书编号、项目案例、服务经历、作品链接等文本证明" @input="form.credentials = $event.detail.value" />

          <view class="field-label">从业年限</view>
          <input class="form-input" type="number" :value="form.years_experience" placeholder="例如：3" @input="form.years_experience = Number($event.detail.value)" />

          <button class="primary" :loading="submitting" @click="submitApply">{{ expert?.status === 'REJECTED' ? '重新提交申请' : '提交申请' }}</button>
        </view>
      </template>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const token = ref('');
const expert = ref(null);
const submitting = ref(false);
const types = ['CULTURE_MASTER', 'BRAND_CONSULTANT'];
const typeLabels = ['国学命名专家', '品牌咨询师'];
const form = reactive({ display_name: '', expert_type: 'CULTURE_MASTER', bio: '', credentials: '', years_experience: 0 });
const expertTypeLabel = value => typeLabels[types.indexOf(value)] || typeLabels[0];

const fillForm = data => {
  if (!data || data.status !== 'REJECTED') return;
  Object.assign(form, {
    display_name: data.display_name || '',
    expert_type: data.expert_type || 'CULTURE_MASTER',
    bio: data.bio || '',
    credentials: data.credentials || '',
    years_experience: Number(data.years_experience || 0)
  });
};

const load = async () => {
  token.value = uni.getStorageSync('token');
  if (!token.value) return;
  try {
    expert.value = await http.getMyExpertProfile();
    fillForm(expert.value);
  } catch (e) {
    expert.value = null;
  }
};

const submitApply = async () => {
  if (!form.display_name.trim() || form.bio.trim().length < 20 || form.credentials.trim().length < 10) {
    return uni.showToast({ title: '请完整填写展示名、简介和资历证明', icon: 'none' });
  }
  submitting.value = true;
  try {
    expert.value = await http.applyExpert({
      display_name: form.display_name.trim(),
      expert_type: form.expert_type,
      bio: form.bio.trim(),
      credentials: form.credentials.trim(),
      years_experience: Number(form.years_experience || 0)
    });
    uni.showToast({ title: '申请已提交', icon: 'success' });
    setTimeout(() => uni.redirectTo({ url: '/pages/profile/index' }), 500);
  } finally {
    submitting.value = false;
  }
};

const goLogin = () => uni.navigateTo({ url: '/pages/login/login' });
const goProfile = () => uni.redirectTo({ url: '/pages/profile/index' });
const goWorkbench = () => uni.redirectTo({ url: '/pages/expert/workbench' });
onShow(load);
</script>

<style scoped>
.apply-page{min-height:100%;color:#17243b}.page-head{display:flex;justify-content:space-between;align-items:center;gap:24rpx;margin-bottom:28rpx}.page-title{font-size:44rpx;font-weight:800}.panel{background:#fff;border:1px solid #e7e0d4;border-radius:8px;padding:36rpx;margin-bottom:28rpx}.login-panel{text-align:center;padding:100rpx 30rpx}.muted{display:block;color:#667085;font-size:25rpx;line-height:1.6;margin-top:8rpx}.status-title{font-size:34rpx;font-weight:800;margin-bottom:22rpx}.readonly-row{display:flex;justify-content:space-between;gap:24rpx;padding:18rpx 0;border-bottom:1px solid #eee7dc;color:#667085}.readonly-row text:last-child{color:#17243b;text-align:right}.readonly-block{padding:20rpx 0;border-bottom:1px solid #eee7dc}.readonly-block>text{display:block;color:#667085;margin-bottom:10rpx}.readonly-block>view{line-height:1.7}.status-copy{margin-top:24rpx}.field-label{font-size:26rpx;color:#52647f;font-weight:700;margin:20rpx 0 10rpx}.form-input,.form-area{width:100%;box-sizing:border-box;border:1px solid #e7e0d4;background:#fff;border-radius:8px;font-size:28rpx;color:#17243b}.form-input{height:88rpx;padding:0 22rpx}.picker{display:flex;align-items:center}.form-area{height:160rpx;padding:22rpx;line-height:1.6}.form-area.large{height:220rpx}.primary{background:#24324a;color:#f5d392;border-radius:8px;margin-top:28rpx}.outline-btn{margin:0;background:#fff;color:#52647f;border:1px solid #e7e0d4;border-radius:8px}.reject-note{background:#fff1f3;color:#b42318;padding:22rpx;border-radius:8px;margin-bottom:24rpx}@media(max-width:768px){.page-head{align-items:flex-start;flex-direction:column}.outline-btn{width:100%}}
</style>
