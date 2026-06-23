// http/http.js

// 动态获取环境：开发模式连接本地后端，发行模式连接线上域名
const BASE_URL = "http://127.0.0.1:8000";

/**
 * 核心请求封装函数
 */
const request = (url, options = {}) => {
  // 每次请求前，动态获取最新的 token
  const token = uni.getStorageSync("token");
  const { silent = false, ...requestOptions } = options;
  
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      header: {
        "content-type": "application/json",
        "authorization": token ? "Bearer " + token : ""
      },
      ...requestOptions,
      success: (res) => {
        // HTTP 状态码 200 代表完全成功
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          // --- 核心修复：智能解析 FastAPI 的错误格式 ---
          let errorMsg = '服务器请求失败';
          
          if (res.data && Array.isArray(res.data.detail)) {
            // 捕获 Pydantic 数据校验 422 错误 (Array 格式)
            // 取第一条错误信息并展示
            errorMsg = res.data.detail[0].msg || '表单参数校验失败';
          } else if (res.data && typeof res.data.detail === 'string') {
            // 捕获我们自定义的 HttpException 错误 (String 格式)
            errorMsg = res.data.detail;
          }
          
          // 确保 title 绝对是字符串，防止前端崩溃红屏
          if (!silent) {
            uni.showToast({
              title: String(errorMsg),
              icon: 'none',
              duration: 3000
            });
          }
          
          // 将错误抛出，供业务层 catch 处理（比如用来关掉 loading 动画）
          reject(res.data);
        }
      },
      fail: (err) => {
        if (!silent) {
          uni.showToast({ title: '网络连接断开，请检查网络', icon: 'none' });
        }
        reject(err);
      }
    });
  });
};

/**
 * 专门处理文件上传的封装函数 (针对 RAG 私有知识库)
 */
