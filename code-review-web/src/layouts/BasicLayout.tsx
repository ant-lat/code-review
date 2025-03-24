import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Breadcrumb, Dropdown, Avatar, Badge, message } from 'antd';
import {
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  UserOutlined,
  BellOutlined,
  LogoutOutlined,
  SettingOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import SideMenu from './SideMenu';
import { selectMenus } from '../store/slices/menuSlice';
import { getCurrentUser, logout } from '../utils/auth';
import './BasicLayout.less';

const { Header, Sider, Content } = Layout;

/**
 * 基础布局组件
 */
const BasicLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>([]);
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const menus = useSelector(selectMenus);
  const currentUser = getCurrentUser();
  
  // 根据路径生成面包屑
  useEffect(() => {
    const pathParts = location.pathname.split('/').filter(Boolean);
    
    // 根据菜单数据找到当前路径对应的菜单项和父级菜单
    if (menus.length > 0) {
      const breadcrumbItems: string[] = ['首页'];
      
      // 递归查找菜单和父菜单
      const findBreadcrumbPath = (menuItems: any[], path: string, currentPath = ''): boolean => {
        for (const item of menuItems) {
          const itemPath = item.path || '';
          const fullPath = itemPath.startsWith('/') ? itemPath : `${currentPath}/${itemPath}`;
          
          if (fullPath === path) {
            breadcrumbItems.push(item.title);
            return true;
          }
          
          if (item.children && item.children.length > 0) {
            if (findBreadcrumbPath(item.children, path, fullPath)) {
              breadcrumbItems.splice(1, 0, item.title);
              return true;
            }
          }
        }
        return false;
      };
      
      findBreadcrumbPath(menus, location.pathname);
      
      // 如果没找到，使用路径分割生成
      if (breadcrumbItems.length === 1 && pathParts.length > 0) {
        breadcrumbItems.push(...pathParts.map(part => part.charAt(0).toUpperCase() + part.slice(1)));
      }
      
      setBreadcrumbs(breadcrumbItems);
    } else {
      // 如果没有菜单数据，使用路径部分生成面包屑
      const newBreadcrumbs = ['首页'];
      if (pathParts.length > 0) {
        newBreadcrumbs.push(...pathParts.map(part => part.charAt(0).toUpperCase() + part.slice(1)));
      }
      setBreadcrumbs(newBreadcrumbs);
    }
  }, [location.pathname, menus]);
  
  // 切换菜单折叠状态
  const toggle = () => {
    setCollapsed(!collapsed);
  };
  
  // 处理退出登录
  const handleLogout = () => {
    logout();
    message.success('已退出登录');
    navigate('/login');
  };
  
  // 处理导航到个人设置
  const handleGoToProfile = () => {
    navigate('/settings/profile');
  };
  
  // 处理导航到通知中心
  const handleGoToNotifications = () => {
    navigate('/notifications');
  };
  
  // 用户下拉菜单
  const userMenu = (
    <Menu>
      <Menu.Item key="profile" onClick={handleGoToProfile} icon={<UserOutlined />}>
        个人资料
      </Menu.Item>
      <Menu.Item key="settings" onClick={() => navigate('/settings')} icon={<SettingOutlined />}>
        系统设置
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" onClick={handleLogout} icon={<LogoutOutlined />}>
        退出登录
      </Menu.Item>
    </Menu>
  );
  
  return (
    <Layout className="basic-layout">
      <Sider trigger={null} collapsible collapsed={collapsed} width={256} theme="dark">
        <div className="logo">
          <AppstoreOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          {!collapsed && <h1>代码检视系统</h1>}
        </div>
        
        {/* 使用动态生成的侧边栏菜单 */}
        <SideMenu />
      </Sider>
      
      <Layout className="site-layout">
        <Header className="site-layout-header">
          {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
            className: 'trigger',
            onClick: toggle,
          })}
          
          <div className="header-right">
            <Badge count={5} className="notification-badge">
              <BellOutlined className="header-icon" onClick={handleGoToNotifications} />
            </Badge>
            
            <Dropdown overlay={userMenu} placement="bottomRight">
              <div className="user-info">
                <Avatar size="small" icon={<UserOutlined />} />
                <span className="username">{currentUser?.username || '用户'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        
        <Content className="site-layout-content">
          <Breadcrumb className="breadcrumb">
            {breadcrumbs.map((item, index) => (
              <Breadcrumb.Item key={index}>{item}</Breadcrumb.Item>
            ))}
          </Breadcrumb>
          
          <div className="main-content">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default BasicLayout; 