<template>
  <DashboardLayout currentMenu="community">
    <view class="publish-page">
      <view class="page-head">
        <view>
          <view class="title">发起我的投票</view>
          <view class="sub">把候选名称交给社区，让真实选择帮助你做决定。</view>
        </view>
      </view>

      <view class="form-card">
        <view class="field-label">投票标题</view>
        <input v-model="form.title" placeholder="例如：帮我选一个品牌名" />
        <view class="field-label">分类</view>
        <picker :range="categories" @change="event => form.category = categories[event.detail.value]">
          <view class="picker">{{ form.category }}<text>⌄</text></view>
        </picker>
        <view class="field-label">背景描述</view>
        <textarea v-model="form.description" placeholder="说明用途、行业、目标用户和命名偏好"></textarea>

        <view class="candidate-head">
          <view class="section-title">候选名称</view>
          <button class="outline" @click="addCandidate">添加候选</button>
        </view>
        <view v-for="(item,index) in form.candidates" :key="index" class="candidate-row">
          <view class="candidate-index">{{ index + 1 }}</view>
          <input v-model="item.name" placeholder="候选名称" />
          <input v-model="item.moral" placeholder="名称说明（可选）" />
        </view>

        <button class="dark" :loading="submitting" @click="submit">发布投票</button>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { reactive, ref } from 'vue';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const categories = ['企业名', '人名', '宠物名'];
const submitting = ref(false);
const form = reactive({
  title: '',
  category: '企业名',
  description: '',
  candidates: [{ name: '', moral: '' }, { name: '', moral: '' }]
});
const addCandidate = () => {
  if (form.candidates.length >= 5) return uni.showToast({ title: '最多 5 个候选', icon: 'none' });
  form.candidates.push({ name: '', moral: '' });
};
const submit = async () => {
  const candidates = form.candidates.filter(item => item.name.trim()).map(item => ({ name: item.name.trim(), moral: item.moral.trim() || null, reference: null }));
  if (!form.title.trim()) return uni.showToast({ title: '请填写标题', icon: 'none' });
  if (candidates.length < 2) return uni.showToast({ title: '至少填写 2 个候选名称', icon: 'none' });
  submitting.value = true;
  try {
    const post = await http.createCommunityPost({
      title: form.title.trim(),
      description: form.description.trim() || null,
      category: form.category,
      candidates
    });
    uni.redirectTo({ url: `/pages/community/detail?id=${post.id}` });
  } finally {
    submitting.value = false;
  }
};
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.publish-page { max-width: 980px; margin: 0 auto; }
.page-head { margin: 30px 0 24px; }
.title { color: $brand-primary; font-size: 40px; font-weight: 900; line-height: 1.1; }
.sub { margin-top: 10px; color: $text-secondary; }
.form-card { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; padding: 28px; }
.field-label,.section-title { color: $brand-primary; font-weight: 900; margin: 18px 0 8px; }
input,.picker,textarea { width: 100%; box-sizing: border-box; border: 1px solid #e7e0d4; border-radius: 8px; background: #fbfaf7; color: $text-main; font-size: 14px; }
input,.picker { height: 46px; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; }
textarea { height: 120px; padding: 14px; line-height: 1.6; }
.candidate-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-top: 24px; }
.outline,.dark { margin: 0; border-radius: 8px; font-weight: 900; }
.outline { height: 36px; line-height: 34px; padding: 0 16px; background: #fff; color: #9b6a20; border: 1px solid rgba(199,154,75,.5); }
.outline::after,.dark::after { border: none; }
.candidate-row { display: grid; grid-template-columns: 36px 1fr 1.4fr; gap: 12px; align-items: center; margin-top: 12px; }
.candidate-index { width: 32px; height: 32px; border-radius: 50%; background: $brand-gold; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.dark { width: 100%; height: 48px; line-height: 48px; background: $brand-primary; color: #f5d392; margin-top: 26px; }
@media (max-width: 680px) { .candidate-row { grid-template-columns: 1fr; } }
</style>
