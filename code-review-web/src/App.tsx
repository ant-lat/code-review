import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCurrentUser } from './store/slices/authSlice';
import { fetchUserMenus, selectMenus, selectMenuInitialized } from './store/slices/menuSlice';
import { isLoggedIn, hasToken } from './utils/auth';

// 全局样式
import './styles/global.less';

// 布局
import BasicLayout from './layouts/BasicLayout';

// 页面
import LoginPage from './pages/login/index';
import ForgotPasswordPage from './pages/login/ForgotPassword';
import Dashboard from './pages/dashboard/index';
import Projects from './pages/projects/index';
import ProjectDetail from './pages/projects/detail';
import Issues from './pages/issues/index';
import IssueDetail from './pages/issues/detail';
import CodeReview from './pages/codeReview/index';
import CodeReviewDetail from './pages/codeReview/detail';
import CodeAnalysis from './pages/codeAnalysis/index';
import Users from './pages/users';
import Settings from './pages/settings/index';
import NotFound from './pages/404';
import Forbidden from './pages/403';
import NotificationsPage from './pages/Notifications';

// 组件
import AuthRoute from './components/AuthRoute';

// 页面组件映射表
const pageComponents: Record<string, React.FC<any>> = {
  '/dashboard': Dashboard,
  '/projects': Projects,
  '/projects/:id': ProjectDetail,
  '/issues': Issues,
  '/issues/:id': IssueDetail,
  '/code-review': CodeReview,
  '/code-review/:id': CodeReviewDetail,
  '/code-analysis': CodeAnalysis,
  '/users': Users,
  '/settings': Settings,
  '/settings/profile': () => <div>个人设置页面</div>,
  '/notifications': NotificationsPage,
};

// 创建临时页面组件，在开发阶段使用
const TemporaryPage: React.FC<{ title: string }> = ({ title }) => (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h1>{title}页面</h1>
    <p>该页面正在开发中...</p>
  </div>
);

const App: React.FC = () => {
  const dispatch = useDispatch();
  const menuInitialized = useSelector(selectMenuInitialized);
  const menus = useSelector(selectMenus);
  
  // 自动获取当前用户和菜单
  useEffect(() => {
    if (hasToken() && isLoggedIn()) {
      dispatch(fetchCurrentUser() as any);
      dispatch(fetchUserMenus() as any);
    }
  }, [dispatch]);
  
  // 生成动态路由配置
  const generateRoutes = () => {
    // 如果菜单未初始化或为空，返回兜底路由配置
    if (!menuInitialized || menus.length === 0) {
      console.log('菜单未初始化或为空，使用兜底路由');
      return Object.entries(pageComponents).map(([path, Component]) => (
        <Route 
          key={path} 
          path={path.replace(/^\//, '')} // 移除开头的斜杠，因为在父路由已添加
          element={<AuthRoute><Component /></AuthRoute>} 
        />
      ));
    }
    
    // 基于权限菜单生成路由
    const routeElements: React.ReactNode[] = [];
    
    // 递归处理菜单生成路由
    const processMenu = (menu: any) => {
      // 如果菜单没有路径，则跳过
      if (!menu.path) return null;
      
      // 移除路径开头的斜杠，避免嵌套路由问题
      const routePath = menu.path.replace(/^\//, '');
      // 查找对应的组件
      const Component = pageComponents[menu.path];
      
      if (Component) {
        // 返回带权限检查的路由
        return (
          <Route 
            key={menu.path} 
            path={routePath}
            element={<AuthRoute requiredPermission={menu.permission?.code}><Component /></AuthRoute>} 
          />
        );
      }
      
      // 如果没找到对应组件但有路径，生成临时页面
      return (
        <Route 
          key={menu.path} 
          path={routePath}
          element={<AuthRoute requiredPermission={menu.permission?.code}><TemporaryPage title={menu.title} /></AuthRoute>} 
        />
      );
    };
    
    // 处理所有菜单项
    const processMenus = (menuList: any[]) => {
      menuList.forEach(menu => {
        const route = processMenu(menu);
        if (route) routeElements.push(route);
        
        // 递归处理子菜单
        if (menu.children && menu.children.length > 0) {
          processMenus(menu.children);
        }
      });
    };
    
    // 处理顶级菜单
    processMenus(menus);
    console.log('生成的动态路由数量:', routeElements.length);
    
    return routeElements;
  };
  
  // 根据菜单生成路由
  const routes = generateRoutes();

  return (
    <ConfigProvider 
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#3b82f6',
          colorSuccess: '#10b981',
          colorWarning: '#f59e0b',
          colorError: '#ef4444',
          colorInfo: '#3b82f6',
          borderRadius: 6,
          colorBgContainer: '#ffffff',
          colorBgBase: '#f8fafc',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
        }
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/403" element={<Forbidden />} />
          <Route path="/404" element={<NotFound />} />
          
          {/* 需要登录验证的路由 */}
          <Route
            path="/"
            element={
              <AuthRoute>
                <BasicLayout />
              </AuthRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            {routes}
          </Route>

          {/* 未匹配的路由重定向到404 */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App; 