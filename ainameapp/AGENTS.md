# ainameapp — AI 智能起名服务前端项目

## 项目概述
基于 `uni-app` 和 `Vue.js` 开发的 AI 智能起名服务前端应用。该前端项目对接了基于 FastAPI 和 LangGraph 的后端服务，旨在提供多平台的客户端体验（如 H5、微信小程序、App 等），包含用户认证、多轮对话起名交互（支持人名、企业名、宠物名场景）及 RAG 知识库文件上传等功能。

## 技术栈
- **前端框架**：`uni-app` (兼容 Vue 2 / Vue 3 语法)
- **页面路由配置**：`pages.json`
- **样式语言**：SCSS / `uni.scss`
- **网络请求**：自定义封装 `uni.request` 与 `uni.uploadFile`，支持全局 Token 注入和统一异常拦截 (FastAPI 原生 422 错误与业务异常)。
- **状态管理**：主要通过 `uni.getStorageSync` 与 `uni.setStorageSync` 实现本地 Token 和用户状态的持久化。

## 项目结构
```text
ainameapp/
├── main.js                  # Vue 实例挂载，区分 Vue 2 与 Vue 3 环境的入口文件
├── App.vue                  # 根组件，管理应用生命周期（onLaunch, onShow, onHide 等）
├── pages.json               # 页面路由与全局窗口外观配置文件（包含 index, login, register）
├── manifest.json            # 应用配置，包括 AppID、基础环境配置及各平台特有配置
├── uni.scss                 # 全局 SCSS 变量与样式定义
├── http/
│   └── http.js              # 全局请求接口封装：封装鉴权、API路由及异常拦截
├── pages/
│   ├── index/               # 首页及起名核心交互页面
│   ├── login/               # 登录页面
│   └── register/            # 注册及验证码获取页面
├── static/                  # 静态资源存放目录（图片、图标等）
└── unpackage/               # 编译后的各平台产物目录（无需提交到版本控制）
```

## 核心接口调用规划 (由 http.js 提供)
- **账号鉴权模块**：
  - `getEmailCode(email)`: 发送邮箱验证码
  - `register(data)`: 用户注册
  - `login(data)`: 密码登录，获取 JWT Token
- **智能体工作流模块**：
  - `generateName(data)`: 首次起名请求 (无上下文)
  - `feedbackName(data)`: 基于 `thread_id` 的多轮对话微调起名
- **RAG 知识库模块**：
  - `uploadKnowledge(filePath)`: 使用 `uni.uploadFile` 上传本地文件作为企业起名私有知识库

## 编码与开发规范
- **网络层解耦**：所有与后端的 HTTP 通信必须通过 `http/http.js` 中封装的方法进行，严禁在 `pages` 目录下直接调用 `uni.request`。
- **异常处理**：在 `http.js` 中已统一处理了后端的 `422 Unprocessable Entity` 和自定义异常。前端页面在调用接口时，应主要关注业务逻辑，通过 `.catch()` 处理特定异常或关闭 `loading` 状态。
- **全局鉴权**：接口请求会自动从本地存储中读取 `token` 并拼装在 Header `authorization: Bearer <token>` 中。涉及到需要登录的页面，应在页面 `onLoad` 或 `onShow` 时检查是否存在 Token，若无则拦截并跳转至 `/pages/login/login`。
- **跨平台兼容**：避免使用特定平台（如仅限微信小程序）的特有 API，尽量使用 `uni.xxx` 跨平台 API 进行开发；如必须使用，需通过条件编译 (`// #ifdef` 等) 隔离代码。
- **样式统一**：优先使用 `uni.scss` 中定义的全局变量控制主题色和基础样式，保证多端视觉效果一致。

## 当前开发状态与注意事项
- 基础的请求封装和 API 接口定义已完成，支持与本地 FastAPI 后端 (`192.168.150.29:8000`) 通信。部署生产环境前需将 `BASE_URL` 切换为生产域名。
- `pages.json` 已配置了 `index`、`login` 和 `register` 的路由。
- 当前正在或即将开发具体的页面 UI 交互和数据绑定，包括：
  - 登录/注册表单校验与交互。
  - 核心起名页面的对话聊天流 UI 以及表单控制参数传入。
  - 知识库上传页面的文件选择与状态反馈机制。
