<template>
  <view class="page" v-if="post">
    <view class="header"><text class="tag">{{ post.category }}</text><text class="author">{{ post.author_name }}</text></view>
    <view class="title">{{ post.title }}</view><view class="desc">{{ post.description }}</view>
    <image v-if="post.cover_image_url" :src="post.cover_image_url" mode="widthFix" class="cover" />
    <view class="vote-title">选择你最认可的名字</view>
    <view v-for="item in post.candidates" :key="item.id" :class="['candidate', post.my_vote_candidate_id === item.id ? 'selected' : '']" @click="vote(item.id)">
      <view><text class="name">{{ item.name }}</text><text class="moral">{{ item.moral }}</text></view><text>{{ item.vote_count }} 票</text>
    </view>
    <button v-if="post.my_vote_candidate_id" size="mini" class="link" @click="removeVote">取消投票</button>
    <view class="comments"><view class="section-title">网友建议</view>
      <view class="composer"><input v-model="comment" placeholder="写下你的建议"/><button size="mini" @click="sendComment">发送</button></view>
      <view v-for="item in comments" :key="item.id" class="comment"><text class="username">{{ item.username }}</text><text>{{ item.content }}</text></view>
      <view v-if="!comments.length" class="empty">还没有建议</view>
    </view>
    <button size="mini" class="report" @click="report">举报内容</button>
  </view>
</template>
<script setup>
import { ref } from 'vue'; import { onLoad } from '@dcloudio/uni-app'; import http from '@/http/http.js';
const id=ref(0),post=ref(null),comments=ref([]),comment=ref(''); const requireLogin=()=>{if(!uni.getStorageSync('token')){uni.navigateTo({url:'/pages/login/login'});return false}return true};
const load=async()=>{post.value=await http.getCommunityPost(id.value);comments.value=(await http.getCommunityComments(id.value)).items};
const vote=async candidateId=>{if(!requireLogin())return;post.value=await http.voteCommunityPost(id.value,candidateId)};
const removeVote=async()=>{await http.removeCommunityVote(id.value);await load()};
const sendComment=async()=>{if(!requireLogin()||!comment.value.trim())return;await http.addCommunityComment(id.value,comment.value.trim());comment.value='';await load()};
const report=()=>{if(!requireLogin())return;uni.showModal({title:'举报内容',editable:true,placeholderText:'请说明原因',success:async r=>{if(r.confirm)await http.reportCommunityContent({target_type:'POST',target_id:id.value,reason:'OTHER',detail:r.content||''})}})};
onLoad(q=>{id.value=Number(q.id);load()});
</script>
<style scoped>
.page{min-height:100vh;background:#f6f8f7;padding:30rpx;box-sizing:border-box}.header{display:flex;justify-content:space-between;color:#64748b;font-size:24rpx}.tag{color:#0f766e}.title{font-size:42rpx;font-weight:700;color:#17252a;margin:24rpx 0 12rpx}.desc{color:#64748b;line-height:1.7}.cover{width:100%;margin:24rpx 0;border-radius:8rpx}.vote-title,.section-title{font-weight:700;font-size:30rpx;margin:30rpx 0 16rpx}.candidate{background:#fff;border:1px solid #dbe5e3;padding:22rpx;margin-bottom:14rpx;border-radius:8rpx;display:flex;justify-content:space-between;align-items:center}.candidate.selected{border-color:#0f766e;background:#ecfdf8}.name{font-size:34rpx;font-weight:700;display:block}.moral{font-size:23rpx;color:#64748b;display:block;margin-top:6rpx}.link,.report{background:#fff;color:#64748b;margin:14rpx 0}.comments{margin-top:38rpx}.composer{display:flex;background:#fff;padding:12rpx;border-radius:8rpx}.composer input{flex:1;padding:12rpx}.comment{background:#fff;padding:20rpx;border-bottom:1px solid #eef2f7;display:flex;gap:18rpx}.username{color:#0f766e;font-weight:600}.empty{text-align:center;color:#94a3b8;padding:40rpx}
</style>
