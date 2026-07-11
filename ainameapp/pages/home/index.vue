<template>
  <DashboardLayout currentMenu="home">
    <view class="home-page">
      <view class="hero">
        <view class="hero-copy">
          <view class="eyebrow">AI NAMING STUDIO</view>
          <view class="hero-title">为你生成更有<text>文化感</text>的好名字</view>
          <view class="hero-sub">AI 结合国学文化与现代审美，为个人、品牌与企业提供更有记忆点的命名方案。</view>
          <view class="hero-actions">
            <button class="primary" :loading="loading" @click="handleGenerate">开始AI起名</button>
            <button class="outline" @click="goNaming">查看起名结果</button>
          </view>
        </view>
        <view class="hero-art">
          <view class="gold-ring"></view>
          <view class="red-seal">启名</view>
        </view>
      </view>

      <view class="main-grid">
        <view class="form-card">
          <view class="tabs">
            <view v-for="item in categories" :key="item" :class="['tab', form.category === item ? 'active' : '']" @click="form.category = item">
              <text class="tab-icon">{{ iconMap[item] }}</text>{{ item === '企业名' ? '企业/品牌起名' : item }}
            </view>
          </view>

          <view class="form-grid" v-if="form.category === '企业名'">
            <view class="field">
              <text class="step">1</text><text class="label">所属行业</text>
              <input v-model="form.industry" placeholder="请选择或输入所属行业" />
            </view>
            <view class="field">
              <text class="step">2</text><text class="label">产品/服务</text>
              <input v-model="form.product" placeholder="请输入产品或服务名称" />
            </view>
            <view class="field">
              <text class="step">3</text><text class="label">目标用户</text>
              <input v-model="form.audience" placeholder="例如：年轻白领、宝妈、企业客户" />
            </view>
            <view class="field">
              <text class="step">4</text><text class="label">品牌定位</text>
              <input v-model="form.positioning" placeholder="例如：高端、专业、创新、亲民" />
            </view>
            <view class="field">
              <text class="step">5</text><text class="label">名称风格</text>
              <picker :range="styleOptions" @change="event => form.style = styleOptions[event.detail.value]">
                <view class="picker">{{ form.style }}<text>⌄</text></view>
              </picker>
            </view>
            <view class="field">
              <text class="step">6</text><text class="label">核心关键词</text>
              <input v-model="form.keywords" maxlength="20" placeholder="请输入2-5个关键词，逗号分隔" />
            </view>
            <view class="field">
              <text class="step">7</text><text class="label">禁用词</text>
              <input v-model="form.forbidden" maxlength="20" placeholder="请输入不希望出现的字词" />
            </view>
            <view class="field switch-field">
              <text class="step empty"></text><text class="label">检查 .com 域名</text>
              <switch :checked="form.checkDomain" color="#24324A" @change="event => form.checkDomain = event.detail.value" />
            </view>
          </view>

          <view class="form-grid" v-else>
            <view class="field" v-if="form.category === '人名'">
              <text class="step">1</text><text class="label">姓氏</text>
              <input v-model="form.surname" placeholder="请输入姓氏，如：张" />
            </view>
            <view class="field" v-if="form.category === '宠物名'">
              <text class="step">1</text><text class="label">宠物类型</text>
              <input v-model="form.petType" placeholder="例如：猫、狗、兔子" />
            </view>
            <view class="field">
              <text class="step">2</text><text class="label">性别倾向</text>
              <picker :range="genderOptions" @change="event => form.gender = genderOptions[event.detail.value]"><view class="picker">{{ form.gender }}<text>⌄</text></view></picker>
            </view>
            <view class="field">
              <text class="step">3</text><text class="label">字数要求</text>
              <picker :range="lengthOptions" @change="event => form.length = lengthOptions[event.detail.value]"><view class="picker">{{ form.length }}<text>⌄</text></view></picker>
            </view>
            <view class="field">
              <text class="step">4</text><text class="label">风格偏好</text>
              <picker :range="styleOptions" @change="event => form.style = styleOptions[event.detail.value]"><view class="picker">{{ form.style }}<text>⌄</text></view></picker>
            </view>
            <view class="field full">
              <text class="step">5</text><text class="label">补充说明</text>
              <textarea v-model="form.other" placeholder="例如：希望名字清雅、避免生僻字、带水木意象"></textarea>
            </view>
          </view>

          <view v-if="form.category === '企业名'" class="upload-row">
            <view>
              <text class="upload-title">使用私有资料</text>
              <text class="muted">上传企业命名规范或品牌资料，让 AI 学习专属标准。</text>
            </view>
            <button class="small-outline" :loading="uploading" @click="uploadKnowledge">上传 TXT/PDF</button>
          </view>

          <view class="quota-bar">
            <view class="quota-item"><text>今日免费次数</text><strong>{{ quotaText }}</strong></view>
            <view class="quota-line"></view>
            <view class="quota-item"><text>已购买次数</text><strong>{{ balanceText }}</strong></view>
            <button class="generate" :loading="loading" @click="handleGenerate">开始生成</button>
          </view>
        </view>

        <view class="side-stack">
          <view class="side-card">
            <view class="side-title">AI起名的优势</view>
            <view class="adv-grid">
              <view v-for="item in advantages" :key="item.title" class="adv-item">
                <view class="mini-icon">{{ item.icon }}</view>
                <view><text>{{ item.title }}</text><text>{{ item.desc }}</text></view>
              </view>
            </view>
          </view>
          <view class="side-card">
            <view class="side-head"><view class="side-title">示例输出</view><text @click="goNaming">查看更多</text></view>
            <view class="sample" v-for="item in samples" :key="item.name">
              <view class="sample-mark">{{ item.name.slice(0, 1) }}</view>
              <view><text>{{ item.name }}</text><text>{{ item.tags }}</text></view>
              <text class="heart">♡</text>
            </view>
          </view>
          <view class="stats-card">
            <view><strong>10,521,648+</strong><text>已生成名称</text></view>
            <view><strong>3,286,571+</strong><text>用户数</text></view>
            <view><strong>98.7%</strong><text>满意度</text></view>
          </view>
        </view>
      </view>

      <view class="trust-row">
        <view v-for="item in trustItems" :key="item.title"><strong>{{ item.title }}</strong><text>{{ item.desc }}</text></view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const RESULT_KEY = 'namingResultDraft';
