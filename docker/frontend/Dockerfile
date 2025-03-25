FROM node:18-alpine as build

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json ./

# 清理npm缓存并安装依赖
RUN npm cache clean --force && \
    npm ci --no-cache

# 复制源代码
COPY . .

# 显示环境变量内容
RUN echo "=== Environment Variables ===" && \
    cat .env.production && \
    echo "=== End Environment Variables ==="

# 清理构建缓存并重新构建
RUN rm -rf dist && \
    npm run build

# 显示构建后的 main.js 内容
RUN echo "=== Checking main.js content ===" && \
    cat dist/assets/main-*.js | grep -o "baseURL.*" || true && \
    echo "=== End main.js content ==="

# 使用nginx作为生产环境服务器
FROM nginx:stable-alpine

# 从构建阶段复制构建结果到nginx目录
COPY --from=build /app/dist /usr/share/nginx/html

# 暴露80端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"] 