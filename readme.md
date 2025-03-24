# 代码审查系统(Code Review)项目文档

<div align="center">

![代码审查系统](https://img.shields.io/badge/Code%20Review-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![React](https://img.shields.io/badge/React-18.0+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0+-orange)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

## 项目概述

代码审查系统是一个全功能的代码审核和问题跟踪平台，支持多数据库后端，提供代码质量管理、问题追踪、团队协作等核心功能。系统设计为前后端分离架构，支持容器化部署，可灵活适应各种开发环境和团队规模。

### 核心功能

- **代码提交管理**：追踪和管理代码仓库的提交记录
- **问题跟踪**：记录、分类和管理代码问题及改进建议
- **代码审核**：支持多人协作的代码审核流程
- **用户权限管理**：基于角色的精细化权限控制
- **项目管理**：多项目支持，每个项目可配置不同的审核规则
- **数据分析**：代码质量分析和团队表现报告
- **IDEA插件**：支持IntelliJ IDEA集成，提供IDE内直接审核功能
- **多语言支持**：完整支持中文和英文界面，轻松切换
- **响应式设计**：适配桌面和移动设备的用户界面
- **黑暗模式**：支持明亮和黑暗主题，保护眼睛

## 技术栈亮点

- **高性能的RESTful API**：FastAPI提供的异步处理能力确保高并发场景下的良好表现
- **可扩展的模块化设计**：前后端均采用模块化设计，便于功能扩展和定制
- **强类型保障**：TypeScript和Python类型提示确保代码质量和开发效率
- **实时通知**：支持WebSocket实时通知，保持团队即时沟通
- **安全防护**：JWT认证、CORS控制、XSS防护、CSRF令牌等多重安全机制
- **自动化文档**：API自动生成Swagger文档，简化集成和测试
- **流畅的用户体验**：React SPA应用结合Ant Design提供专业的UI/UX

## 目录结构

```
code-review/
├── code-review-api/      # 后端API服务
│   ├── app/              # 应用代码
│   │   ├── core/         # 核心功能
│   │   ├── database/     # 数据库配置
│   │   ├── models/       # 数据模型
│   │   ├── routers/      # API路由
│   │   ├── schemas/      # 数据验证模式
│   │   ├── services/     # 业务逻辑
│   │   └── main.py       # 应用入口
│   ├── tests/            # 测试代码
│   └── requirements.txt  # 依赖列表
├── code-review-web/      # 前端应用
│   ├── public/           # 静态资源
│   ├── src/              # 源代码
│   │   ├── api/          # API客户端
│   │   ├── components/   # 通用组件
│   │   ├── layouts/      # 页面布局
│   │   ├── pages/        # 页面组件
│   │   ├── store/        # 状态管理
│   │   ├── styles/       # 样式文件
│   │   └── App.tsx       # 应用入口
│   └── package.json      # 依赖配置
├── code-r-plugin/        # IDEA插件
│   ├── src/              # 源代码
│   └── build.gradle      # 构建配置
├── docker/               # Docker配置
│   ├── backend/          # 后端容器配置
│   ├── frontend/         # 前端容器配置
│   ├── mysql/            # MySQL容器配置
│   └── docker-compose.yml # 容器编排配置
└── README.md             # 项目文档
```

## 系统架构

系统由三个主要组件构成：

### 前端 (code-review-web)

- 基于React 18和TypeScript开发
- 使用Vite作为构建工具，实现快速开发和优化的生产构建
- Ant Design组件库提供专业美观的UI界面
- Axios处理API请求，支持拦截器和全局错误处理
- Redux Toolkit进行状态管理，保证数据流的可预测性
- React Router v6管理路由，支持嵌套路由和路由守卫
- 使用Tailwind CSS进行样式管理，提高开发效率

### 后端 (code-review-api)

- 基于Python 3.9+和FastAPI 0.95+框架开发
- SQLAlchemy 2.0 ORM用于数据库交互，支持异步查询
- Pydantic 2.0进行数据验证和序列化
- JWT认证机制保障API安全
- 支持多种数据库引擎(MySQL, PostgreSQL, SQLite, Oracle)
- FastAPI依赖注入系统实现简洁的代码组织
- 集成单元测试和集成测试框架，保证代码质量

### IDEA插件 (code-r-plugin)

- 基于IntelliJ平台SDK开发，使用Kotlin语言
- 支持在IDE内直接查看和提交代码审核
- 与团队服务器同步，提供实时审核状态
- 支持添加行内评论和批注
- 集成代码差异比较工具
- 支持所有JetBrains IDEs (IntelliJ IDEA, WebStorm, PyCharm等)
- 离线工作模式支持，稍后同步功能

## 数据库支持

系统支持四种主流数据库，每种数据库都有专门优化的初始化脚本：

- **MySQL**：适合中大型项目，提供良好的性能和稳定性
- **PostgreSQL**：支持高级数据类型和查询功能，适合复杂数据分析
- **SQLite**：轻量级选项，适合小型团队或个人使用
- **Oracle**：企业级数据库，适合大型企业环境

所有数据库脚本位于`code-review-api/app/db/`目录下。

### 数据库特性

- **多数据库适配**：无缝切换不同数据库系统，无需修改应用代码
- **自动迁移工具**：使用Alembic进行版本控制和数据库迁移
- **连接池管理**：优化的连接池配置，确保高并发下的数据库性能
- **慢查询日志**：自动记录和分析慢查询，辅助性能优化
- **UTF-8编码支持**：完整的多语言字符集支持，正确处理各种文字

### 数据库初始化

除了使用SQL脚本外，系统还提供了便捷的命令行工具初始化数据库：

```bash
# 切换到项目根目录
cd code-review-api

# 使用命令行工具初始化数据库（自动创建表结构和初始数据）
python -m app.main init-db
```

这个命令会根据配置的数据库连接字符串，自动创建所有表结构并加载初始数据，包括默认用户、角色、权限等。该命令具体执行以下操作：

1. 删除现有的数据库表（如果存在）
2. 创建全新的表结构
3. 插入默认管理员用户（admin/123456）
4. 创建默认角色和权限
5. 配置初始系统参数
6. 创建基础菜单项

如果您想保留现有数据并只更新表结构，可以使用：

```bash
python -m app.main migrate-db
```

对于生产环境，请确保在初始化后立即修改默认管理员密码。

## 快速开始

### 使用Docker Compose（推荐）

最快速的部署方式是使用项目提供的Docker Compose配置：

```bash
# 克隆仓库
git clone https://github.com/yourusername/code-review.git
cd code-review

# 启动所有服务
cd docker
docker-compose up -d

# 查看服务状态
docker-compose ps
```

服务启动后，可以通过以下方式访问：
- 前端界面：http://localhost:80
- API服务：http://localhost:8000
- API文档：http://localhost:8000/docs
- MySQL数据库：localhost:13306 (用户名: codecheck, 密码: codecheck_password)

### 手动部署

如果您希望手动部署各个组件，请按照以下步骤操作：

#### 1. 数据库准备

##### MySQL

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE codecheck CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'codecheck'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON codecheck.* TO 'codecheck'@'%';
FLUSH PRIVILEGES;
EXIT;

# 执行初始化脚本
mysql -u codecheck -p codecheck < code-review-api/app/db/MySQL.sql
```

##### PostgreSQL

```bash
# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE codecheck;
CREATE USER codecheck WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE codecheck TO codecheck;
\q

# 执行初始化脚本
psql -U codecheck -d codecheck -f code-review-api/app/db/PostgreSQL.sql
```

##### SQLite

```bash
# 创建数据库文件
mkdir -p data
sqlite3 data/codecheck.db < code-review-api/app/db/SQLite.sql
```

##### Oracle

```bash
# 使用Oracle客户端工具连接数据库
sqlplus username/password@service

# 执行SQL脚本
@code-review-api/app/db/Oracle.sql
```

#### 2. 后端部署

##### 本地开发部署

```bash
# 克隆仓库
git clone [仓库地址]
cd code-review-api

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows使用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置数据库连接（创建.env文件）
echo "DB_URL=mysql+pymysql://codecheck:your_password@localhost:3306/codecheck?charset=utf8mb4" > .env
echo "JWT_SECRET=your_secure_jwt_secret" >> .env
echo "JWT_ALGORITHM=HS256" >> .env
echo "ACCESS_TOKEN_EXPIRE_MINUTES=60" >> .env

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

##### 生产环境部署

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

#### 3. 前端部署

##### 本地开发部署

```bash
# 进入前端目录
cd code-review-web

# 安装依赖
npm install

# 配置环境变量（创建.env.local文件）
echo "VITE_API_BASE_URL=/api" > .env.local

# 启动开发服务器
npm run dev
```

##### 生产环境部署

```bash
# 构建生产版本
npm run build

# 使用Nginx部署（Nginx配置示例）
server {
    listen 80;
    server_name your-domain.com;
    
    # 设置默认字符集
    charset utf-8;
    
    location / {
        root /path/to/code-review-web/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 为HTML等添加字符编码
        add_header Content-Type "text/html; charset=utf-8";
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 确保API响应使用UTF-8编码
        add_header Content-Type "application/json; charset=utf-8";
    }
}
```

## UTF-8字符集配置指南

为确保系统正确处理中文等多语言字符，需要在各个层级正确配置UTF-8字符集：

### 1. 数据库配置

#### MySQL配置

```ini
# MySQL配置文件 (my.cnf)
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
init-connect='SET NAMES utf8mb4'
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
```

#### 数据库连接字符串

确保连接字符串中包含字符集参数：

```
mysql+pymysql://username:password@hostname:port/database?charset=utf8mb4
```

### 2. 后端API配置

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

### 3. 前端配置

在前端API请求配置中设置正确的请求头：

```typescript
// Axios配置
const config = {
  baseURL: '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json; charset=utf-8',
    'Accept-Charset': 'utf-8'
  },
};

// 确保所有请求都包含正确的字符集
axios.interceptors.request.use(config => {
  config.headers['Content-Type'] = 'application/json; charset=utf-8';
  config.headers['Accept'] = 'application/json; charset=utf-8';
  config.headers['Accept-Charset'] = 'utf-8';
  return config;
});
```

### 4. Nginx配置

```nginx
server {
    # 设置默认字符集
    charset utf-8;
    
    # 添加默认类型
    default_type 'text/html; charset=utf-8';
    
    location / {
        # 为HTML等添加字符编码
        add_header Content-Type "text/html; charset=utf-8";
        add_header X-Content-Type-Options "nosniff" always;
    }
    
    location /api {
        # 确保API响应使用UTF-8编码
        add_header Content-Type "application/json; charset=utf-8" always;
        proxy_set_header Accept-Charset "utf-8";
        proxy_set_header Accept "application/json; charset=utf-8";
    }
}
```

## 配置详解

### 后端配置

主要配置文件：`code-review-api/app/config/__init__.py`

```python
# 数据库配置
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:123456@localhost:3306/codecheck?charset=utf8mb4")

# JWT认证配置
JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# 系统配置
CORS_ORIGINS = ["*"]  # 允许的跨域来源
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

### 前端配置

主要配置文件：`code-review-web/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    hmr: {
      host: "localhost",
      port: 5173,
    },
    proxy: {
      '/api': {
        // 本地开发环境
        target: 'http://localhost:8000',
        // Docker环境
        // target: 'http://host.docker.internal:8000',
        // Docker Compose环境
        // target: 'http://code-review-api-container:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  // 其他配置...
});
```

## 系统管理与维护

### 备份与恢复

#### 数据库备份

```bash
# MySQL备份
mysqldump -u codecheck -p codecheck > backup-$(date +%Y%m%d).sql

# PostgreSQL备份
pg_dump -U codecheck codecheck > backup-$(date +%Y%m%d).sql

# SQLite备份
sqlite3 data/codecheck.db .dump > backup-$(date +%Y%m%d).sql
```

#### 数据库恢复

```bash
# MySQL恢复
mysql -u codecheck -p codecheck < backup.sql

# PostgreSQL恢复
psql -U codecheck -d codecheck -f backup.sql

# SQLite恢复
sqlite3 data/codecheck.db < backup.sql
```

### 日志管理

系统日志保存在以下位置：

- 后端API日志：`code-review-api/logs/`
- Docker容器日志：通过`docker logs`命令查看
- Nginx访问日志：`/var/log/nginx/access.log`
- Nginx错误日志：`/var/log/nginx/error.log`

### 性能监控

本系统已集成以下性能监控功能：

- **数据库慢查询日志**：记录执行时间超过阈值的查询
- **API性能监控**：记录各API端点的请求耗时统计
- **系统资源监控**：可选择集成Prometheus+Grafana监控方案
- **用户活动审计**：记录关键操作的执行用户和时间

## 测试与验证

### API测试

1. 后端启动后，访问Swagger文档：`http://localhost:8000/docs`
2. 使用自带的交互界面测试各个API端点
3. 系统健康检查：`http://localhost:8000/api/v1/health`

### 用户认证测试

```bash
# 登录测试（使用curl）
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"user_id":"admin","password":"123456"}'

# 应返回包含access_token的JSON响应
```

### 前端页面测试

1. 访问前端首页：`http://localhost`
2. 使用默认管理员账户登录：
   - 用户名：admin
   - 密码：123456
3. 验证菜单和功能是否正常显示

### 容器网络测试

```bash
# 测试API容器是否可访问数据库
docker exec -it code-review-api curl -v http://mysql:3306

# 测试Web容器是否可访问API
docker exec -it code-review-web curl -v http://code-review-api:8000/api/v1/health
```

## 常见问题解决

### 数据库连接问题

#### 问题：后端无法连接到数据库

1. **检查数据库状态**：
   ```bash
   # MySQL
   mysql -u root -p -e "SHOW DATABASES;"
   
   # PostgreSQL
   psql -U postgres -c "\l"
   ```

2. **检查连接字符串**：
   - MySQL连接格式：`mysql+pymysql://username:password@hostname:port/database?charset=utf8mb4`
   - PostgreSQL连接格式：`postgresql://username:password@hostname:port/database`
   - SQLite连接格式：`sqlite:///path/to/database.db`
   - Oracle连接格式：`oracle+cx_oracle://username:password@hostname:port/service`

3. **检查用户权限**：
   ```sql
   -- MySQL
   GRANT ALL PRIVILEGES ON codecheck.* TO 'codecheck'@'%';
   FLUSH PRIVILEGES;
   ```

4. **排查网络问题**：
   - 确保数据库服务器的防火墙允许连接
   - 检查主机名解析是否正确

### 中文乱码问题

#### 问题：界面或API返回中文乱码

1. **检查数据库字符集配置**：
   ```bash
   # 检查MySQL字符集
   docker-compose exec mysql mysql -uroot -proot_password -e "SHOW VARIABLES LIKE 'character%';"
   
   # 正确结果应该显示所有字符集为utf8mb4
   ```

2. **检查数据库连接字符串**：
   - 确保连接字符串包含`?charset=utf8mb4`参数
   - 示例：`mysql+pymysql://codecheck:password@mysql:3306/codecheck?charset=utf8mb4`

3. **检查HTTP响应头**：
   ```bash
   # 检查API响应头
   curl -s -I http://localhost/api/v1/health
   
   # 应包含：Content-Type: application/json; charset=utf-8
   ```

4. **检查前端请求头**：
   - 确保API请求设置了正确的`Content-Type`和`Accept`头
   - 示例：`Content-Type: application/json; charset=utf-8`

### Docker容器通信问题

#### 问题：前端容器无法访问后端API

1. **检查网络连接**：
   ```bash
   docker network inspect docker_code-review-network
   ```

2. **测试容器间通信**：
   ```bash
   docker exec -it code-review-web ping code-review-api
   ```

3. **检查代理配置**：
   - 在Docker环境中，将`localhost`改为容器名或`host.docker.internal`
   - 确保代理路径正确（如`/api`前缀）

4. **查看容器日志**：
   ```bash
   docker logs code-review-api
   docker logs code-review-web
   ```

### API端点404问题

1. **检查API路径**：
   - 确保所有API请求包含前缀`/api/v1/`
   - 检查URL拼写是否正确

2. **验证后端路由**：
   - 查看API文档：`http://localhost:8000/docs`
   - 检查后端日志是否有路由注册信息

3. **前端跨域设置**：
   - 检查CORS设置是否正确
   - 验证代理配置是否有效

### 认证和权限问题

1. **登录失败**：
   - 验证用户名和密码是否正确
   - 检查JWT配置（密钥和算法）
   - 确认用户账户状态是否激活

2. **权限不足**：
   - 检查用户角色分配
   - 验证角色-权限关联
   - 查看请求头中是否包含有效的JWT令牌

## 开发扩展指南

### 添加新API端点

1. 创建新路由文件：
   ```python
   # code-review-api/app/routers/new_feature.py
   from fastapi import APIRouter, Depends
   
   router = APIRouter(prefix="/api/v1/new-feature", tags=["new-feature"])
   
   @router.get("/")
   async def get_new_features():
       return {"features": ["feature1", "feature2"]}
   ```

2. 注册路由：
   ```python
   # code-review-api/app/main.py
   from app.routers import new_feature
   
   app.include_router(new_feature.router)
   ```

### 添加新数据库表

1. 创建模型：
   ```python
   # code-review-api/app/models/new_model.py
   from sqlalchemy import Column, Integer, String, ForeignKey
   from app.database import Base
   
   class NewModel(Base):
       __tablename__ = "new_models"
       
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String(100), nullable=False)
       description = Column(String(255))
   ```

2. 创建数据库迁移：
   ```bash
   alembic revision --autogenerate -m "Add new model"
   alembic upgrade head
   ```

### 添加新前端页面

1. 创建新组件：
   ```jsx
   // code-review-web/src/pages/NewFeature.jsx
   import React from 'react';
   
   const NewFeature = () => {
     return (
       <div>
         <h1>New Feature</h1>
         <p>This is a new feature page.</p>
       </div>
     );
   };
   
   export default NewFeature;
   ```

2. 添加路由：
   ```jsx
   // code-review-web/src/App.jsx
   import NewFeature from './pages/NewFeature';
   
   // 在路由配置中添加
   <Route path="/new-feature" element={<NewFeature />} />
   ```

## 贡献指南

欢迎为本项目做出贡献！以下是贡献流程：

1. **Fork项目**：在GitHub上fork本项目
2. **创建分支**：`git checkout -b feature/your-feature-name`
3. **编写代码**：遵循项目的代码风格和约定
4. **运行测试**：确保所有测试通过
5. **提交代码**：`git commit -m "Add feature: your feature description"`
6. **推送分支**：`git push origin feature/your-feature-name`
7. **创建Pull Request**：在GitHub上创建PR，详细描述你的更改

### 代码风格

- **Python后端**：遵循PEP 8规范，使用pylint检查
- **React前端**：使用ESLint+Prettier保持一致风格
- **注释**：为所有公共接口提供文档注释
- **测试**：为新功能编写单元测试和集成测试

### 分支策略

- `main`：稳定的生产版本分支
- `develop`：开发分支，包含待发布的功能
- `feature/*`：新功能开发分支
- `bugfix/*`：Bug修复分支
- `release/*`：发布准备分支

## 系统升级和迁移

### 数据库升级

```bash
# 使用Alembic进行数据库迁移
cd code-review-api
alembic revision --autogenerate -m "Add new features"
alembic upgrade head
```

### 代码部署更新

```bash
# 从Git更新代码
git pull origin main

# 更新后端依赖
pip install -r requirements.txt

# 更新前端依赖
cd code-review-web
npm install

# 重启服务
sudo systemctl restart code-review-api
```

### Docker镜像更新

```bash
# 构建新镜像
docker build -t code-review-api:latest ./code-review-api
docker build -t code-review-web:latest ./code-review-web

# 更新容器
docker-compose down
docker-compose up -d
```

## 性能优化建议

为获得最佳性能，推荐以下配置：

1. **数据库优化**：
   - 为常用查询字段添加索引
   - 对大型表进行分区
   - 使用连接池管理连接资源

2. **API性能**：
   - 启用API响应缓存
   - 使用异步查询处理大量并发请求
   - 实现分批加载大结果集

3. **前端优化**：
   - 启用代码分割减小初始加载体积
   - 实现懒加载组件和路由
   - 使用虚拟滚动处理大列表

4. **Docker容器**：
   - 指定合理的内存和CPU限制
   - 使用卷挂载而非容器内数据存储
   - 使用多阶段构建减小镜像体积

## 安全最佳实践

本系统实施了以下安全措施：

1. **身份验证与授权**：
   - JWT令牌认证
   - 基于角色的访问控制
   - 密码哈希存储(bcrypt)

2. **防护措施**：
   - SQL注入防护
   - XSS攻击防护
   - CSRF令牌验证
   - 请求频率限制

3. **安全更新建议**：
   - 定期更新依赖包
   - 启用HTTPS加密传输
   - 实施IP白名单限制

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系与支持

如有问题或需要支持，请通过以下方式联系：

- 项目仓库Issues: https://github.com/yourusername/code-review/issues
- 电子邮件：support@example.com
- 技术文档：https://docs.example.com/code-review

## 致谢

感谢所有为本项目做出贡献的开发者和用户。本项目使用了以下开源技术：

- React
- FastAPI
- SQLAlchemy
- Ant Design
- Vite
- Docker

