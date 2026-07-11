<template>
  <DashboardLayout currentMenu="community">
    <view class="detail-page" v-if="post">
      <view class="breadcrumb">灵感社区 〉 投票详情</view>
      <view class="layout">
        <view class="main">
          <view class="post-card">
            <view class="author-row">
              <view class="avatar">{{ post.author_name?.slice(0,1) || '用' }}</view>
              <view><view class="author">{{ post.author_name }}</view><view class="muted">{{ formatTime(post.created_time) }} · 发布于 {{ post.category }}</view></view>
              <button class="more" @click="reportPost">更多</button>
            </view>
            <view class="post-title">{{ post.title }}</view>
            <view class="post-desc">{{ post.description || '邀请大家一起选择更适合的名字。' }}</view>
            <view class="tag">{{ post.category }}</view>
          </view>

          <view class="vote-card">
            <view class="section-head"><view class="section-title">候选名称投票</view><text>单选 · {{ post.vote_count }}人参与</text></view>
            <view class="candidate-grid">
              <view v-for="(item,index) in post.candidates" :key="item.id" :class="['candidate', post.my_vote_candidate_id === item.id ? 'selected' : '']" @click="vote(item.id)">
                <view class="candidate-rank">{{ index + 1 }}</view>
                <view class="candidate-name">{{ item.name }}</view>
                <view class="candidate-moral">{{ item.moral || '暂无说明' }}</view>
                <view class="mini-bar"><view :style="{ width: percent(item.vote_count) + '%' }"></view></view>
                <view class="percent">{{ percent(item.vote_count) }}%（{{ item.vote_count }}票）</view>
              </view>
            </view>
          </view>

          <view class="result-card">
            <view class="section-title">投票结果分布 <text>{{ post.vote_count }}人参与</text></view>
            <view v-for="item in post.candidates" :key="`bar-${item.id}`" class="bar-row">
              <text>{{ item.name }}</text>
              <view class="bar"><view :style="{ width: percent(item.vote_count) + '%' }"></view></view>
              <strong>{{ percent(item.vote_count) }}%</strong>
              <text>({{ item.vote_count }}票)</text>
            </view>
          </view>

          <view class="comment-card">
            <view class="section-title">精彩评论 <text>{{ comments.length }}</text></view>
            <view v-for="comment in comments" :key="comment.id" class="comment">
              <view class="avatar small">{{ comment.username?.slice(0,1) || '评' }}</view>
              <view><view class="comment-meta">{{ comment.username }} · {{ formatTime(comment.created_time) }}</view><view class="comment-text">{{ comment.content }}</view></view>
            </view>
            <view class="comment-input">
              <input v-model="commentInput" placeholder="写下你的评论..." />
              <button class="dark" @click="submitComment">发表评论</button>
            </view>
          </view>
        </view>

        <view class="side">
          <view class="side-card">
            <view class="section-title">帖子信息</view>
            <view class="info-row"><text>发布时间</text><strong>{{ formatTime(post.created_time) }}</strong></view>
            <view class="info-row"><text>所属行业</text><strong>{{ post.category }}</strong></view>
            <view class="info-row"><text>投票状态</text><strong>{{ post.my_vote_candidate_id ? '已投票' : '进行中' }}</strong></view>
            <view class="info-row"><text>参与人数</text><strong>{{ post.vote_count }}人</strong></view>
          </view>
          <view class="side-card">
            <view class="section-title">热门标签</view>
            <view class="tags"><text v-for="item in tags" :key="item">{{ item }}</text></view>
          </view>
          <view class="side-card related">
            <view class="section-head"><view class="section-title">相关帖子</view><text @click="goCommunity">查看更多</text></view>
            <view v-for="item in related" :key="item.title" class="related-row">
              <view class="thumb">{{ item.title.slice(0,1) }}</view>
              <view><text>{{ item.title }}</text><text>{{ item.meta }}</text></view>
            </view>
          </view>
          <view class="cta-card">
            <view class="cta-title">发起我的投票</view>
            <view class="muted">有选择困难？让社区帮你决定。</view>
            <button class="dark" @click="goPublish">去发起投票</button>
          </view>
        </view>
      </view>
    </view>
  </DashboardLayout>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import DashboardLayout from '@/components/DashboardLayout/DashboardLayout.vue';
import http from '@/http/http.js';

const postId = ref(null);
const post = ref(null);
const comments = ref([]);
const commentInput = ref('');
const tags = ['科技', '品牌命名', '创业', '互联网', 'SaaS', '国际化'];
const related = [
  { title: '想做一个AI工具产品，帮我想个品牌名', meta: '38人参与 · 86条评论' },
  { title: '教育行业品牌命名求建议', meta: '54人参与 · 32条评论' },
  { title: '医疗健康品牌，大家帮忙参考下', meta: '41人参与 · 28条评论' }
];
const load = async () => {
  post.value = await http.getCommunityPost(postId.value);
  const result = await http.getCommunityComments(postId.value, 1);
  comments.value = result.items || [];
};
const percent = count => post.value?.vote_count ? Math.round(count / post.value.vote_count * 100) : 0;
const formatTime = value => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
};
const vote = async candidateId => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  post.value = await http.voteCommunityPost(postId.value, candidateId);
};
const submitComment = async () => {
  const content = commentInput.value.trim();
  if (!content) return;
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  await http.addCommunityComment(postId.value, content);
  commentInput.value = '';
  await load();
};
const reportPost = async () => {
  if (!uni.getStorageSync('token')) return uni.navigateTo({ url: '/pages/login/login' });
  await http.reportCommunityContent({ target_type: 'POST', target_id: postId.value, reason: 'OTHER', detail: '用户举报' });
  uni.showToast({ title: '已提交举报', icon: 'none' });
};
const goPublish = () => uni.navigateTo({ url: '/pages/community/publish' });
const goCommunity = () => uni.redirectTo({ url: '/pages/community/index' });
onLoad(query => { postId.value = Number(query.id || 0); load(); });
</script>

