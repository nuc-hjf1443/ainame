<template>
  <view class="page">
    <view class="toolbar">
      <view><text class="title">灵感广场</text><text class="sub">让真实选择帮助好名字胜出</text></view>
      <button size="mini" class="primary" @click="goPublish">发布</button>
    </view>
    <view class="filters">
      <view v-for="item in sorts" :key="item.value" :class="['chip', sort === item.value ? 'active' : '']" @click="changeSort(item.value)">{{ item.label }}</view>
      <picker :range="categories" @change="changeCategory"><view class="chip">{{ category || '全部分类' }}</view></picker>
    </view>
    <view v-if="loading" class="state">正在加载...</view>
    <view v-else-if="!posts.length" class="state">还没有公开灵感</view>
    <view class="masonry">
      <view v-for="post in posts" :key="post.id" class="post" @click="openPost(post.id)">
        <image v-if="post.cover_image_url" :src="post.cover_image_url" mode="widthFix" class="cover" />
        <view v-else class="name-cover">{{ post.candidates[0]?.name }}</view>
        <view class="body">
          <view class="post-title">{{ post.title }}</view>
          <view class="candidate-line">{{ post.candidates.map(item => item.name).join(' · ') }}</view>
          <view class="meta"><text>{{ post.author_name }}</text><text>{{ post.vote_count }} 票 · {{ post.comment_count }} 建议</text></view>
        </view>
      </view>
    </view>
    <button v-if="posts.length < total" class="more" :loading="loadingMore" @click="loadMore">加载更多</button>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const posts = ref([]); const total = ref(0); const page = ref(1); const loading = ref(false); const loadingMore = ref(false);
const sort = ref('latest'); const category = ref('');
const sorts = [{ label: '最新', value: 'latest' }, { label: '热门', value: 'popular' }];
const categories = ['全部分类', '人名', '企业名', '宠物名'];
const load = async (append = false) => { append ? loadingMore.value = true : loading.value = true; try { const res = await http.getCommunityPosts(page.value, sort.value, category.value); posts.value = append ? [...posts.value, ...res.items] : res.items; total.value = res.total; } finally { loading.value = false; loadingMore.value = false; } };
const changeSort = value => { sort.value = value; page.value = 1; load(); };
const changeCategory = e => { category.value = categories[e.detail.value] === '全部分类' ? '' : categories[e.detail.value]; page.value = 1; load(); };
const loadMore = () => { page.value += 1; load(true); };
const openPost = id => uni.navigateTo({ url: `/pages/community/detail?id=${id}` });
const goPublish = () => { if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' }); uni.navigateTo({ url: '/pages/community/publish' }); };
onShow(() => { page.value = 1; load(); });
</script>

<style scoped>
.page{min-height:100vh;background:#f4f7f6;padding:28rpx;box-sizing:border-box}.toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:22rpx}.title{display:block;font-size:42rpx;font-weight:700;color:#102a2a}.sub{display:block;font-size:24rpx;color:#64748b;margin-top:6rpx}.primary{background:#0f766e;color:#fff;margin:0}.filters{display:flex;gap:12rpx;margin-bottom:24rpx}.chip{padding:12rpx 22rpx;background:#fff;border:1px solid #dbe5e3;border-radius:8rpx;font-size:24rpx;color:#475569}.chip.active{background:#134e4a;color:#fff}.masonry{column-count:2;column-gap:20rpx}.post{break-inside:avoid;background:#fff;margin-bottom:20rpx;border-radius:8rpx;overflow:hidden;border:1px solid #e2e8f0}.cover{width:100%;display:block}.name-cover{height:220rpx;display:flex;align-items:center;justify-content:center;background:#dff4ef;color:#134e4a;font-size:48rpx;font-weight:700}.body{padding:20rpx}.post-title{font-weight:700;color:#1f2937;font-size:28rpx}.candidate-line{font-size:24rpx;color:#0f766e;margin:12rpx 0;line-height:1.5}.meta{font-size:21rpx;color:#94a3b8;display:flex;justify-content:space-between;gap:10rpx}.state{text-align:center;padding:100rpx 0;color:#64748b}.more{background:#fff;color:#0f766e;margin:24rpx auto}.masonry .post{display:inline-block;width:100%}@media(max-width:600px){.masonry{column-count:1}}
</style>
