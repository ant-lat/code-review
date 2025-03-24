#!/bin/bash

# 进入docker目录
cd "$(dirname "$0")"

# 检查docker-compose是否存在
if ! command -v docker-compose &> /dev/null; then
    echo "错误：未找到docker-compose命令"
    echo "请安装docker-compose后再尝试部署"
    exit 1
fi

# 停止并移除现有容器
echo "停止现有容器..."
docker-compose down

# 启动新容器
echo "启动新容器..."
docker-compose up -d

# 检查容器状态
echo "检查容器状态..."
docker-compose ps

echo "部署完成！"
echo "前端应用可通过 http://localhost 访问"
echo "后端API可通过 http://localhost/api 访问" 