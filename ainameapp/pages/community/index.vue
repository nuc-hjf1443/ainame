<template>
  <DashboardLayout currentMenu="community">
    <view class="community-page">
      <view class="page-head">
        <view>
          <view class="title">灵感社区</view>
          <view class="sub">让真实选择帮助好名字胜出，发起投票并收集大家的判断。</view>
        </view>
        <button class="primary" @click="goPublish">发起我的投票</button>
      </view>

      <view class="filters">
        <view v-for="item in sorts" :key="item.value" :class="['chip', sort === item.value ? 'active' : '']" @click="changeSort(item.value)">{{ item.label }}</view>
        <picker :range="categories" @change="changeCategory"><view class="chip">{{ category || '全部分类' }} ⌄</view></picker>
      </view>

      <view v-if="loading && page === 1" class="state-card">正在加载灵感...</view>
      <view v-else-if="!posts.length" class="state-card">还没有公开灵感，快来发布第一篇。</view>

      <view v-else class="post-grid">
        <view v-for="post in posts" :key="post.id" class="post-card" @click="openPost(post.id)">
          <view class="cover">
            <image v-if="post.cover_image_url" :src="post.cover_image_url" mode="aspectFill" />
            <view v-else class="name-cover">{{ post.candidates?.[0]?.name || '灵感' }}</view>
          </view>
          <view class="post-body">
            <view class="post-meta"><text>{{ post.author_name }}</text><text>{{ post.category }}</text></view>
            <view class="post-title">{{ post.title }}</view>
            <view class="candidate-line">{{ (post.candidates || []).map(item => item.name).join(' / ') }}</view>
            <view class="post-foot"><text>{{ post.vote_count }} 人参与</text><text>{{ post.comment_count }} 条评论</text></view>
          </view>
        </view>
      </view>

      <button v-if="posts.length && posts.length < total" class="more" :loading="loadingMore" @click="loadMore">加载更多</button>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const posts = ref([]);
const total = ref(0);
const page = ref(1);
const loading = ref(false);
const loadingMore = ref(false);
const sort = ref('latest');
const category = ref('');
const sorts = [{ label: '最新', value: 'latest' }, { label: '热门', value: 'popular' }];
const categories = ['全部分类', '人名', '企业名', '宠物名'];

const load = async (append = false) => {
  append ? loadingMore.value = true : loading.value = true;
  try {
    const result = await http.getCommunityPosts(page.value, sort.value, category.value);
    posts.value = append ? [...posts.value, ...(result.items || [])] : result.items || [];
    total.value = result.total || 0;
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};
const changeSort = value => { sort.value = value; page.value = 1; load(); };
const changeCategory = event => { category.value = categories[event.detail.value] === '全部分类' ? '' : categories[event.detail.value]; page.value = 1; load(); };
const loadMore = () => { page.value += 1; load(true); };
const openPost = id => uni.navigateTo({ url: `/pages/community/detail?id=${id}` });
const goPublish = () => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  uni.navigateTo({ url: '/pages/community/publish' });
};
onShow(() => { page.value = 1; load(); });
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.community-page { max-width: 1280px; margin: 0 auto; }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 24px; margin: 28px 0; }
.title { color: $brand-primary; font-size: 40px; line-height: 1.1; font-weight: 900; }
.sub { margin-top: 10px; color: $text-secondary; font-size: 15px; }
.primary,.more { margin: 0; border-radius: 8px; font-weight: 900; }
.primary { height: 42px; line-height: 42px; padding: 0 22px; background: $brand-primary; color: #f5d392; }
.primary::after,.more::after { border: none; }
.filters { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 22px; }
.chip { padding: 10px 18px; border-radius: 999px; background: #fff; border: 1px solid #e7e0d4; color: $text-secondary; font-size: 14px; cursor: pointer; }
.chip.active { background: $brand-primary; color: #f5d392; border-color: $brand-primary; font-weight: 900; }
.state-card,.post-card { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.state-card { text-align: center; color: $text-secondary; padding: 80px 30px; }
.post-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 18px; }
.post-card { overflow: hidden; cursor: pointer; transition: transform .2s, box-shadow .2s; }
.post-card:hover { transform: translateY(-3px); box-shadow: $shadow-hover; }
.cover { height: 190px; overflow: hidden; background: #f7f4ee; }
.cover image { width: 100%; height: 100%; }
.name-cover { height: 100%; display: flex; align-items: center; justify-content: center; color: #f5d392; background: linear-gradient(135deg,#17243b,#24324a); font-size: 34px; font-weight: 900; }
.post-body { padding: 20px; }
.post-meta,.post-foot { display: flex; justify-content: space-between; gap: 12px; color: $text-secondary; font-size: 12px; }
.post-title { margin-top: 12px; color: $brand-primary; font-size: 22px; font-weight: 900; line-height: 1.35; }
.candidate-line { margin-top: 12px; color: #9b6a20; background: #fffbf2; border: 1px solid #ead6ad; border-radius: 8px; padding: 8px 10px; font-size: 13px; }
.post-foot { margin-top: 18px; padding-top: 14px; border-top: 1px solid #eee7dc; }
.more { display: block; margin: 28px auto 0; height: 42px; line-height: 42px; padding: 0 32px; background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; }
@media (max-width: 980px) { .post-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 640px) { .page-head { flex-direction: column; align-items: stretch; } .post-grid { grid-template-columns: 1fr; } }
</style>
