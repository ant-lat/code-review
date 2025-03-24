from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Dict, Any
import platform
import psutil
from datetime import datetime

from app.config.logging_config import logger
from app.database import get_db

base_router = APIRouter(tags=["基础"])

@base_router.get("/")
async def welcome():
    return JSONResponse(content={"message": "欢迎使用CodeC代码检视系统"})

@base_router.get("/health")
async def health_check():
    """
    系统健康检查
    
    Returns:
        JSONResponse: 系统状态信息
    """
    try:
        # 获取系统基本信息
        system_info = {
            "status": "ok",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system": platform.system(),
            "version": platform.version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent
        }
        
        return JSONResponse(content=system_info)
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"健康检查失败: {str(e)}"}
        )

@base_router.get("/info")
async def system_info():
    """
    获取系统信息
    
    Returns:
        JSONResponse: 系统详细信息
    """
    return JSONResponse(content={
        "name": "CodeC代码检视系统",
        "version": "2.0.0",
        "description": "专业的代码审核与质量控制平台",
        "author": "技术团队",
        "contact": "support@codec.com"
    })

# 配置静态文件路由
base_router.mount("/static", StaticFiles(directory=os.path.abspath("static")), name="static")