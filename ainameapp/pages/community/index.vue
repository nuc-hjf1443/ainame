<template>
  <DashboardLayout currentMenu="community">
    <view class="content-inner">
      
      <view class="page-toolbar">
        <view class="toolbar-text">
          <text class="sub">让真实选择帮助好名字胜出</text>
        </view>
        <button class="primary-action-btn" @click="goPublish">
          + 发布灵感
        </button>
      </view>

      <view class="filters">
        <view class="filter-group">
          <view v-for="item in sorts" :key="item.value" 
                :class="['chip', sort === item.value ? 'active' : '']" 
                @click="changeSort(item.value)">
            {{ item.label }}
          </view>
        </view>
        
        <picker :range="categories" @change="changeCategory">
          <view class="chip category-picker">
            <text>{{ category || '全部分类' }}</text>
            <text class="arrow">▼</text>
          </view>
        </picker>
      </view>

      <view v-if="loading && page === 1" class="state-box">
        <text class="state-text">正在加载灵感...</text>
      </view>
      <view v-else-if="!posts.length" class="state-box">
        <text class="state-text">还没有公开灵感，快来发布第一篇吧！</text>
      </view>

      <view class="masonry" v-else>
        <view v-for="post in posts" :key="post.id" class="post-card" @click="openPost(post.id)">
          <image v-if="post.cover_image_url" :src="post.cover_image_url" mode="widthFix" class="cover" />
          <view v-else class="name-cover">
            {{ post.candidates[0]?.name || '灵感' }}
          </view>
          
          <view class="body">
            <view class="post-title">{{ post.title }}</view>
            <view class="candidate-line">{{ post.candidates.map(item => item.name).join(' · ') }}</view>
            <view class="meta">
              <text class="author">{{ post.author_name }}</text>
              <text class="stats">{{ post.vote_count }} 票 · {{ post.comment_count }} 建议</text>
            </view>
          </view>
        </view>
      </view>

      <button v-if="posts.length > 0 && posts.length < total" class="btn-more" :loading="loadingMore" @click="loadMore">
        加载更多
      </button>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';

const posts = ref([]); 
const total = ref(0); 
const page = ref(1); 
const loading = ref(false); 
const loadingMore = ref(false);
const sort = ref('latest'); 
const category = ref('');

const sorts = [
  { label: '最新', value: 'latest' }, 
  { label: '热门', value: 'popular' }
];
const categories = ['全部分类', '人名', '企业名', '宠物名'];

const load = async (append = false) => { 
  append ? loadingMore.value = true : loading.value = true; 
  try { 
    const res = await http.getCommunityPosts(page.value, sort.value, category.value); 
    posts.value = append ? [...posts.value, ...res.items] : res.items; 
    total.value = res.total; 
  } catch (e) {
    console.error(e);
  } finally { 
    loading.value = false; 
    loadingMore.value = false; 
  } 
};

const changeSort = value => { 
  sort.value = value; 
  page.value = 1; 
  load(); 
};

const changeCategory = e => { 
  category.value = categories[e.detail.value] === '全部分类' ? '' : categories[e.detail.value]; 
  page.value = 1; 
  load(); 
};

const loadMore = () => { 
  page.value += 1; 
  load(true); 
};

const openPost = id => uni.navigateTo({ url: `/pages/community/detail?id=${id}` });

const goPublish = () => { 
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' }); 
  uni.navigateTo({ url: '/pages/community/publish' }); 
};

onShow(() => { 
  page.value = 1; 
  load(); 
});
</script>

<style lang="scss" scoped>
/* 限制最大宽度，居中显示 */
.content-inner { 
  max-width: 1200px; 
  margin: 0 auto; 
}

