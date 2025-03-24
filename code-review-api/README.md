# 代码审查系统 - 后端API服务

image.png<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0+-orange)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-blue)
![JWT](https://img.shields.io/badge/JWT-Auth-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

## 项目概述

代码审查系统后端API服务是基于FastAPI框架开发的RESTful API，为代码审查平台提供数据存储、业务逻辑处理和身份验证等核心功能。本服务支持多种数据库后端，内置完善的用户权限体系，可灵活适应各种开发团队的需求。

### 核心特性

- **高性能异步API**: 基于FastAPI的异步处理能力，支持高并发请求
- **多数据库支持**: 兼容MySQL、PostgreSQL、SQLite和Oracle数据库
- **JWT身份验证**: 安全的基于令牌的身份验证机制
- **RBAC权限控制**: 细粒度的基于角色的访问控制
- **自动生成API文档**: 内置Swagger和ReDoc接口文档
- **全面的数据验证**: 使用Pydantic进行数据验证和序列化
- **UTF-8字符集支持**: 完整支持中文等字符的存储和显示
- **可扩展性设计**: 模块化结构便于功能扩展

## 技术架构

- **Web框架**: FastAPI 0.95+ (基于Starlette和Pydantic)
- **ASGI服务器**: Uvicorn (用于开发) / Gunicorn (用于生产)
- **ORM**: SQLAlchemy 2.0，支持异步查询
- **数据迁移**: Alembic
- **身份验证**: JWT令牌 (PyJWT)
- **数据验证**: Pydantic 2.0
- **日志**: 标准库logging模块，可配置
- **测试**: Pytest

## 项目结构

```
code-review-api/
├── app/                # 应用代码
│   ├── api/            # API路由模块
│   │   ├── v1/         # API v1版本
│   │   │   ├── auth.py # 认证相关接口
│   │   │   ├── users.py # 用户管理接口
│   │   │   ├── projects.py # 项目管理接口
│   │   │   ├── issues.py # 问题管理接口
│   │   │   └── reviews.py # 审核管理接口
│   │   └── deps.py     # 依赖注入
│   ├── core/           # 核心功能
│   │   ├── config.py   # 配置加载
│   │   ├── security.py # 安全相关
│   │   └── logging.py  # 日志配置
│   ├── db/             # 数据库
│   │   ├── base.py     # 数据库基础设置
│   │   ├── session.py  # 会话管理
│   │   ├── MySQL.sql   # MySQL初始化脚本
│   │   ├── PostgreSQL.sql # PostgreSQL初始化脚本
│   │   ├── SQLite.sql  # SQLite初始化脚本
│   │   └── Oracle.sql  # Oracle初始化脚本
│   ├── models/         # 数据模型
│   ├── schemas/        # 数据模式
│   ├── crud/           # 数据操作
│   ├── services/       # 业务服务
│   └── main.py         # 应用入口
├── migrations/         # 数据库迁移文件
├── tests/              # 测试代码
├── alembic.ini         # Alembic配置
├── requirements.txt    # 依赖列表
└── README.md           # 文档
```

## 数据库支持

本服务支持四种主流数据库，每种数据库都有专门优化的初始化脚本：

- **MySQL**: 适合中大型项目，提供良好的性能和稳定性
- **PostgreSQL**: 支持高级数据类型和查询功能，适合复杂数据分析
- **SQLite**: 轻量级选项，适合小型团队或个人使用
- **Oracle**: 企业级数据库，适合大型企业环境

所有数据库脚本位于`app/db/`目录下。

### 数据库初始化

除了使用SQL脚本外，系统还提供了便捷的命令行工具初始化数据库：

```bash
# 切换到项目根目录
cd code-review-api

# 使用命令行工具初始化数据库（自动创建表结构和初始数据）
python -m app.main init-db
```

## 安装与部署

### 1. 本地开发环境

#### 前置条件
- Python 3.9+
- pip
- 支持的数据库之一

#### 安装步骤

```bash
# 克隆仓库
git clone [仓库地址]
cd code-review-api

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows使用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 创建.env文件
echo "DB_URL=mysql+pymysql://user:password@localhost:3306/codecheck?charset=utf8mb4" > .env
echo "JWT_SECRET=your_secure_jwt_secret" >> .env
echo "JWT_ALGORITHM=HS256" >> .env
echo "ACCESS_TOKEN_EXPIRE_MINUTES=60" >> .env

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 生产环境部署

```bash
# 安装生产依赖
pip install gunicorn

# 创建系统服务配置
sudo nano /etc/systemd/system/code-review-api.service

# 服务配置内容
[Unit]
Description=Code Review API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/code-review-api
ExecStart=/path/to/code-review-api/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target

# 启动服务
sudo systemctl enable code-review-api
sudo systemctl start code-review-api
```

### 3. Docker部署

```bash
# 构建镜像
docker build -t code-review-api:latest .

# 运行容器
docker run -d --name code-review-api \
  -p 8000:8000 \
  -e DB_URL="mysql+pymysql://user:password@db_host:3306/codecheck?charset=utf8mb4" \
  -e JWT_SECRET="your_secret_key" \
  code-review-api:latest
```

## API文档

API服务启动后，可以通过以下URL访问自动生成的API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 主要API端点

#### 认证相关

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/refresh | 刷新令牌 |

#### 用户管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/users | 获取用户列表 |
| GET | /api/v1/users/{user_id} | 获取用户详情 |
| POST | /api/v1/users | 创建新用户 |
| PUT | /api/v1/users/{user_id} | 更新用户信息 |
| DELETE | /api/v1/users/{user_id} | 删除用户 |

#### 项目管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/projects | 获取项目列表 |
| GET | /api/v1/projects/{project_id} | 获取项目详情 |
| POST | /api/v1/projects | 创建新项目 |
| PUT | /api/v1/projects/{project_id} | 更新项目信息 |
| DELETE | /api/v1/projects/{project_id} | 删除项目 |

#### 问题和审核管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/issues |
| POST | /api/v1/reviews | 创建代码审核 |
| GET | /api/v1/reviews/{review_id}/comments | 获取审核评论 |

## UTF-8字符集配置

为确保系统正确处理中文等多语言字符，需要在API服务中正确配置UTF-8字符集：

### 1. 数据库连接配置

确保数据库连接字符串中包含字符集参数（以MySQL为例）：

```
mysql+pymysql://username:password@hostname:port/database?charset=utf8mb4
```

### 2. FastAPI应用配置

在FastAPI应用中添加中间件确保正确的响应头：

```python
@app.middleware("http")
async def add_charset_middleware(request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    elif isinstance(response, HTMLResponse):
        response.headers["Content-Type"] = "text/html; charset=utf-8"
    elif isinstance(response, PlainTextResponse):
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response
```

## 环境变量配置

主要环境变量配置说明：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_URL | 数据库连接字符串 | mysql+pymysql://root:123456@localhost:3306/codecheck?charset=utf8mb4 |
| JWT_SECRET | JWT签名密钥 | your_secret_key (生产环境必须更改) |
| JWT_ALGORITHM | JWT签名算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌过期时间(分钟) | 60 |
| CORS_ORIGINS | 允许的跨域来源 | * |
| DEBUG | 是否启用调试模式 | False |
| LOG_LEVEL | 日志级别 | INFO |

## 开发指南

### 添加新API端点

1. 创建新路由文件：
   ```python
   # app/api/v1/new_feature.py
   from fastapi import APIRouter, Depends, HTTPException
   from app.api import deps
   from app.schemas.new_feature import NewFeatureCreate, NewFeatureResponse
   
   router = APIRouter(prefix="/new-feature", tags=["new-feature"])
   
   @router.get("/", response_model=list[NewFeatureResponse])
   async def get_new_features(
       db = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user)
   ):
       """获取新特性列表"""
       # 业务逻辑实现
       return []
   
   @router.post("/", response_model=NewFeatureResponse)
   async def create_new_feature(
       feature: NewFeatureCreate,
       db = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user)
   ):
       """创建新特性"""
       # 业务逻辑实现
       return {}
   ```

2. 注册路由：
   ```python
   # app/api/v1/__init__.py
   from fastapi import APIRouter
   from app.api.v1 import auth, users, projects, new_feature
   
   api_router = APIRouter()
   api_router.include_router(auth.router)
   api_router.include_router(users.router)
   api_router.include_router(projects.router)
   api_router.include_router(new_feature.router)
   ```

### 添加新数据库表

1. 创建数据模型：
   ```python
   # app/models/new_model.py
   from sqlalchemy import Column, Integer, String, ForeignKey, Text
   from sqlalchemy.orm import relationship
   from app.db.base_class import Base
   
   class NewModel(Base):
       __tablename__ = "new_models"
       
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String(100), nullable=False)
       description = Column(Text)
       user_id = Column(Integer, ForeignKey("users.id"))
       
       user = relationship("User", back_populates="new_models")
   ```

2. 更新数据库映射：
   ```python
   # app/db/base.py
   from app.models.user import User
   from app.models.project import Project
   from app.models.new_model import NewModel  # 添加新模型
   ```

3. 创建数据库迁移：
   ```bash
   alembic revision --autogenerate -m "Add new model"
   alembic upgrade head
   ```

## 测试

### 单元测试

```bash
# 运行所有测试
pytest

