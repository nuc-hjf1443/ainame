# ainame 当前架构与技术栈

## 1. 文档说明

本文记录当前仓库已经存在的代码、ORM 模型和基础设施接入，不描述尚未实施的目标架构。

本文依据 `ainamebackend/models/`、`ainamebackend/routers/`、`ainamebackend/services/`、`ainamebackend/core/`、Alembic 迁移和依赖配置整理，未连接本地 MySQL 实例核验真实数据、表结构和当前迁移版本。数据库实际状态应以目标环境执行 Alembic 检查和数据库查询的结果为准。

## 2. 项目边界

### 2.1 前端

前端代码位于 `ainameapp/`，采用 uni-app + Vue 3，当前工程支持构建到 H5、App 以及微信、支付宝等小程序平台。

主要页面包括：

- AI 起名、登录和注册。
- AI 品牌工作台。
- 个人资料与名称、视觉资产。
- 灵感社区、候选名称投票和评论。
- 专家市场、专家详情和专家工作台。
- 用户、财务、AI 配置及 Marketplace 管理页面。

工程使用 uni-app 条件编译入口，同时保留 Vue 2 和 Vue 3 启动分支；`manifest.json` 当前指定 `vueVersion: 3`。仓库未配置独立的前端 `package.json`，主要按 HBuilderX/uni-app 工程方式组织。

### 2.2 后端

后端代码位于 `ainamebackend/`，主要目录职责如下：

| 位置 | 当前职责 |
| --- | --- |
| `ainamebackend/main.py` | FastAPI 应用入口、生命周期、路由注册、CORS 和静态资源挂载 |
| `ainamebackend/routers/` | HTTP 接口、参数编排、认证依赖和少量接口级校验 |
| `ainamebackend/services/` | 配额、订单过期、支付、视觉、品牌方案和 Marketplace AI 草稿等业务服务 |
| `ainamebackend/schemas/` | Pydantic 请求和响应模型 |
| `ainamebackend/models/` | SQLAlchemy ORM 模型、异步引擎和 Session 工厂 |
| `ainamebackend/repository/` | 用户、会员、资产、视觉、社区、Marketplace 和管理端数据访问 |
| `ainamebackend/core/` | LangGraph 命名、RAG、认证、AIGC 工具、缓存、邮件等基础能力 |
| `ainamebackend/alembictable/` | Alembic 异步迁移环境和版本脚本 |
| `ainamebackend/rag_worker.py` | RabbitMQ RAG 消费进程 |
| `ainamebackend/tests/` | 会员、视觉、Marketplace、社区和静态资源相关测试 |

当前项目已新增 `services/` 分层，`quota_service`、`marketplace_service`、`brand_kit_service`、`visual_service`、`alipay_service` 和 `order_expiry` 已归入该层。部分 Router 仍会直接调用 Repository 完成简单查询或接口级校验，后续复杂状态流转应继续下沉到 Service。

## 3. 当前技术栈

| 领域 | 当前实现 |
| --- | --- |
| 前端 | uni-app、Vue 3、JavaScript、Vue 单文件组件 |
| API | Python 3.13+、FastAPI、Uvicorn、Pydantic |
| ORM | SQLAlchemy async、`async_sessionmaker` |
| 业务数据库 | MySQL、`aiomysql` |
| 数据库迁移 | Alembic |
| AI 编排 | LangChain、LangGraph |
| 大模型 | DeepSeek `deepseek-chat` |
| 对话记忆 | PostgreSQL、LangGraph `AsyncPostgresSaver` |
| RAG | ChromaDB、Ollama `nomic-embed-text`、PyPDF |
| 缓存 | Redis async client |
| 消息队列 | RabbitMQ、`aio-pika`，当前仅用于 RAG 上传任务 |
| 视觉异步 | FastAPI `BackgroundTasks` |
| HTTP 客户端 | HTTPX |
| 认证 | JWT、pwdlib Argon2、FastAPI `Depends()` |
| 邮件 | fastapi-mail |
| 支付 | 支付宝沙箱电脑网站支付/手机网站支付、RSA2 签名/验签，保留本地 mock 测试后门 |
| 测试 | pytest、pytest-asyncio、aiosqlite |