/* 顶部操作栏 */
.page-toolbar {
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 32rpx;
  background: #FFFFFF; 
  padding: 24rpx 32rpx; 
  border-radius: 24rpx; 
  border: 1px solid #E5E7EB; 
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);

  .sub { 
    font-size: 28rpx; 
    color: #6B7280; 
    font-weight: 500; 
  }

  .primary-action-btn {
    background-color: #4F46E5; 
    color: #FFFFFF; 
    border-radius: 16rpx; 
    font-size: 28rpx; 
    font-weight: 600; 
    padding: 0 40rpx; 
    height: 80rpx; 
    line-height: 80rpx; 
    margin: 0; 
    border: none; 
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25); 
    transition: all 0.2s;
    &::after { border: none; }
    &:active { transform: translateY(2rpx); box-shadow: none; }
  }
}

/* 筛选区 */
.filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;

  .filter-group {
    display: flex;
    gap: 16rpx;
  }

  .chip {
    padding: 12rpx 32rpx;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 999px;
    font-size: 26rpx;
    font-weight: 500;
    color: #4B5563;
    cursor: pointer;
    transition: all 0.2s;

    &.active {
      background: #EEF2FF;
      color: #4F46E5;
      border-color: #A5B4FC;
      font-weight: 600;
    }
    
    &:hover:not(.active) {
      background: #F9FAFB;
    }
  }

  .category-picker {
    display: flex;
    align-items: center;
    gap: 8rpx;
    .arrow { font-size: 20rpx; color: #9CA3AF; }
  }
}

/* 空状态/加载状态 */
.state-box {
  background: #FFFFFF;
  border-radius: 24rpx;
  border: 1px solid #E5E7EB;
  padding: 100rpx 0;
  text-align: center;
  .state-text { color: #6B7280; font-size: 28rpx; }
}

/* 瀑布流布局 */
.masonry {
  column-count: 3; /* 桌面端默认3列 */
  column-gap: 32rpx;

  .post-card {
    break-inside: avoid;
    display: inline-block;
    width: 100%;
    background: #FFFFFF;
    margin-bottom: 32rpx;
    border-radius: 24rpx;
    overflow: hidden;
    border: 1px solid #E5E7EB;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;

    &:hover { 
      transform: translateY(-4rpx); 
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
    }

    .cover {
      width: 100%;
      display: block;
    }

    .name-cover {
      height: 280rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
      color: #4F46E5;
      font-size: 56rpx;
      font-weight: 800;
      letter-spacing: 4rpx;
    }

    .body {
      padding: 32rpx;

      .post-title {
        font-weight: 700;
        color: #111827;
        font-size: 30rpx;
        line-height: 1.4;
        margin-bottom: 16rpx;
      }

      .candidate-line {
        font-size: 26rpx;
        font-weight: 600;
        color: #4F46E5;
        margin-bottom: 24rpx;
        line-height: 1.5;
        background: #F5F3FF;
        padding: 8rpx 16rpx;
        border-radius: 8rpx;
        display: inline-block;
      }

      .meta {
        font-size: 24rpx;
        color: #6B7280;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #F3F4F6;
        padding-top: 24rpx;

        .author { font-weight: 500; color: #374151; }
      }
    }
  }
}

/* 加载更多按钮 */
.btn-more {
  background: #FFFFFF;
  color: #4F46E5;
  border: 1px solid #D1D5DB;
  border-radius: 16rpx;
  font-size: 28rpx;
  font-weight: 600;
  height: 88rpx;
  line-height: 88rpx;
  margin: 40rpx auto;
  max-width: 400rpx;
  transition: all 0.2s;
  
  &::after { border: none; }
  &:active { background: #F3F4F6; }
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .masonry { column-count: 2; }
}
@media (max-width: 600px) {
  .masonry { column-count: 1; }
  .page-toolbar { flex-direction: column; gap: 24rpx; align-items: stretch; text-align: center; }
  .filters { flex-direction: column; align-items: stretch; gap: 24rpx; }
  .filters .filter-group { justify-content: center; }
  .filters .chip { text-align: center; }
}
</style>