const categories = ['人名', '企业名', '宠物名'];
const iconMap = { 人名: '人', 企业名: '企', 宠物名: '宠' };
const genderOptions = ['不限', '男', '女'];
const lengthOptions = ['不限', '单字', '两字', '多字'];
const styleOptions = ['古典文雅', '现代简约', '国际时尚', '科技未来', '温暖亲和'];
const advantages = [
  { icon: '文', title: '文化赋能', desc: '融合国学文化与现代审美' },
  { icon: '智', title: '智能生成', desc: '多维组合候选方案' },
  { icon: '评', title: '多维评估', desc: '音形义与传播综合评估' },
  { icon: '效', title: '高效定制', desc: '支持多轮反馈优化' }
];
const samples = [
  { name: '云启科技', tags: '科技/互联网  云计算  智能' },
  { name: '栖光品牌', tags: '美妆/个护  自然  温暖' },
  { name: '沐川创意', tags: '文化/创意  文创  流动感' }
];
const trustItems = [
  { title: '安全可靠', desc: '数据加密保护，隐私无忧' },
  { title: '专业权威', desc: '国学专家与品牌专家双重把关' },
  { title: '持续迭代', desc: 'AI 持续学习，不断优化结果' },
  { title: '商用安心', desc: '可用于注册商标与商业使用' }
];

