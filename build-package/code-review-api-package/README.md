# Code Review API 服务

这是代码审查系统的后端API服务，基于Python和FastAPI框架开发。本服务提供了代码审查系统所需的所有API接口，包括用户认证、项目管理、问题跟踪等功能。

## 技术栈

- **Python 3.9+**: 主要编程语言
- **FastAPI**: 高性能API框架
- **SQLAlchemy**: ORM框架
- **Pydantic**: 数据验证和设置管理
- **PostgreSQL**: 数据库
- **JWT**: 认证授权

## 目录结构

```
code-review-api/
├── app/                   # 应用程序主目录
│   ├── config/            # 配置文件
│   ├── core/              # 核心功能
│   ├── database/          # 数据库操作
│   ├── models/            # 数据模型
│   ├── routers/           # API路由
│   ├── schemas/           # 数据验证模式
│   ├── services/          # 业务逻辑服务
│   └── main.py            # 应用程序入口
├── tests/                 # 测试代码
├── static/                # 静态资源
├── requirements.txt       # 依赖项列表
├── Dockerfile             # Docker构建文件
└── .env.example           # 环境变量示例
```

## 核心功能

1. **用户认证与授权**
   - JWT认证
   - 基于角色的权限系统
   - 用户管理

2. **项目管理**
   - 创建和管理项目
   - 项目成员管理
   - 项目统计

3. **问题跟踪**
   - 创建和管理问题
   - 问题分配和状态跟踪
   - 问题评论和讨论

4. **代码审查**
   - 支持代码片段审查
   - 支持提交代码审查
   - 审查评论和标记

## 开发环境设置

1. 克隆仓库:
   ```bash
   git clone https://github.com/yourusername/code-review.git
   cd code-review-api
   ```

2. 创建并激活虚拟环境:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 创建环境变量文件:
   ```bash
   cp .env.example .env
   # 编辑.env文件，配置数据库连接和其他设置
   ```

5. 初始化数据库:
   ```bash
   python -m app.db.init_db
   ```

6. 启动开发服务器:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API文档

启动服务后，可以通过以下URL访问API文档:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

运行单元测试:
```bash
pytest
```

## Docker部署

### 单独构建和运行

1. 构建Docker镜像:
   ```bash
   docker build -t code-review-api .
   ```

2. 运行容器:
   ```bash
   docker run -d --name code-review-api \
     -p 8000:8000 \
     -e DATABASE_URL=postgresql://postgres:postgres@db:5432/code_review \
     -e SECRET_KEY=your_secure_secret_key \
     -e DEBUG=False \
     code-review-api
   ```

### Docker Compose

推荐使用项目根目录中的`docker-compose.yml`进行部署，它会自动配置API服务、Web前端和数据库之间的连接。

## 二次开发指南

### 添加新的API端点

1. 在`app/routers/`目录下创建新的路由模块
2. 在`app/schemas/`目录下创建请求和响应模型
3. 在`app/services/`目录下实现业务逻辑
4. 在`app/main.py`中注册新路由

### 数据库模型定义

1. 在`app/models/`目录下创建新的模型类
2. 在需要使用该模型的服务中导入并使用

### 授权和权限

所有需要授权的API端点应使用`get_current_user`依赖项:
```python
from app.core.security import get_current_user
from app.models.user import User

@router.get("/protected-endpoint")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    # 处理请求
    pass
```

## 常见问题

1. **数据库连接错误**
   - 检查`.env`文件中的`DATABASE_URL`配置
   - 确保数据库服务正在运行

2. **授权失败**
   - 检查`SECRET_KEY`配置
   - 验证JWT令牌是否有效
   - 确保用户具有所需权限

3. **性能问题**
   - 优化数据库查询
   - 使用缓存
   - 调整Uvicorn工作进程数量

## 贡献

欢迎贡献代码和提出建议! 请参阅项目根目录中的[贡献指南](../CONTRIBUTING.md)。

## 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](../LICENSE)文件。 