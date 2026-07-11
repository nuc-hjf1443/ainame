<script setup>
const applicationReady = true;
</script>

<style>
/* 引入现代字体 (如果部署可用可引入网络字体，此处优先使用系统自带的现代无衬线字体栈) */
page, body {
  font-family: 'Inter', 'Noto Serif SC', 'Songti SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #F7F4EE;
  margin: 0;
  padding: 0;
  color: #17243B;
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
  background: #D8DDE6;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #C79A4B;
}
</style>
