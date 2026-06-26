<script setup>
const applicationReady = true;
</script>

<style>
/* 引入现代字体 (如果部署可用可引入网络字体，此处优先使用系统自带的现代无衬线字体栈) */
page, body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #F8F9FA;
  margin: 0;
  padding: 0;
  color: #1A1A1A;
}

/* 隐藏滚动条增强沉浸感 (针对 Webkit) */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #E5E7EB;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #D1D5DB;
}
</style>