const uploadFile = (url, filePath) => {
  const token = String(uni.getStorageSync("token") || '').trim();

  if (!token) {
    return Promise.reject({
      statusCode: 401,
      data: { detail: '请先登录后再上传文件' }
    });
  }

  const parseResponseData = (data) => {
    if (typeof data !== 'string') return data;
    try {
      return JSON.parse(data);
    } catch (e) {
      return { detail: data || '文件上传失败' };
    }
  };
  
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      filePath: filePath,
      name: 'file',
      header: {
        "Authorization": "Bearer " + token
      },
      success: (res) => {
        const data = parseResponseData(res.data);
        if (res.statusCode >= 200 && res.statusCode < 300) {
          // uni.uploadFile 返回的 data 是字符串格式的 JSON，需要手动 parse
          resolve(data);
        } else {
          reject({ ...res, data });
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};

// 导出所有后端接口
export default {
  // ================= 1. 账号鉴权接口 =================
  getEmailCode: (email) => request("/auth/code?email=" + email, { method: 'GET' }),
  register: (data) => request("/auth/register", { method: 'POST', data }),
  login: (data) => request("/auth/login", { method: 'POST', data }),
  
  // ================= 2. 智能体核心工作流 =================
  generateName: (data) => request("/names/generate", { method: 'POST', data }), // 首次起名 (无记忆)
  feedbackName: (data) => request("/names/feedback", { method: 'POST', data }), // 多轮微调 (带记忆 thread_id)
  
  // ================= 3. RAG 知识库接口 =================
  uploadKnowledge: (filePath) => uploadFile("/knowledge/upload", filePath),

  // ================= 4. 品牌视觉生成接口 =================
  generateVisual: (data) => request("/visual/generate", { method: 'POST', data }),
  getVisualStatus: (visualId) => request(`/visual/${visualId}`, { method: 'GET' }),
  createBrandKit: (data) => request('/visual/kits', { method: 'POST', data }),
  getBrandKit: (kitId) => request(`/visual/kits/${kitId}`, { method: 'GET' }),

  // ================= 5. 个人数字资产 =================
  saveNameAsset: (data) => request('/me/assets/names', { method: 'POST', data }),
  getNameAssets: (page = 1, pageSize = 20) => request(`/me/assets/names?page=${page}&page_size=${pageSize}`, { method: 'GET' }),
  deleteNameAsset: (assetId) => request(`/me/assets/names/${assetId}`, { method: 'DELETE' }),
  getVisualAssets: (page = 1, pageSize = 20) => request(`/me/assets/visuals?page=${page}&page_size=${pageSize}`, { method: 'GET' }),
  getMyProfile: () => request('/me/profile', { method: 'GET' }),
  updateMyProfile: (data) => request('/me/profile', { method: 'PUT', data }),
  getMembershipPackages: () => request('/membership/packages', { method: 'GET' }),
  createMembershipOrder: (packageId) => request('/membership/orders', { method: 'POST', data: { package_id: packageId } }),
  payMembershipOrder: (orderId) => request(`/membership/orders/${orderId}/pay`, { method: 'PUT' }),

  // ================= 6. 灵感社区 =================
  getCommunityPosts: (page = 1, sort = 'latest', category = '') => request(`/community/posts?page=${page}&page_size=20&sort=${sort}${category ? `&category=${encodeURIComponent(category)}` : ''}`, { method: 'GET' }),
  getCommunityPost: (postId) => request(`/community/posts/${postId}`, { method: 'GET' }),
  createCommunityPost: (data) => request('/community/posts', { method: 'POST', data }),
  voteCommunityPost: (postId, candidateId) => request(`/community/posts/${postId}/vote`, { method: 'PUT', data: { candidate_id: candidateId } }),
  removeCommunityVote: (postId) => request(`/community/posts/${postId}/vote`, { method: 'DELETE' }),
  getCommunityComments: (postId, page = 1) => request(`/community/posts/${postId}/comments?page=${page}&page_size=20`, { method: 'GET' }),
  addCommunityComment: (postId, content) => request(`/community/posts/${postId}/comments`, { method: 'POST', data: { content } }),
  reportCommunityContent: (data) => request('/community/reports', { method: 'POST', data }),

  // ================= 7. 专家市场 =================
  getExperts: (page = 1, expertType = '') => request(`/marketplace/experts?page=${page}&page_size=20${expertType ? `&expert_type=${expertType}` : ''}`, { method: 'GET' }),
  getExpert: (expertId) => request(`/marketplace/experts/${expertId}`, { method: 'GET' }),
  getExpertPackages: (expertType = '') => request(`/marketplace/packages${expertType ? `?expert_type=${expertType}` : ''}`, { method: 'GET' }),
  applyExpert: (data) => request('/marketplace/expert-application', { method: 'POST', data }),
  getMyExpertProfile: () => request('/marketplace/expert-application/me', { method: 'GET', silent: true }),
  createExpertOrder: (data) => request('/marketplace/orders', { method: 'POST', data }),
  getMyExpertOrders: (page = 1) => request(`/marketplace/orders?page=${page}&page_size=20`, { method: 'GET' }),
  payExpertOrder: (orderId) => request(`/marketplace/orders/${orderId}/pay`, { method: 'PUT' }),
  cancelExpertOrder: (orderId) => request(`/marketplace/orders/${orderId}/cancel`, { method: 'PUT' }),
  completeExpertOrder: (orderId) => request(`/marketplace/orders/${orderId}/complete`, { method: 'PUT' }),
  reviewExpertOrder: (orderId, data) => request(`/marketplace/orders/${orderId}/review`, { method: 'POST', data }),
  getExpertWorkOrders: (status = '') => request(`/marketplace/expert/orders?page=1&page_size=50${status ? `&status=${status}` : ''}`, { method: 'GET' }),
  acceptExpertOrder: (orderId) => request(`/marketplace/expert/orders/${orderId}/accept`, { method: 'PUT' }),
  rejectExpertOrder: (orderId, reason) => request(`/marketplace/expert/orders/${orderId}/reject`, { method: 'PUT', data: { reason } }),
  generateReportDraft: (orderId) => request(`/marketplace/expert/orders/${orderId}/report/draft`, { method: 'POST' }),
  saveExpertReport: (orderId, data) => request(`/marketplace/expert/orders/${orderId}/report`, { method: 'PUT', data }),
  submitExpertReport: (orderId, data) => request(`/marketplace/expert/orders/${orderId}/report/submit`, { method: 'PUT', data }),

  // ================= 8. 管理员后台接口 =================
  getAdminUsers: (page = 1, pageSize = 20, keyword = '') => request(`/admin/users?page=${page}&page_size=${pageSize}${keyword ? `&keyword=${encodeURIComponent(keyword)}` : ''}`, { method: 'GET' }),
  checkAdminAccess: () => request("/admin/users?page=1&page_size=1", { method: 'GET', silent: true }),
  toggleUserBan: (userId) => request(`/admin/users/${userId}/ban`, { method: 'PUT' }),
  resetAdminUserPassword: (userId, password) => request(`/admin/users/${userId}/password`, { method: 'PUT', data: { password } }),
  deleteAdminUser: (userId) => request(`/admin/users/${userId}`, { method: 'DELETE' }),
  giftAdminUserVip: (userId) => request(`/admin/marketplace/users/${userId}/gift-vip`, { method: 'POST' }),
  getAdminOrders: (page = 1, pageSize = 20) => request(`/admin/finance/orders?page=${page}&page_size=${pageSize}`, { method: 'GET' }),
  reviewRefund: (refundId, data) => request(`/admin/finance/refunds/${refundId}`, { method: 'PUT', data }),
  getAdminAgents: () => request("/admin/ai/agents", { method: 'GET' }),
  updateAdminAgent: (agentId, data) => request(`/admin/ai/agents/${agentId}`, { method: 'PUT', data }),
  upsertKnowledge: (data) => request("/admin/ai/knowledge", { method: 'POST', data }),
  getSensitiveLogs: (page = 1, pageSize = 20) => request(`/admin/audit/sensitive?page=${page}&page_size=${pageSize}`, { method: 'GET' }),
  getAdminExperts: (status = '') => request(`/admin/marketplace/experts?page=1&page_size=100${status ? `&status=${status}` : ''}`, { method: 'GET' }),
  reviewAdminExpert: (expertId, data) => request(`/admin/marketplace/experts/${expertId}/review`, { method: 'PUT', data }),
  getAdminServicePackages: () => request('/admin/marketplace/packages', { method: 'GET' }),
  createAdminServicePackage: (data) => request('/admin/marketplace/packages', { method: 'POST', data }),
  updateAdminServicePackage: (packageId, data) => request(`/admin/marketplace/packages/${packageId}`, { method: 'PUT', data }),
  getAdminCommunityReports: (status = 'PENDING') => request(`/admin/marketplace/reports?page=1&page_size=100&status=${status}`, { method: 'GET' }),
  moderateAdminReport: (reportId, data) => request(`/admin/marketplace/reports/${reportId}`, { method: 'PUT', data })
};
