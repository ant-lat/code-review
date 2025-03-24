# 代码审查系统部署指南

本文档提供了Code Review系统的详细部署指导，包括开发环境、测试环境和生产环境的不同部署方案。

## 目录

- [环境要求](#环境要求)
- [Docker部署](#docker部署)
- [手动部署](#手动部署)
- [Kubernetes部署](#kubernetes部署)
- [配置说明](#配置说明)
- [数据备份与恢复](#数据备份与恢复)
- [常见问题](#常见问题)

## 环境要求

### 最低系统要求

- **CPU**: 2核
- **内存**: 4GB RAM
- **存储**: 20GB可用空间
- **操作系统**: Ubuntu 20.04+/CentOS 8+/Windows Server 2019+

### 软件依赖

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+
- **Node.js**: 16+
- **PostgreSQL**: 13+
- **Nginx**: 1.20+

## Docker部署

### 前置条件

在开始Docker部署之前，请确保您的系统已安装以下软件：

- Docker（20.10.0或更高版本）
- Docker Compose（2.0.0或更高版本）

### 文件说明

本项目包含以下Docker相关文件：

- `docker/backend/Dockerfile`：用于构建后端API的Docker镜像
- `docker/frontend/Dockerfile`：用于构建前端应用的Docker镜像
- `docker/nginx.conf`：Nginx配置文件，用于配置前端服务器和API代理
- `docker/docker-compose.yml`：定义多容器应用的部署配置
- `code-review-web/.dockerignore`：指定构建Docker镜像时要忽略的文件
- `docker/build.sh`：Linux/MacOS环境下构建Docker镜像的脚本
- `docker/deploy.sh`：Linux/MacOS环境下部署Docker容器的脚本
- `docker/windows/build.ps1`：Windows环境下构建Docker镜像的脚本
- `docker/windows/deploy.ps1`：Windows环境下部署Docker容器的脚本

### 构建镜像

可以通过以下几种方式构建Docker镜像：

#### Linux/MacOS环境

##### 方式一：使用构建脚本

```bash
# 赋予脚本可执行权限
chmod +x docker/build.sh

# 执行构建脚本
./docker/build.sh
```

#### Windows环境

##### 方式一：使用PowerShell构建脚本

```powershell
# 执行PowerShell构建脚本
.\docker\windows\build.ps1
```

#### 所有环境通用

##### 方式二：手动构建

```bash
# 进入docker目录
cd docker

# 构建前端Docker镜像
docker build -t code-review-web:latest -f frontend/Dockerfile ../code-review-web

# 构建后端Docker镜像
docker build -t code-review-api:latest -f backend/Dockerfile ../code-review-api
```

### 部署应用

可以通过以下几种方式部署应用：

#### Linux/MacOS环境

##### 方式一：使用部署脚本

```bash
# 赋予脚本可执行权限
chmod +x docker/deploy.sh

# 执行部署脚本
./docker/deploy.sh
```

#### Windows环境

##### 方式一：使用PowerShell部署脚本

```powershell
# 执行PowerShell部署脚本
.\docker\windows\deploy.ps1
```

#### 所有环境通用

##### 方式二：手动部署

```bash
# 进入docker目录
cd docker

# 启动应用
docker-compose up -d

# 查看容器状态
docker-compose ps
```

### 访问应用

部署完成后，可以通过以下地址访问应用：

- 前端应用：http://localhost
- 后端API：http://localhost/api

### 常见问题

#### 1. 无法访问应用

- 检查Docker容器是否正常运行：`docker-compose ps`
- 检查容器日志：`docker-compose logs web`
- 确认80端口未被其他应用占用

#### 2. API请求失败

- 检查后端API容器是否正常运行：`docker-compose ps api`
- 检查后端API容器日志：`docker-compose logs api`
- 确认Nginx配置中的API代理设置是否正确

#### 3. 数据库连接失败

- 检查数据库容器是否正常运行：`docker-compose ps mysql`
- 检查数据库容器日志：`docker-compose logs mysql`
- 确认数据库连接字符串是否正确

#### 4. Windows环境特有问题

- 如果在Windows环境下遇到路径相关问题，请确保使用正确的路径分隔符（`\`而不是`/`）
- 如果执行PowerShell脚本时遇到权限问题，可能需要调整PowerShell执行策略：
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

## 手动部署

对于需要更精细控制或不使用Docker的环境，可以采用手动部署方式。

### 后端API部署

1. **安装Python依赖**

```bash
cd code-review-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑.env文件
```

3. **设置数据库**

```bash
# 安装PostgreSQL并创建数据库
createdb codereview
```

4. **初始化数据库并创建管理员用户**

```bash
python create_security.py
```

5. **启动应用**

开发环境：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

生产环境：
```bash
# 使用gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### 前端Web部署

1. **安装Node.js依赖**

```bash
cd code-review-web
npm install
```

2. **配置环境变量**

```bash
cp .env.example .env.production
# 编辑.env.production文件，设置API地址
```

3. **构建生产版本**

```bash
npm run build
```

4. **部署静态文件**

使用Nginx配置:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        root /path/to/code-review-web/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 插件部署

插件通过IntelliJ Platform插件市场分发，或者直接提供ZIP文件供用户安装。

1. **构建插件**

```bash
cd code-r-plugin
./gradlew buildPlugin
```

2. **生成的插件位于**

```
build/distributions/code-review-plugin-*.zip
```

## Kubernetes部署

对于大型团队或企业环境，Kubernetes提供更好的扩展性和可靠性。

### 前提条件

- Kubernetes集群 (1.20+)
- Helm 3+
- kubectl已配置

### 部署步骤

1. **添加Helm仓库**

```bash
helm repo add code-review https://yourusername.github.io/code-review-helm/
helm repo update
```

2. **创建配置文件 values.yaml**

```yaml
api:
  replicas: 2
  resources:
    limits:
      cpu: 1
      memory: 1Gi
  env:
    DB_HOST: postgres-postgresql
    DB_USER: postgres
    SECRET_KEY: your-secret-key

web:
  replicas: 2
  resources:
    limits:
      cpu: 500m
      memory: 512Mi

database:
  persistence:
    size: 10Gi
  
ingress:
  enabled: true
  hosts:
    - host: codereview.yourdomain.com
      paths:
        - path: /
```

3. **安装Chart**

```bash
helm install code-review code-review/code-review -f values.yaml
```

4. **验证部署**

```bash
kubectl get pods
kubectl get svc
```

5. **初始化数据库**

```bash
kubectl exec -it $(kubectl get pods -l app=code-review-api -o jsonpath='{.items[0].metadata.name}') -- python create_security.py
```

## 配置说明

### 核心配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | 用于安全签名 | 必须设置 |
| DB_HOST | 数据库主机 | postgres |
| DB_PORT | 数据库端口 | 5432 |
| DB_NAME | 数据库名称 | codereview |
| DB_USER | 数据库用户 | postgres |
| DB_PASSWORD | 数据库密码 | 必须设置 |
| ALLOWED_HOSTS | 允许的主机名 | localhost |
| DEBUG | 调试模式 | False |
| API_URL | 后端API地址 | http://localhost:8000 |
| JWT_EXPIRATION | JWT令牌过期时间(分钟) | 1440 |
| SMTP_* | 邮件配置参数 | 可选 |

### SSL配置

对于生产环境，强烈建议配置HTTPS。可以使用Let's Encrypt自动配置：

```bash
# 使用certbot
certbot --nginx -d yourdomain.com
```

或者Docker环境中，编辑docker-compose.yml添加证书卷：

```yaml
volumes:
  - ./ssl:/etc/nginx/ssl
```

## 数据备份与恢复

### 数据库备份

```bash
# Docker环境
docker-compose exec postgres pg_dump -U postgres codereview > backup.sql

# 直接访问PostgreSQL
pg_dump -U postgres codereview > backup.sql
```

### 数据库恢复

```bash
# Docker环境
cat backup.sql | docker-compose exec -T postgres psql -U postgres codereview

# 直接访问PostgreSQL
psql -U postgres codereview < backup.sql
```

### 定期备份

建议设置cron任务进行定期备份：

```cron
0 2 * * * cd /path/to/code-review && docker-compose exec -T postgres pg_dump -U postgres codereview > backups/backup_$(date +\%Y\%m\%d).sql
```

## 常见问题

### 1. 数据库连接失败

检查：
- 数据库服务是否运行
- 连接参数是否正确
- 网络连接是否畅通
- 防火墙是否允许连接

### 2. API服务无法启动

检查：
- 环境变量是否正确配置
- Python依赖是否完整安装
- 日志文件中的错误信息

### 3. 前端无法连接API

检查：
- API_URL是否正确配置
- API服务是否正常运行
- 跨域配置是否正确

### 4. 插件连接问题

检查：
- 服务器URL是否正确配置
- 服务器是否可以公网访问
- 用户凭证是否有效

### 5. Docker容器无法启动

运行：
```bash
docker-compose logs
```
查看详细错误信息。

## 性能优化

### 数据库优化

- 添加适当的索引
- 增加连接池大小
- 调整PostgreSQL配置参数

### Web服务器优化

- 启用Gzip压缩
- 配置浏览器缓存
- 使用CDN加速静态资源

### API服务优化

- 增加worker数量
- 启用响应缓存
- 使用异步任务处理耗时操作

## 监控与维护

### 日志管理

- 使用ELK栈集中管理日志
- 设置日志轮转策略

### 性能监控

- 使用Prometheus监控系统指标
- 使用Grafana创建可视化面板

### 告警配置

- 设置CPU/内存使用率告警
- 设置服务可用性检查
- 设置数据库性能告警

## 联系与支持

如果您在部署过程中遇到任何问题，请：

- 提交GitHub Issue
- 发送邮件至support@example.com
- 查阅更多文档：[文档中心](https://docs.codereview.example.com) 