当前运行依赖至少包括 MySQL、PostgreSQL、Redis、RabbitMQ、Ollama、支付宝沙箱配置和外部 DeepSeek/图像生成服务。ChromaDB 数据及上传文件当前以本地目录持久化。

## 4. 当前运行架构

```text
ainameapp
   │ HTTP
   ▼
FastAPI
   ├─ Routers → Services → Repository → MySQL
   ├─ Routers → Repository → MySQL
   ├─ LangGraph → DeepSeek
   │      └─ AsyncPostgresSaver → PostgreSQL
   ├─ 验证码与缓存 → Redis
   ├─ 支付 → 支付宝沙箱 H5 → notify/sync → MySQL 权益与订单状态
   ├─ RAG 上传 → RabbitMQ → rag_worker.py
   │                         └─ Ollama Embedding → ChromaDB
   └─ 视觉生成 → BackgroundTasks → 图像生成服务
```

### 4.1 命名工作流

- `core/workflow.py` 使用 LangGraph 编排命名流程。
- DeepSeek 通过结构化输出生成候选名称。
- 企业命名流程会调用 WHOIS 工具检查候选 `.com` 域名。
- `thread_id` 和 PostgreSQL checkpoint 用于反馈迭代和对话记忆。
- 命名请求当前仍在 FastAPI 请求周期内执行，没有进入统一任务队列。

### 4.2 RAG 工作流

- `/knowledge/upload` 接收文件并将任务发布到 RabbitMQ。
- `rag_worker.py` 消费任务，调用文件解析、Ollama embedding 和 ChromaDB 写入。
- 当前知识库文件和 ChromaDB 均使用本地持久化路径。

### 4.3 视觉工作流

- 品牌方案和视觉接口先创建 MySQL 记录。
- FastAPI `BackgroundTasks` 在应用进程中执行视觉生成。
- 视觉状态和图像路径写回 `brand_kits`、`brand_visuals`。
- 当前没有独立视觉 Worker，也未使用 ARQ。

### 4.4 会员、支付与退款

- 套餐、会员、订单、起名次数余额和每日配额保存在 MySQL。
- 命名和视觉请求会预扣配额，异常时执行退款补偿。
- 起名请求优先消耗当日免费或会员额度；当日额度用完后，可继续扣减用户已购买的起名次数余额。
- 会员与专家订单的主支付路径为支付宝沙箱支付；默认使用电脑网站支付，`ALIPAY_PAY_METHOD=wap` 时使用手机网站支付。支付结果以后端 `notify` 或主动 `sync` 查询为准。
- 原 `/pay` mock 支付接口仍保留为测试后门，必须通过 `ENABLE_MOCK_PAYMENT` 显式启用。
- 专家订单已支付后取消或拒单时，会调用支付宝沙箱退款；退款失败时保留原订单状态。

## 5. 当前 API 模块

| 路由前缀 | 当前能力 |
| --- | --- |
| `/auth` | 验证码、注册、登录 |
| `/names` | 起名、带 `thread_id` 起名、反馈迭代 |
| `/knowledge` | RAG 文件上传 |
| `/visual` | 品牌方案、视觉生成和状态查询 |
| `/me/assets` | 名称和视觉资产管理 |
| `/membership`、`/me/profile` | 套餐、模拟订单、会员与个人资料 |
| `/community` | 帖子、候选名称、投票、评论和举报 |
| `/marketplace` | 专家、服务包、订单、报告和评价 |
| `/payments` | 支付宝沙箱通知、回跳和主动同步 |
| `/admin` | 用户、财务、AI 配置、知识库和审计 |
| `/admin/marketplace` | 专家审核、服务包和报告管理 |