# 运行特定测试模块
pytest tests/api/test_users.py

# 运行带有覆盖率报告
pytest --cov=app tests/
```

### API测试

1. 测试用户登录API：
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json; charset=utf-8" \
     -d '{"user_id":"admin","password":"123456"}'
   ```

2. 测试获取用户列表API（需要认证）：
   ```bash
   curl -X GET http://localhost:8000/api/v1/users \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

## 故障排除

### 数据库连接问题

#### 问题：后端无法连接到数据库

1. **检查数据库状态**：
   ```bash
   # MySQL
   mysql -u root -p -e "SHOW DATABASES;"
   ```

2. **检查连接字符串**：
   确保格式正确：`mysql+pymysql://username:password@hostname:port/database?charset=utf8mb4`

3. **检查用户权限**

### 中文乱码问题

1. **检查数据库字符集配置**：
   ```bash
   # 检查MySQL字符集
   mysql -u root -p -e "SHOW VARIABLES LIKE 'character%';"
   ```

2. **检查HTTP响应头**：
   ```bash
   curl -s -I http://localhost:8000/api/v1/health
   ```

## 性能优化建议

1. **数据库查询优化**：
   - 为频繁查询的字段添加索引
   - 使用`select_from()`减少连接查询
   - 使用`joinedload()`减少N+1查询问题

2. **API响应优化**：
   - 使用异步查询处理大量并发请求
   - 实现响应缓存机制
   - 分页返回大结果集

## 许可证

本项目采用MIT许可证，详见LICENSE文件。