<style lang="scss" scoped>
@import "@/uni.scss";
.detail-page { max-width: 1280px; margin: 0 auto; }
.breadcrumb { color: $text-secondary; font-size: 13px; margin: 8px 0 18px; }
.layout { display: grid; grid-template-columns: minmax(0,1fr) 320px; gap: 18px; align-items: start; }
.post-card,.vote-card,.result-card,.comment-card,.side-card,.cta-card { background: rgba(255,255,255,.96); border: 1px solid #e7e0d4; border-radius: 10px; box-shadow: $shadow-soft; }
.post-card,.vote-card,.result-card,.comment-card,.side-card,.cta-card { padding: 24px; margin-bottom: 14px; }
.author-row { display: grid; grid-template-columns: 48px minmax(0,1fr) auto; gap: 14px; align-items: center; }
.avatar { width: 48px; height: 48px; border-radius: 50%; background: $brand-primary; color: #f5d392; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.avatar.small { width: 36px; height: 36px; }
.author,.section-title { color: $brand-primary; font-weight: 900; }
.muted,.section-head>text { color: $text-secondary; font-size: 13px; }
.more,.dark { margin: 0; border-radius: 8px; font-weight: 900; }
.more { height: 34px; line-height: 32px; padding: 0 14px; background: #fff; color: $brand-primary; border: 1px solid #e7e0d4; }
.more::after,.dark::after { border: none; }
.post-title { margin-top: 22px; color: $brand-primary; font-size: 30px; font-weight: 900; }
.post-desc { color: #52647f; line-height: 1.8; margin-top: 10px; }
.tag { display: inline-block; margin-top: 14px; padding: 6px 12px; border-radius: 6px; background: #fffbf2; color: #9b6a20; font-size: 13px; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.section-title { font-size: 18px; }
.section-title text { color: $text-secondary; margin-left: 8px; font-size: 13px; }
.candidate-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-top: 18px; }
.candidate { border: 1px solid #e7e0d4; border-radius: 10px; padding: 18px; cursor: pointer; }
.candidate.selected { border-color: $brand-gold; background: #fffbf2; }
.candidate-rank { width: 24px; height: 24px; border-radius: 50%; background: #e7e0d4; color: $brand-primary; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.candidate.selected .candidate-rank { background: $brand-gold; color: #fff; }
.candidate-name { margin-top: 12px; color: $brand-primary; font-size: 22px; font-weight: 900; }
.candidate-moral { margin-top: 8px; min-height: 42px; color: $text-secondary; font-size: 13px; line-height: 1.6; }
.mini-bar,.bar { height: 8px; background: #eef0f3; border-radius: 999px; overflow: hidden; }
.mini-bar { margin-top: 14px; }
.mini-bar view,.bar view { height: 100%; background: linear-gradient(90deg,$brand-primary,$brand-gold); }
.percent { margin-top: 10px; color: $brand-primary; font-size: 13px; text-align: center; font-weight: 900; }
.bar-row { display: grid; grid-template-columns: 100px minmax(0,1fr) 52px 70px; gap: 12px; align-items: center; margin-top: 16px; color: $brand-primary; font-size: 14px; }
.bar-row strong { color: #9b6a20; }
.comment { display: grid; grid-template-columns: 36px minmax(0,1fr); gap: 12px; padding: 16px 0; border-bottom: 1px solid #eee7dc; }
.comment-meta { color: $brand-primary; font-size: 13px; font-weight: 900; }
.comment-text { color: #52647f; margin-top: 6px; line-height: 1.7; }
.comment-input { display: grid; grid-template-columns: minmax(0,1fr) 120px; gap: 12px; margin-top: 16px; }
input { height: 42px; box-sizing: border-box; border: 1px solid #e7e0d4; border-radius: 8px; padding: 0 14px; background: #fbfaf7; }
.dark { height: 42px; line-height: 42px; background: $brand-primary; color: #f5d392; padding: 0 18px; }
.info-row { display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; }
.info-row text { color: $text-secondary; font-size: 13px; }
.info-row strong { color: $brand-primary; font-size: 13px; text-align: right; }
.tags { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; }
.tags text { padding: 7px 10px; border-radius: 6px; border: 1px solid #ead6ad; color: #9b6a20; background: #fffbf2; font-size: 12px; }
.related-row { display: grid; grid-template-columns: 48px minmax(0,1fr); gap: 12px; padding: 12px 0; border-bottom: 1px solid #eee7dc; }
.thumb { width: 48px; height: 42px; border-radius: 8px; background: $brand-primary; color: #f5d392; display: flex; align-items: center; justify-content: center; font-weight: 900; }
.related-row text:first-child { display: block; color: $brand-primary; font-size: 13px; font-weight: 900; }
.related-row text:last-child { display: block; color: $text-secondary; font-size: 12px; margin-top: 4px; }
.cta-card { background: #fffbf2; border-color: #ead6ad; }
.cta-title { color: $brand-primary; font-size: 20px; font-weight: 900; }
.cta-card .dark { width: 100%; margin-top: 16px; }
@media (max-width: 1080px) { .layout { grid-template-columns: 1fr; } .side { display: none; } }
@media (max-width: 760px) { .candidate-grid { grid-template-columns: 1fr; } .bar-row { grid-template-columns: 1fr; } .comment-input { grid-template-columns: 1fr; } }
</style>