当前接口没有统一 `/api/v1` 版本前缀。根应用还保留基础示例和邮件测试接口，不应视为正式产品 API。

## 6. MySQL ORM 表结构

当前 ORM 共定义 26 张业务表。以下内容描述代码中的模型，不代表目标数据库已经全部执行对应迁移。

### 6.1 用户与认证（2 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `user` | 用户账号、密码哈希、角色、封禁和软删除状态 | `email` 唯一；其他业务表的主要用户外键 |
| `email_code` | 邮箱验证码记录 | 按邮箱保存验证码和创建时间 |

当前验证码接口同时使用 Redis；`email_code` 仍保留在 ORM 中，具体环境是否继续使用该表需以运行路径为准。

### 6.2 会员与财务（7 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `package_config` | 会员套餐、价格、有效期及每日配额 | `package_code` 唯一 |
| `orders` | 统一财务订单，保存支付渠道、系统交易号、支付宝交易号和退款信息 | 关联 `user`，可关联 `package_config`；`out_trade_no` 唯一 |
| `refund_audit` | 退款申请和审核 | 关联 `orders` |
| `api_bill` | 功能调用、Token 和配额消耗记录 | 关联 `user` |
| `user_memberships` | 用户当前会员权益 | `user_id` 唯一，关联 `package_config` |
| `user_quota_balances` | 用户已购买的起名次数余额 | `user_id` 唯一；用于每日起名额度耗尽后的余额扣减 |
| `daily_quota_usage` | 用户每日命名和视觉使用量 | `user_id + usage_date` 唯一 |

### 6.3 名称与视觉资产（3 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `naming_assets` | 用户保存的候选名称、寓意、典故和域名结果 | 关联 `user`；`user_id + thread_id + name` 唯一 |
| `brand_kits` | 一键品牌方案和总体生成状态 | 关联 `user`，可关联 `naming_assets`，并通过 `thread_id` 对应命名会话 |
| `brand_visuals` | Logo、名片等具体视觉变体 | 关联 `user` 和可选 `brand_kits`；保存任务、路径、错误及退款状态 |

### 6.4 Marketplace（5 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `expert_profiles` | 专家资料和审核状态 | 每个 `user` 最多一个专家资料 |
| `expert_service_packages` | 专家服务类型、价格和交付周期 | 按专家类型配置，不直接绑定单个专家 |
| `expert_service_orders` | 专家服务订单和交付状态 | 关联财务订单、客户、专家、服务包和名称资产 |
| `expert_reports` | 专家分析报告 | 每个服务订单最多一份报告 |
| `expert_reviews` | 客户对专家服务的评分和评价 | 每个服务订单最多一条评价 |

`expert_service_orders.finance_order_id` 将专家业务订单与通用 `orders` 财务订单一对一关联。

### 6.5 社区（5 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `community_posts` | 灵感投票帖子 | 关联作者，可关联 `brand_visuals` 作为封面 |
| `community_candidates` | 帖子中的候选名称 | 关联帖子，可关联 `naming_assets` |
| `community_votes` | 用户投票 | `post_id + user_id` 唯一，即每帖每用户一票 |
| `community_comments` | 帖子评论 | 关联帖子和用户 |
| `community_reports` | 对帖子或评论的举报与审核 | 关联举报人和可选审核人；目标使用类型和 ID 表示 |

删除社区帖子时，候选和投票外键配置了级联删除；其他关联的实际删除行为应结合数据库约束和 Repository 逻辑确认。

### 6.6 AI 资产与配置（2 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `agent_config` | 智能体名称、Prompt、模型和温度配置 | `agent_key` 唯一 |
| `knowledge_base` | 知识库文件元数据和状态 | 当前记录文件名及本地路径 |

### 6.7 合规审计（2 张）

