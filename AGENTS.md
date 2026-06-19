# ainame — AI 智能起名服务

## 项目概述
基于 FastAPI + LangGraph + DeepSeek 的 AI 智能起名后端服务，支持人名、企业名、宠物名场景，并集成 RAG 知识库与对话记忆。

## 技术栈
- **后端框架**：FastAPI (uvicorn)
- **AI / LLM**：LangChain + LangGraph + DeepSeek (`deepseek-chat`)
- **向量数据库**：ChromaDB (Ollama `nomic-embed-text` 嵌入)
- **关系数据库**：MySQL (aiomysql, SQLAlchemy async)
- **记忆持久化**：PostgreSQL (langgraph-checkpoint-postgres)
- **缓存引擎**：Redis (用于验证码存储, TTL 300s)
- **其他组件**：Alembic (数据库迁移), pwdlib (Argon2 密码哈希), JWT (双 token 认证), fastapi-mail (邮件发送)
- **环境及包管理**：Python >= 3.13, uv (pyproject.toml)

## 项目结构
```text
ainame/
├── main.py                  # FastAPI 入口，lifespan 管理工作流生命周期
├── dependencies.py          # FastAPI 依赖注入 (DB session, 邮件实例)
├── settings/
│   └── __init__.py          # 全局配置常量 (DB_URI, 邮箱, JWT 密钥)
├── models/
│   ├── __init__.py          # SQLAlchemy async engine, sessionmaker, Base
│   └── user.py              # User / EmailCode ORM 模型
├── schemas/
│   ├── name_schemas.py      # 起名生成与反馈相关 Pydantic 模型
│   └── user_schemas.py      # 用户注册、登录相关 Pydantic 模型
├── repository/
│   └── user_repo.py         # 封装 SQLAlchemy 数据访问层
├── routers/
│   ├── auth_router.py       # 认证相关路由：验证码、注册、登录
│   ├── name_router.py       # 起名相关路由：生成、反馈迭代
│   └── rag_router.py        # 知识库相关路由：文件上传
├── core/
│   ├── auth.py              # AuthHandler 单例 (JWT 编解码与依赖注入)
│   ├── workflow.py          # LangGraph 工作流核心逻辑
│   ├── nametools.py         # 早期链式起名实现 (供参考)
│   ├── rag_service.py       # RAG 服务 (文件解析、向量存储、语义检索)
│   ├── tools.py             # 外部工具 (如并发 WHOIS 域名查询)
│   ├── mailtools.py         # 邮件实例工厂
│   └── redisconfig.py       # Redis 异步客户端配置
├── alembictable/            # Alembic 异步迁移相关配置和脚本
├── chroma_rag_db/           # ChromaDB 向量数据持久化目录
├── uploads/                 # 用户上传的企业知识库文件存储目录
├── alembic.ini              # Alembic 配置文件
├── pyproject.toml           # 项目依赖和元数据配置
├── init_pg_memory.py        # PostgreSQL 记忆表初始化脚本
└── redisdemo.py             # Redis 使用示例 (开发参考)
```

## 编码规范
- **架构分层**：`routers/` 仅负责参数校验和请求编排；`core/` 负责 AI 等核心业务逻辑；`repository/` 封装数据库访问。
- **异步优先**：所有的 I/O 操作均要求使用 `async/await`，以发挥 FastAPI 并发优势。
- **依赖注入**：广泛使用 FastAPI `Depends()` 获取数据库 Session、Redis、邮件客户端以及用户认证信息。
- **类型安全**：采用 `Annotated` + `Field` 进行 Pydantic 模型字段验证。
- **结构化输出**：AI 节点中通过 `llm.with_structured_output` 强制要求 LLM 按照 Pydantic Schema 返回数据。
- **设计模式**：对核心工具（如 `AuthHandler`）使用单例模式 (`SingletonMeta` 元类)。

## 当前开发状态
- [x] 项目基础架构及 FastAPI 配置初始化完成
- [x] 基于 MySQL 的用户数据和验证码 Schema 设计与 Alembic 迁移配置完成
- [x] 用户注册、登录、邮件验证码认证模块开发完成
- [x] 核心 LangGraph 路由编排及工作流（支持人名、企业名、宠物名）开发完成
- [x] 基于 PostgreSQL 的多轮对话记忆功能开发完成
- [x] 域名并发查询工具集成至企业起名工作流完成
- [x] RAG 企业知识库的文件上传、解析和 ChromaDB 向量检索开发完成
- [x] 基于 Thread ID 的起名反馈迭代接口开发完成

## 注意事项
- `settings/__init__.py` 中含有硬编码的凭据（数据库 URI、API Key），生产部署前应改为从环境变量或 `.env` 加载，切勿将敏感信息提交到代码仓库。
- `core/nametools.py` 是早期实现，已被 `core/workflow.py` 替代，目前仅作为参考保留。
- CORS 在 `main.py` 内部被设定为 `allow_origins=["*"]` 全开放模式，部署上线前须针对具体前端域名收紧此配置。
- 在本地首次运行前，必须手动执行 `python init_pg_memory.py` 以建立 PostgreSQL 中必须的检查点表格。
- 需确保本地启动了 MySQL、PostgreSQL、Redis，并保持 Ollama 处于后台运行并具有 `nomic-embed-text` 模型。
