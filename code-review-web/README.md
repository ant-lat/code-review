# 代码审查系统 - 前端应用

<div align="center">

![React](https://img.shields.io/badge/React-18.0+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)
![Vite](https://img.shields.io/badge/Vite-4.0+-brightgreen)
![Ant Design](https://img.shields.io/badge/Ant%20Design-5.0+-blue)
![Redux](https://img.shields.io/badge/Redux%20Toolkit-1.9+-purple)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

## 项目概述

代码审查系统前端应用是基于React和TypeScript开发的现代化Web应用，提供直观的用户界面来管理代码审核流程。应用采用组件化设计，支持响应式布局，主题切换等特性，提供良好的用户体验。

### 主要功能

- **用户友好的界面**：清晰直观的操作流程和界面设计
- **代码审核管理**：创建、查看和管理代码审核请求
- **问题追踪**：跟踪和管理代码中发现的问题
- **项目管理**：创建和管理项目，设置项目成员和权限
- **用户管理**：管理用户信息和系统权限
- **统计分析**：代码质量和审核进度的可视化统计
- **可定制主题**：支持亮色和暗色模式
- **响应式设计**：适配桌面和移动设备

## 技术栈

- **基础框架**：React 18 + TypeScript 5
- **构建工具**：Vite 4
- **UI组件库**：Ant Design 5
- **状态管理**：Redux Toolkit
- **路由管理**：React Router v6
- **HTTP请求**：Axios
- **样式解决方案**：Tailwind CSS + Less
- **代码规范**：ESLint + Prettier
- **测试工具**：Jest + Testing Library
- **可视化图表**：Echarts / Recharts

## 项目结构

```
code-review-web/
├── public/             # 静态资源
├── src/                # 源代码
│   ├── api/            # API接口定义
│   ├── assets/         # 静态资源
│   ├── components/     # 通用组件
│   │   ├── layout/     # 布局组件
│   │   ├── common/     # 公共组件
│   │   └── business/   # 业务组件
│   ├── hooks/          # 自定义Hooks
│   ├── pages/          # 页面组件
│   │   ├── dashboard/  # 仪表盘
│   │   ├── projects/   # 项目管理
│   │   ├── reviews/    # 代码审核
│   │   ├── issues/     # 问题管理
│   │   └── system/     # 系统管理
│   ├── router/         # 路由配置
│   ├── store/          # Redux状态管理
│   ├── styles/         # 全局样式
│   ├── types/          # TypeScript类型定义
│   ├── utils/          # 工具函数
│   ├── App.tsx         # 应用入口
│   ├── main.tsx        # 主入口
│   └── vite-env.d.ts   # Vite类型声明
├── .eslintrc.js        # ESLint配置
├── .prettierrc         # Prettier配置
├── index.html          # HTML模板
├── package.json        # 项目依赖
├── tailwind.config.js  # Tailwind配置
├── tsconfig.json       # TypeScript配置
├── vite.config.ts      # Vite配置
└── README.md           # 文档
```

## 安装与开发

### 前置条件

- Node.js 16+ 
- npm 8+ 或 yarn 1.22+

### 本地开发

```bash
# 克隆项目
git clone [仓库地址]
cd code-review-web

# 安装依赖
npm install
# 或使用yarn
yarn

# 启动开发服务器
npm run dev
# 或使用yarn
yarn dev
```

开发服务器启动后，访问 http://localhost:5173 即可进入应用。

### 环境变量配置

在项目根目录创建以下环境变量文件:

- `.env` - 所有环境的默认值
- `.env.development` - 开发环境特定值
- `.env.production` - 生产环境特定值

主要环境变量:

```
# API基础URL
VITE_API_BASE_URL=/api

# 是否启用Mock数据
VITE_USE_MOCK=false

# 网站标题
VITE_APP_TITLE=代码审查系统
```

### 构建生产版本

```bash
# 构建生产版本
npm run build
# 或使用yarn
yarn build

# 本地预览生产构建
npm run preview
# 或使用yarn
yarn preview
```

构建完成后，产物将输出到 `dist` 目录。

## 部署方案

### 静态文件部署

将构建生成的 `dist` 目录内容部署到任何静态文件服务器，如Nginx、Apache等。

Nginx配置示例:

```nginx
server {
    listen 80;
    server_name example.com;
    
    # 设置默认字符集
    charset utf-8;
    
    root /path/to/dist;
    index index.html;
    
    # 处理SPA路由
    location / {
        try_files $uri $uri/ /index.html;
        
        # 添加正确的字符集
        add_header Content-Type "text/html; charset=utf-8";
    }
    
    # API代理
    location /api/ {
        proxy_pass http://backend-api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 确保API响应使用UTF-8编码
        add_header Content-Type "application/json; charset=utf-8";
    }
}
```

### Docker部署

使用项目提供的Dockerfile进行构建:

```bash
# 构建镜像
docker build -t code-review-web:latest .

# 运行容器
docker run -d --name code-review-web \
  -p 80:80 \
  -e VITE_API_BASE_URL=/api \
  code-review-web:latest
```

## UTF-8字符集配置

为确保前端应用正确处理中文字符，需要注意以下几点:

1. **HTML头部设置**:
   ```html
   <meta charset="UTF-8" />
   ```

2. **API请求headers设置**:
   ```typescript
   // src/utils/request.ts
   axios.defaults.headers.post['Content-Type'] = 'application/json; charset=utf-8';
   ```

3. **文件编码确保为UTF-8**:
   所有源代码文件应使用UTF-8编码保存，避免中文字符乱码问题。

## 开发指南

### 添加新页面

1. 创建页面组件:
   ```tsx
   // src/pages/new-feature/index.tsx
   import React from 'react';
   
   const NewFeaturePage: React.FC = () => {
     return (
       <div>
         <h1>新功能页面</h1>
         <p>这是一个新功能页面</p>
       </div>
     );
   };
   
   export default NewFeaturePage;
   ```

2. 添加路由配置:
   ```tsx
   // src/router/index.tsx
   import NewFeaturePage from '@/pages/new-feature';
   
   const routes = [
     // 其他路由...
     {
       path: '/new-feature',
       element: <NewFeaturePage />,
     },
   ];
   ```

### 添加新API接口

1. 定义API类型:
   ```typescript
   // src/types/api.ts
   export interface NewFeatureParams {
     name: string;
     description: string;
   }
   
   export interface NewFeatureResponse {
     id: number;
     name: string;
     description: string;
     createdAt: string;
   }
   ```

2. 创建API请求:
   ```typescript
   // src/api/new-feature.ts
   import request from '@/utils/request';
   import { NewFeatureParams, NewFeatureResponse } from '@/types/api';
   
   export function getNewFeatures() {
     return request<NewFeatureResponse[]>({
       url: '/api/v1/new-features',
       method: 'get',
     });
   }
   
   export function createNewFeature(data: NewFeatureParams) {
     return request<NewFeatureResponse>({
       url: '/api/v1/new-features',
       method: 'post',
       data,
     });
   }
   ```

### 添加新Redux状态

1. 创建Slice:
   ```typescript
   // src/store/features/newFeatureSlice.ts
   import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
   import { getNewFeatures } from '@/api/new-feature';
   
   export const fetchNewFeatures = createAsyncThunk(
     'newFeature/fetchAll',
     async () => {
       const response = await getNewFeatures();
       return response.data;
     }
   );
   
   const newFeatureSlice = createSlice({
     name: 'newFeature',
     initialState: {
       items: [],
       loading: false,
       error: null,
     },
     reducers: {},
     extraReducers: (builder) => {
       // 处理异步Action
     },
   });
   
   export default newFeatureSlice.reducer;
   ```

2. 注册到Store:
   ```typescript
   // src/store/index.ts
   import newFeatureReducer from './features/newFeatureSlice';
   
   export const store = configureStore({
     reducer: {
       // 其他reducer...
       newFeature: newFeatureReducer,
     },
   });
   ```

## 测试

### 单元测试

```bash
# 运行所有测试
npm run test

# 运行特定测试文件
npm run test src/components/Button.test.tsx

# 带有覆盖率报告
npm run test:coverage
```

### 端到端测试

```bash
# 使用Cypress运行E2E测试
npm run test:e2e
```

## 故障排除

### 常见问题

#### 1. API请求失败

- 检查API基础URL配置是否正确
- 确认API代理设置是否正确
- 检查网络请求是否包含正确的认证信息

```typescript
// 检查环境变量
console.log(import.meta.env.VITE_API_BASE_URL);

// 检查请求配置
console.log(axios.defaults.baseURL);
```

#### 2. 中文显示乱码

- 检查HTML文件编码设置
- 确认API响应头包含正确的Content-Type
- 验证文本内容中是否有特殊字符编码问题

```bash
# 检查API响应头
curl -I http://localhost:8000/api/v1/endpoint
```

#### 3. 构建失败

- 检查依赖项版本兼容性
- 清除缓存后重新构建
- 检查TypeScript类型错误

```bash
# 清除依赖缓存
rm -rf node_modules
npm install

# 检查类型
npm run typecheck
```

## 性能优化

- 使用React.memo减少不必要的重渲染
- 实现组件懒加载和代码分割
- 使用Service Worker缓存静态资源
- 优化大列表渲染，使用虚拟列表
- 进行图片压缩和资源CDN部署

## 许可证

本项目采用MIT许可证，详见LICENSE文件。 