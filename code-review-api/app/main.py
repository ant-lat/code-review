"""
主函数模块
@author: pgao
@date: 2024-03-13
"""
import logging
from app.config.logging_config import logger
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Config, parse_arguments, config
from app.database.init_db import init_db
from fastapi.responses import JSONResponse
from starlette.responses import HTMLResponse, PlainTextResponse
from dotenv import load_dotenv
import pathlib
import os
# 确保项目根目录在Python路径中
ROOT_DIR = pathlib.Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

app = FastAPI()

# 设置默认响应的编码和内容类型
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

# 从配置获取CORS设置
# 默认允许localhost和localhost:5173
default_origins = ["http://localhost", "http://localhost:5173"]
# 使用统一的配置类获取配置
allowed_origins = config.get('ALLOWED_ORIGINS', ",".join(default_origins))
# 如果是字符串，按逗号分隔
if isinstance(allowed_origins, str):
    origins = allowed_origins.split(",")
    # 移除可能的空格
    origins = [origin.strip() for origin in origins if origin.strip()]
    # 如果环境变量为空，使用默认值
    if not origins:
        origins = default_origins
else:
    # 如果已经是列表，直接使用
    origins = allowed_origins if allowed_origins else default_origins

logger.info(f"CORS允许的源: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# async def startup_event():
#     logger.info("应用启动：CodeC代码检视系统服务已启动")

# 注册认证路由

# 注册路由
from app.routers import (
    base_router,
    auth_router,
    users_router,
    projects_router,
    roles_router,
    code_analysis_router,
    issues_router,
    dashboard_router,
    notification_router,
    user_menu_access_router as user_menu_router,
    code_review_router,
)
app.include_router(base_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(roles_router)
app.include_router(code_analysis_router)
app.include_router(issues_router)
app.include_router(dashboard_router)
app.include_router(notification_router)
# 注册新添加的用户菜单路由
app.include_router(user_menu_router)
app.include_router(code_review_router)
from dotenv import load_dotenv
load_dotenv()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    # 独立解析命令行参数
    args = parse_arguments()
    config = Config(args=args, config_path=args.config)
    
    if args.command == 'init-db':
        try:
            print("执行数据库初始化...")
            init_db()
            print("\n\033[92m数据库初始化完成\033[0m\n")
        except Exception as e:
            print(f"\n\033[91m数据库初始化失败: {str(e)}\033[0m\n")
            sys.exit(1)
    else:
        # 使用指定的端口（如果8000被占用，则使用8001）
        port = config.PORT
        try:
            print(f"尝试在 {config.HOST}:{port} 上启动服务...")
            uvicorn.run(app, host=config.HOST, port=port)
        except OSError as e:
            # 如果端口被占用，尝试使用另一个端口
            if "address already in use" in str(e).lower() or "winerror 10048" in str(e).lower():
                alt_port = 8001
                print(f"端口 {port} 已被占用，尝试使用备用端口 {alt_port}...")
                uvicorn.run(app, host=config.HOST, port=alt_port)
            else:
                raise
        logger.info(f"服务启动：监听地址 {config.HOST}:{port}")