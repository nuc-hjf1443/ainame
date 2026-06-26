<template>
  <view class="page">
    <view class="tabs">
      <view v-for="item in tabs" :key="item.value" :class="['tab', tab === item.value ? 'active' : '']" @click="tab = item.value">{{ item.label }}</view>
    </view>

    <view v-if="tab === 'experts'">
      <view v-for="item in experts" :key="item.id" class="card">
        <view class="head"><text class="name">{{ item.display_name }}</text><text>{{ item.status }}</text></view>
        <view class="copy">{{ expertTypeText(item.expert_type) }} · {{ item.years_experience }} 年经验</view>
        <view class="info-block"><text>个人简介</text><view>{{ item.bio }}</view></view>
        <view class="info-block"><text>资历证明</text><view>{{ item.credentials }}</view></view>
        <view v-if="item.review_note" class="review-note">审核备注：{{ item.review_note }}</view>
        <view class="actions">
          <button size="mini" @click="review(item, 'APPROVED')">通过</button>
          <button size="mini" class="danger" @click="review(item, 'REJECTED')">拒绝</button>
          <button size="mini" class="outline" @click="review(item, 'SUSPENDED')">停用</button>
        </view>
      </view>
      <view v-if="!experts.length" class="empty">暂无专家申请</view>
    </view>

    <view v-if="tab === 'packages'">
      <view class="form">
        <view class="form-title">添加平台服务套餐</view>
        <view class="field-label">套餐名称</view>
        <input class="form-input" :value="pkg.name" placeholder="例如：品牌命名基础精批" @input="updateField('name', $event.detail.value)" />

        <view class="field-label">服务专家类型</view>
        <picker :range="typeLabels" @change="changeExpertType">
          <view class="form-input picker-value">{{ expertTypeLabel }}</view>
        </picker>

        <view class="form-grid">
          <view>
            <view class="field-label">价格（元）</view>
            <input class="form-input" type="number" :value="pkg.price" placeholder="199" @input="updateField('price', $event.detail.value)" />
          </view>
          <view>
            <view class="field-label">交付天数</view>
            <input class="form-input" type="number" :value="pkg.delivery_days" placeholder="3" @input="updateField('delivery_days', $event.detail.value)" />
          </view>
        </view>

        <view class="field-label">服务说明</view>
        <textarea class="form-textarea" :value="pkg.description" placeholder="说明报告内容和服务边界" @input="updateField('description', $event.detail.value)" />
        <button class="primary" :loading="packageSaving" @click="createPackage">新增套餐</button>
      </view>

      <view v-for="item in packages" :key="item.id" class="card">
        <view class="head"><text class="name">{{ item.name }}</text><text>¥{{ item.price }}</text></view>
        <view class="copy">{{ item.expert_type }} · {{ item.delivery_days }}天 · {{ item.status }}</view>
        <button size="mini" class="outline" @click="togglePackage(item)">{{ item.status === 'ACTIVE' ? '下架' : '上架' }}</button>
      </view>
      <view v-if="!packages.length" class="empty">暂无服务套餐</view>
    </view>

    <view v-if="tab === 'reports'">
      <view v-for="item in reports" :key="item.id" class="card">
        <view class="head"><text>{{ item.target_type }} #{{ item.target_id }}</text><text>{{ item.reason }}</text></view>
        <view class="copy">{{ item.detail }}</view>
        <view class="actions">
          <button size="mini" class="danger" @click="moderate(item.id, 'HIDE')">隐藏内容</button>
          <button size="mini" class="outline" @click="moderate(item.id, 'DISMISS')">驳回举报</button>
        </view>
      </view>
      <view v-if="!reports.length" class="empty">暂无待处理举报</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const tab = ref('experts');
const experts = ref([]);
const packages = ref([]);
const reports = ref([]);
const packageSaving = ref(false);
const tabs = [{label:'专家审核',value:'experts'},{label:'服务套餐',value:'packages'},{label:'社区举报',value:'reports'}];
const types = ['CULTURE_MASTER', 'BRAND_CONSULTANT'];
const typeLabels = ['国学命名', '品牌咨询'];
const pkg = reactive({name:'',expert_type:'CULTURE_MASTER',price:'',delivery_days:'3',description:'',status:'ACTIVE'});
const expertTypeLabel = computed(() => typeLabels[types.indexOf(pkg.expert_type)] || typeLabels[0]);
const expertTypeText = value => typeLabels[types.indexOf(value)] || value;

