<template>
  <view class="page">
    <view class="title">发布名字投票</view>
    <input class="field" v-model="form.title" placeholder="给这组名字一个标题" />
    <textarea class="area" v-model="form.description" placeholder="补充背景和希望网友关注的方向" />
    <picker :range="categories" @change="e=>form.category=categories[e.detail.value]"><view class="field">分类：{{ form.category }}</view></picker>
    <view class="section">选择 2–5 个候选名</view>
    <view v-for="item in available" :key="item.key" :class="['asset',selectedKeys.includes(item.key)?'selected':'']" @click="toggle(item)">
      <text class="name">{{ item.name }}</text><text>{{ item.moral }}</text>
    </view>
    <view class="section">封面 Logo（可选）</view>
    <picker :range="visualLabels" @change="e=>form.cover_visual_id=visuals[e.detail.value-1]?.id||null"><view class="field">{{ selectedVisualLabel }}</view></picker>
    <button class="primary" :loading="loading" @click="publish">发布到广场</button>
  </view>
</template>
<script setup>
import {computed,ref} from 'vue';import{onLoad}from'@dcloudio/uni-app';import http from '@/http/http.js';
const categories=['人名','企业名','宠物名'];const form=ref({title:'',description:'',category:'人名',cover_visual_id:null});const available=ref([]),visuals=ref([]),selectedKeys=ref([]),loading=ref(false);
const visualLabels=computed(()=>['不使用封面',...visuals.value.map(v=>`${v.name} · ${v.status}`)]);const selectedVisualLabel=computed(()=>form.value.cover_visual_id?visualLabels.value[visuals.value.findIndex(v=>v.id===form.value.cover_visual_id)+1]:'不使用封面');
const toggle=item=>{const i=selectedKeys.value.indexOf(item.key);if(i>=0)selectedKeys.value.splice(i,1);else if(selectedKeys.value.length<5)selectedKeys.value.push(item.key)};
const publish=async()=>{if(!form.value.title.trim()||selectedKeys.value.length<2)return uni.showToast({title:'请填写标题并选择至少2个名字',icon:'none'});loading.value=true;try{const candidates=available.value.filter(i=>selectedKeys.value.includes(i.key)).map(i=>({source_asset_id:i.id||null,name:i.name,moral:i.moral||'',reference:i.reference||''}));const post=await http.createCommunityPost({...form.value,candidates});uni.redirectTo({url:`/pages/community/detail?id=${post.id}`})}finally{loading.value=false}};
onLoad(async()=>{const current=uni.getStorageSync('publishCandidates')||[];const assets=(await http.getNameAssets()).items;available.value=[...current.map((i,index)=>({...i,key:`current-${index}`})),...assets.map(i=>({...i,key:`asset-${i.id}`}))];visuals.value=(await http.getVisualAssets()).items.filter(v=>v.status==='SUCCESS');selectedKeys.value=current.slice(0,5).map((_,i)=>`current-${i}`);if(current[0]?.category)form.value.category=current[0].category});
</script>
<style scoped>
.page{padding:30rpx;background:#f5f7f6;min-height:100vh;box-sizing:border-box}.title{font-size:40rpx;font-weight:700;margin-bottom:24rpx}.field,.area{background:#fff;border:1px solid #dbe5e3;border-radius:8rpx;padding:22rpx;margin-bottom:16rpx;box-sizing:border-box;width:100%}.area{height:150rpx}.section{font-weight:700;margin:28rpx 0 14rpx}.asset{background:#fff;padding:20rpx;border:1px solid #e2e8f0;border-radius:8rpx;margin-bottom:12rpx;display:flex;gap:20rpx;align-items:center}.asset.selected{border-color:#0f766e;background:#ecfdf8}.name{font-size:32rpx;font-weight:700;color:#134e4a}.primary{background:#0f766e;color:#fff;margin-top:30rpx;border-radius:8rpx}
</style>
