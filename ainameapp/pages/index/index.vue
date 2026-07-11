<template>
  <view class="redirect-page"></view>
</template>

<script setup>
import { onLoad } from '@dcloudio/uni-app';

onLoad(() => {
  uni.redirectTo({ url: '/pages/home/index' });
});
</script>

<style scoped>
.redirect-page {
  min-height: 100vh;
  background: #f8f4ec;
}
</style>