| 表 | 用途 | 主要关系或约束 |
| --- | --- | --- |
| `sensitive_word_interception` | 敏感词命中输入和命中词记录 | 可关联 `user` |
| `ai_content_patrol` | AI 生成内容巡检和违规状态 | 可关联 `user` |

## 7. 主要数据关系

```text
user
 ├─ orders ─ package_config
 │    ├─ refund_audit
 │    └─ expert_service_orders
 ├─ user_memberships ─ package_config
 ├─ user_quota_balances
 ├─ daily_quota_usage
 ├─ naming_assets ─ expert_service_orders
 ├─ naming_assets ─ brand_kits ─ brand_visuals
 ├─ expert_profiles ─ expert_service_orders
 └─ community_posts
       ├─ community_candidates ─ naming_assets
       ├─ community_votes
       └─ community_comments

expert_service_orders
 ├─ expert_reports
 └─ expert_reviews
```

模型主要通过显式外键维护关系，但多数模型没有声明 SQLAlchemy `relationship()`；Repository 当前主要通过显式查询和联表获取业务数据。

## 8. 当前实现与目标规划的差异

| 领域 | 当前实现 | 年度规划目标 |
| --- | --- | --- |
| 业务数据库 | MySQL | PostgreSQL |
| LangGraph 记忆 | PostgreSQL | 保留 PostgreSQL，并与业务数据进行 schema 隔离 |
| 异步队列 | RAG 使用 RabbitMQ；视觉使用 `BackgroundTasks`；命名同步执行 | Redis + ARQ 统一任务平台 |
| 业务分层 | 已新增 `services/`，主要配额、支付、订单过期、视觉和 Marketplace AI 草稿逻辑已迁入；仍保留少量 Router → Repository 简单路径 | 完整 Router → Service → Repository 分层 |
| API 版本 | 无统一版本前缀 | `/api/v1` |
| 文件存储 | 本地 `uploads/` 和 ChromaDB 目录 | S3 兼容对象存储和受管理持久卷 |
| 域名校验 | 自建 `.com` WHOIS 查询 | 稳定供应商，覆盖 `.com/.cn/.ai` |
| 商标校验 | 未实现 | 接入一家供应商进行风险预估 |
| 支付 | 支付宝沙箱支付为主路径，保留本地状态模拟测试后门 | 第一年度仍为支付宝沙箱/模拟支付，不包含真实资金交易 |
| Marketplace | 已有基础数据模型、接口和前端页面 | 后半年补齐审核、交付、申诉和试运营闭环 |
| B 端 PaaS | 未实现 | 第一年度只预留接口设计，不正式上线 |
| Growth | 未实现 | 第一年度不建设佣金结算 |

## 9. 当前已知工程约束

- MySQL 业务库和 PostgreSQL checkpoint 同时存在，开发环境必须分别配置和维护。
- RAG Worker 依赖 RabbitMQ、Ollama 和本地 ChromaDB，缺少任一组件都会影响知识库上传处理。
- 视觉任务依赖 FastAPI 进程内 `BackgroundTasks`，进程退出后缺少可靠恢复能力。
- 命名调用处于 HTTP 请求周期内，模型延迟会直接影响接口响应时间。
- CORS 当前为开放配置，适合本地开发，不应直接用于正式部署。
- 本地上传目录与 ChromaDB 不适合多实例共享。
- 支付宝沙箱 `notify_url` 必须是支付宝可访问的公网地址；本地联调需要内网穿透或测试域名。
- 当前表中大量业务状态使用字符串表示，状态转换规则主要由 Service 和 Repository 共同约束，少量接口仍在 Router 中做入口级判断。

## 10. 文档维护规则

- 本文只描述已经存在的实现；未来设计写入 `PROJECT_ROADMAP.md`。
- 新增 ORM 表、基础设施或主要路由后，应同步更新对应章节。
- 数据库结构发生变化时，以 Alembic 迁移为准，并同步更新表数量和关系说明。
- 文档不得记录数据库 URI、密码、API Key、Token、证书或真实用户数据。
