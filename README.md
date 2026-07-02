# ainame

AI 起名与品牌资产管理项目，包含 uni-app 前端和 FastAPI 后端。

## 项目结构

```text
.
├── ainameapp/        # 前端：uni-app + Vue 3
├── ainamebackend/    # 后端：FastAPI、SQLAlchemy、Alembic、RAG、支付等
├── design/           # 本地设计稿，默认不纳入 Git
├── docs/             # 本地文档，默认不纳入 Git
├── .gitignore
└── README.md
```

## 后端

后端代码位于 `ainamebackend/`。

主要目录：

- `main.py`：FastAPI 应用入口
- `routers/`：接口路由
- `schemas/`：Pydantic 请求和响应模型
- `models/`：SQLAlchemy ORM 模型
- `repository/`：数据库访问层
- `core/`：业务服务、认证、RAG、支付、视觉生成等核心逻辑
- `alembictable/`：Alembic 数据库迁移
- `tests/`：后端测试
- `scripts/`：辅助脚本

本地启动示例：

```powershell
cd ainamebackend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

运行测试：

```powershell
python -m pytest
```

依赖文件：

- `pyproject.toml`：项目主依赖配置
- `requirements.txt`：pip/Docker 可用依赖清单
- `uv.lock`：uv 锁文件

## 前端

前端代码位于 `ainameapp/`，按 HBuilderX/uni-app 项目方式组织。

接口基地址当前在：

```text
ainameapp/http/http.js
```

默认后端地址为：

```text
http://127.0.0.1:8000
```

## 环境配置

后端本地环境变量文件：

```text
ainamebackend/.env
```

示例文件：

```text
ainamebackend/.env.example
```

注意：

- `.env` 不应提交到 Git
- `certs/` 下的证书和私钥不应提交到 Git
- 支付宝回调地址不能使用 `127.0.0.1` 给外部服务访问，开发调试可使用内网穿透公网 HTTPS 地址

## Docker

后端目录下提供容器化入口：

```text
ainamebackend/Dockerfile
ainamebackend/docker-compose.yml
```

使用前需要按实际环境核对数据库、Redis、PostgreSQL、RabbitMQ、支付回调域名等配置。

## Git 忽略策略

默认忽略：

- 本地环境变量和密钥
- Python 缓存、虚拟环境、测试缓存
- 前端构建产物
- 本地上传文件和向量库数据
- `docs/` 和 `design/` 本地资料目录
