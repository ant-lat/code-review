#!/bin/bash

# 进入docker目录
cd "$(dirname "$0")"

# 构建前端Docker镜像
echo "构建前端Docker镜像..."
docker build -t code-review-web:latest -f frontend/Dockerfile ../code-review-web

echo "前端Docker镜像构建完成！"

# 如果后端项目存在则构建后端镜像
if [ -d "../code-review-api" ]; then
  echo "构建后端Docker镜像..."
  docker build -t code-review-api:latest -f backend/Dockerfile ../code-review-api
  echo "后端Docker镜像构建完成！"
fi

echo "所有Docker镜像构建完成！" 