const updateField = (field, value) => { pkg[field] = value; };
const changeExpertType = event => { pkg.expert_type = types[Number(event.detail.value)]; };
const load = async () => {
  [experts.value, packages.value, reports.value] = [
    (await http.getAdminExperts()).items,
    await http.getAdminServicePackages(),
    (await http.getAdminCommunityReports()).items
  ];
};
const review = async (item, status) => {
  const title = status === 'APPROVED' ? '通过专家申请' : (status === 'REJECTED' ? '拒绝专家申请' : '停用专家身份');
  uni.showModal({
    title,
    content: status === 'APPROVED' ? `确认通过「${item.display_name}」的专家申请？` : '',
    editable: status !== 'APPROVED',
    placeholderText: status === 'REJECTED' ? '填写拒绝原因' : '填写停用原因',
    success: async result => {
      if (!result.confirm) return;
      if (status !== 'APPROVED' && !String(result.content || '').trim()) return uni.showToast({title:'请填写审核原因',icon:'none'});
      await http.reviewAdminExpert(item.id, {status, review_note:String(result.content || '').trim() || null});
      await load();
    }
  });
};
const createPackage = async () => {
  const price = Number(pkg.price);
  const deliveryDays = Number(pkg.delivery_days);
  if (!pkg.name.trim() || !pkg.description.trim() || !Number.isFinite(price) || price <= 0 || !Number.isInteger(deliveryDays) || deliveryDays <= 0) {
    return uni.showToast({title:'请完整填写套餐名称、价格、天数和说明',icon:'none'});
  }
  packageSaving.value = true;
  try {
    await http.createAdminServicePackage({...pkg, price, delivery_days: deliveryDays});
    Object.assign(pkg, {name:'', price:'', delivery_days:'3', description:''});
    packages.value = await http.getAdminServicePackages();
    uni.showToast({title:'套餐已添加',icon:'success'});
  } finally {
    packageSaving.value = false;
  }
};
const togglePackage = async item => { await http.updateAdminServicePackage(item.id, {status:item.status==='ACTIVE'?'INACTIVE':'ACTIVE'}); packages.value = await http.getAdminServicePackages(); };
const moderate = async (id, action) => { await http.moderateAdminReport(id, {action,resolution:action==='HIDE'?'内容已隐藏':'举报不成立'}); reports.value = (await http.getAdminCommunityReports()).items; };
onLoad(load);
</script>

<style scoped>
.page{padding:28rpx;background:#f5f7f6;min-height:100vh;box-sizing:border-box}.tabs{display:flex;gap:10rpx;margin-bottom:24rpx}.tab{padding:14rpx 22rpx;background:#fff;border-radius:8rpx}.tab.active{background:#1e293b;color:#fff}.card,.form{background:#fff;border:1px solid #e2e8f0;border-radius:8rpx;padding:22rpx;margin-bottom:16rpx}.head{display:flex;justify-content:space-between}.name,.form-title{font-weight:700;font-size:30rpx}.form-title{margin-bottom:24rpx}.copy{color:#64748b;font-size:24rpx;margin:12rpx 0}.info-block{background:#f8fafc;border:1px solid #eef2f7;border-radius:8rpx;padding:16rpx;margin-top:12rpx}.info-block text{display:block;color:#64748b;font-size:23rpx;margin-bottom:8rpx}.info-block view{font-size:25rpx;line-height:1.6}.review-note{background:#fff7ed;color:#c2410c;border-radius:8rpx;padding:14rpx;margin-top:12rpx;font-size:24rpx}.actions{display:flex;gap:10rpx;margin-top:16rpx}.actions button{margin:0}.danger{background:#fff;color:#dc2626}.outline{background:#fff;color:#475569}.field-label{font-size:24rpx;color:#475569;margin:16rpx 0 8rpx}.form-input,.form-textarea{width:100%;box-sizing:border-box;background:#f8fafc;border:1px solid #cbd5e1;border-radius:8rpx;font-size:28rpx}.form-input{height:84rpx;padding:0 18rpx}.picker-value{display:flex;align-items:center}.form-textarea{height:140rpx;padding:18rpx}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16rpx}.primary{background:#1e293b;color:#fff;margin-top:20rpx}.empty{text-align:center;padding:80rpx;color:#94a3b8}@media(max-width:600px){.form-grid{grid-template-columns:1fr}}
</style>