const form = reactive({
  category: '企业名',
  surname: '',
  gender: '不限',
  length: '不限',
  other: '',
  industry: '',
  product: '',
  audience: '',
  positioning: '',
  style: '现代简约',
  keywords: '',
  forbidden: '',
  checkDomain: true,
  petType: ''
});
const loading = ref(false);
const uploading = ref(false);
const quotaText = ref('1 / 3');
const balanceText = ref('12');

const buildOther = () => {
  if (form.category === '企业名') {
    return [
      `所属行业：${form.industry}`,
      `产品/服务：${form.product}`,
      `目标用户：${form.audience}`,
      `品牌定位：${form.positioning}`,
      `名称风格：${form.style}`,
      `核心关键词：${form.keywords}`,
      `禁用词：${form.forbidden}`,
      `检查.com域名：${form.checkDomain ? '是' : '否'}`
    ].filter(item => !item.endsWith('：')).join('\n');
  }
  if (form.category === '宠物名') {
    return [`宠物类型：${form.petType}`, `风格：${form.style}`, form.other].filter(Boolean).join('\n');
  }
  return [`风格：${form.style}`, form.other].filter(Boolean).join('\n');
};
const buildPayload = () => ({
  category: form.category,
  surname: form.category === '人名' ? form.surname.trim() : '',
  gender: form.gender,
  length: form.length,
  other: buildOther(),
  exclude: form.forbidden ? form.forbidden.split(/[，,]/).map(item => item.trim()).filter(Boolean) : []
});
const validate = () => {
  if (!uni.getStorageSync('token')) {
    uni.navigateTo({ url: '/pages/login/login' });
    return false;
  }
  if (form.category === '人名' && !form.surname.trim()) {
    uni.showToast({ title: '请填写姓氏', icon: 'none' });
    return false;
  }
  if (form.category === '企业名' && !String(form.industry || form.product || form.keywords).trim()) {
    uni.showToast({ title: '请填写行业、产品或关键词', icon: 'none' });
    return false;
  }
  if (form.category === '宠物名' && !form.petType.trim()) {
    uni.showToast({ title: '请填写宠物类型', icon: 'none' });
    return false;
  }
  return true;
};
const handleGenerate = async () => {
  if (!validate()) return;
  loading.value = true;
  uni.showLoading({ title: 'AI 生成中...' });
  try {
    const result = await http.generateName(buildPayload());
    uni.setStorageSync(RESULT_KEY, {
      names: result.names || [],
      threadId: result.thread_id,
      form: { ...form },
      round: 1,
      createdAt: new Date().toISOString()
    });
    uni.redirectTo({ url: '/pages/naming/index' });
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};
const uploadKnowledge = () => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  uni.chooseFile({
    count: 1,
    extension: ['.txt', '.pdf'],
    success: async result => {
      const file = result.tempFiles?.[0] || result.tempFilePaths?.[0];
      const path = file.path || file;
      uploading.value = true;
      try {
        await http.uploadKnowledge(path);
        uni.showToast({ title: '资料已提交处理', icon: 'none' });
      } finally {
        uploading.value = false;
      }
    }
  });
};
const goNaming = () => uni.redirectTo({ url: '/pages/naming/index' });
onShow(async () => {
  if (!uni.getStorageSync('token')) return;
  try {
    const profile = await http.getMyProfile();
    quotaText.value = `${profile.naming_quota?.used || 0} / ${profile.naming_quota?.limit || 3}`;
    balanceText.value = String(profile.naming_balance || 0);
  } catch (error) {}
});
</script>

<style lang="scss" scoped>
@import "@/uni.scss";

.home-page { max-width: 1440px; margin: 0 auto; }
.hero {
  min-height: 240px;
  position: relative;
  overflow: hidden;
  margin-bottom: 26px;
  border-radius: 10px;
  background:
    linear-gradient(90deg, rgba(255,255,255,.96), rgba(255,255,255,.72) 58%, rgba(255,255,255,.26)),
    radial-gradient(circle at 76% 26%, rgba(199,154,75,.30), transparent 150px),
    linear-gradient(135deg, #f8f3e8, #fff 55%, #edf1f5);
  border: 1px solid rgba(199,154,75,.2);
  box-shadow: $shadow-soft;
}
.hero::before {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 110px;
  opacity: .16;
  background:
    radial-gradient(ellipse at 18% 100%, #24324a 0 9%, transparent 44%),
    radial-gradient(ellipse at 54% 100%, #24324a 0 10%, transparent 46%),
    radial-gradient(ellipse at 86% 100%, #24324a 0 9%, transparent 44%);
}
.hero-copy { position: relative; z-index: 2; padding: 48px 56px; width: min(740px, 62%); }
.eyebrow { color: $brand-gold; font-size: 13px; font-weight: 900; letter-spacing: 2px; }
.hero-title { margin-top: 14px; font-size: 42px; line-height: 1.18; font-weight: 900; color: $brand-primary; }
.hero-title text { color: $brand-gold; }
.hero-sub { margin-top: 14px; color: $text-secondary; font-size: 18px; line-height: 1.7; }
.hero-actions { display: flex; gap: 16px; margin-top: 26px; flex-wrap: wrap; }
.primary,.outline,.generate,.small-outline {
  margin: 0;
  border-radius: 8px;
  font-weight: 900;
}
.primary,.generate { background: $brand-primary; color: #f5d392; }
.outline,.small-outline { background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.5); }
.primary,.outline { height: 44px; line-height: 44px; padding: 0 28px; }
.primary::after,.outline::after,.generate::after,.small-outline::after { border: none; }
.hero-art { position: absolute; right: 70px; top: 38px; width: 250px; height: 200px; }
.gold-ring { position: absolute; right: 24px; top: 8px; width: 148px; height: 148px; border: 15px solid rgba(199,154,75,.32); border-radius: 50%; }
.red-seal { position: absolute; right: 0; bottom: 24px; width: 54px; height: 54px; border: 3px solid #b42318; color: #b42318; border-radius: 8px; display: flex; align-items: center; justify-content: center; writing-mode: vertical-rl; font-weight: 900; }
.main-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 24px; align-items: start; }
.form-card,.side-card,.stats-card,.trust-row {
  background: rgba(255,255,255,.96);
  border: 1px solid #e7e0d4;
  border-radius: 10px;
  box-shadow: $shadow-soft;
}
.form-card { overflow: hidden; }
.tabs { display: grid; grid-template-columns: repeat(3, 1fr); border-bottom: 1px solid #e7e0d4; }
.tab { min-height: 58px; display: flex; align-items: center; justify-content: center; gap: 10px; color: $text-secondary; font-size: 16px; font-weight: 900; cursor: pointer; border-bottom: 3px solid transparent; }
.tab.active { background: $brand-primary; color: #fff; border-bottom-color: $brand-gold; }
.tab-icon,.mini-icon { width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: $brand-gold-soft; color: $brand-gold; font-size: 12px; font-weight: 900; }
.tab.active .tab-icon { background: rgba(255,255,255,.14); color: #fff; }
.form-grid { padding: 28px 32px 22px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px 28px; }
.field { position: relative; min-width: 0; padding-left: 36px; }
.field.full { grid-column: span 2; }
.step { position: absolute; left: 0; top: 32px; width: 22px; height: 22px; border-radius: 50%; background: $brand-gold; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 900; }
.step.empty { width: 12px; height: 12px; top: 40px; }
.label { display: block; color: $brand-primary; font-size: 14px; font-weight: 900; margin-bottom: 10px; }
input,.picker,textarea { width: 100%; box-sizing: border-box; background: #fbfaf7; border: 1px solid #e7e0d4; border-radius: 8px; color: $text-main; font-size: 14px; }
input,.picker { height: 48px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; }
textarea { min-height: 112px; padding: 14px 16px; line-height: 1.6; }
.switch-field { display: flex; align-items: center; gap: 16px; padding-top: 28px; }
.switch-field .label { flex: 1; margin: 0; }
.upload-row { margin: 0 32px 22px; padding: 18px 20px; border-radius: 8px; border: 1px dashed rgba(199,154,75,.54); background: #fffbf2; display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.upload-title { display: block; color: $brand-primary; font-weight: 900; }
.muted { display: block; margin-top: 4px; color: $text-secondary; font-size: 13px; line-height: 1.5; }
.small-outline { height: 34px; line-height: 34px; padding: 0 16px; font-size: 13px; flex-shrink: 0; }
.quota-bar { border-top: 1px solid #eee7dc; padding: 22px 32px; display: grid; grid-template-columns: 1fr 1px 1fr minmax(220px, .9fr); align-items: center; gap: 24px; }
.quota-item text { display: block; color: $text-secondary; font-size: 13px; }
.quota-item strong { display: block; margin-top: 4px; color: $brand-primary; font-size: 24px; }
.quota-line { width: 1px; height: 48px; background: #e7e0d4; }
.generate { height: 52px; line-height: 52px; font-size: 17px; }
.side-stack { display: flex; flex-direction: column; gap: 16px; }
.side-card { padding: 22px; }
.side-title { color: $brand-primary; font-size: 17px; font-weight: 900; }
.adv-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; margin-top: 18px; }
.adv-item { display: flex; gap: 10px; min-width: 0; }
.adv-item text:first-child,.sample text:first-child { display: block; color: $brand-primary; font-size: 14px; font-weight: 900; }
.adv-item text:last-child,.sample text:last-child { display: block; margin-top: 4px; color: $text-secondary; font-size: 12px; line-height: 1.45; }
.side-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.side-head>text { color: $text-secondary; font-size: 12px; cursor: pointer; }
.sample { display: grid; grid-template-columns: 34px minmax(0,1fr) auto; align-items: center; gap: 12px; padding: 14px 0; border-bottom: 1px solid #eee7dc; }
.sample:last-child { border-bottom: none; }
.sample-mark { width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: #f7f4ee; color: $brand-primary; font-weight: 900; }
.heart { color: $text-secondary; }
.stats-card { padding: 18px; display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; text-align: center; }
.stats-card strong { display: block; color: $brand-primary; font-size: 18px; }
.stats-card text { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }
.trust-row { margin-top: 24px; padding: 18px 24px; display: grid; grid-template-columns: repeat(4,1fr); gap: 18px; }
.trust-row strong { display: block; color: $brand-primary; font-size: 15px; }
.trust-row text { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }

@media (max-width: 1100px) {
  .main-grid { grid-template-columns: 1fr; }
  .side-stack { grid-template-columns: 1fr; }
  .hero-copy { width: auto; }
}
@media (max-width: 768px) {
  .hero { min-height: 280px; background: linear-gradient(135deg, rgba(23,36,59,.96), rgba(36,50,74,.9)); }
  .hero-copy { padding: 34px 26px; width: auto; }
  .hero-title { color: #fff; font-size: 34px; }
  .hero-sub { color: rgba(255,255,255,.76); font-size: 15px; }
  .hero-art { opacity: .45; right: 16px; transform: scale(.72); transform-origin: top right; }
  .form-grid { grid-template-columns: 1fr; padding: 22px 18px; }
  .field.full { grid-column: span 1; }
  .upload-row { margin: 0 18px 18px; flex-direction: column; align-items: stretch; }
  .small-outline { width: 100%; }
  .quota-bar { grid-template-columns: 1fr 1fr; padding: 18px; }
  .quota-line { display: none; }
  .generate { grid-column: span 2; }
  .trust-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 460px) {
  .tabs { grid-template-columns: 1fr; }
  .trust-row,.adv-grid,.stats-card { grid-template-columns: 1fr; }
}
</style>
