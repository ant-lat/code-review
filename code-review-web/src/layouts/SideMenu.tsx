import React, { useState, useEffect } from 'react';
import { Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import * as Icons from '@ant-design/icons';
import { useSelector } from 'react-redux';
import { selectMenus } from '../store/slices/menuSlice';
import { Menu as MenuType } from '../api/permission';

// 动态加载图标组件
const getIconComponent = (iconName: string) => {
  // @ts-ignore
  const Icon = Icons[iconName];
  if (Icon) {
    return <Icon />;
  }
  // 默认图标
  return <Icons.AppstoreOutlined />;
};

// 递归生成菜单项
const renderMenuItems = (menuList: MenuType[]) => {
  return menuList.map((menu) => {
    // 如果有子菜单，递归生成
    if (menu.children && menu.children.length > 0) {
      return (
        <Menu.SubMenu
          key={menu.path || `menu-${menu.id}`}
          title={menu.title}
          icon={menu.icon ? getIconComponent(menu.icon) : <Icons.FolderOutlined />}
        >
          {renderMenuItems(menu.children)}
        </Menu.SubMenu>
      );
    }

    // 没有子菜单，创建单个菜单项
    return (
      <Menu.Item 
        key={menu.path || `menu-${menu.id}`}
        icon={menu.icon ? getIconComponent(menu.icon) : <Icons.FileOutlined />}
      >
        {menu.path ? (
          <Link to={menu.path}>{menu.title}</Link>
        ) : (
          menu.title
        )}
      </Menu.Item>
    );
  });
};

// 兜底菜单项，在没有动态菜单时使用
const fallbackMenuItems = [
  {
    key: 'dashboard',
    icon: <Icons.DashboardOutlined />,
    label: <Link to="/dashboard">仪表盘</Link>,
  },
  {
    key: 'projects',
    icon: <Icons.ProjectOutlined />,
    label: <Link to="/projects">项目管理</Link>,
  },
  {
    key: 'code-review',
    icon: <Icons.CodeOutlined />,
    label: <Link to="/code-review">代码审查</Link>,
  },
  {
    key: 'issues', 
    icon: <Icons.BugOutlined />,
    label: <Link to="/issues">问题追踪</Link>,
  },
  {
    key: 'code-analysis',
    icon: <Icons.BarChartOutlined />,
    label: <Link to="/code-analysis">代码分析</Link>,
  },
  {
    key: 'users',
    icon: <Icons.UserOutlined />,
    label: <Link to="/users">用户管理</Link>,
  },
  {
    key: 'settings',
    icon: <Icons.SettingOutlined />,
    label: <Link to="/settings">系统设置</Link>,
  },
  {
    key: 'notifications',
    icon: <Icons.BellOutlined />,
    label: <Link to="/notifications">通知中心</Link>,
  }
];

const SideMenu: React.FC = () => {
  const location = useLocation();
  const menus = useSelector(selectMenus);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  // 根据当前路径设置选中的菜单项
  useEffect(() => {
    const pathKey = location.pathname;
    setSelectedKeys([pathKey]);
    
    // 找到当前菜单的所有父级菜单，并打开它们
    if (menus.length > 0) {
      const findParentKeys = (menuItems: MenuType[], path: string, parents: string[] = []): string[] => {
        for (const item of menuItems) {
          if (item.path === path) {
            return parents;
          }
          if (item.children && item.children.length > 0) {
            const itemKey = item.path || `menu-${item.id}`;
            const found = findParentKeys(item.children, path, [...parents, itemKey]);
            if (found.length) {
              return found;
            }
          }
        }
        return [];
      };
      
      const parentKeys = findParentKeys(menus, pathKey);
      if (parentKeys.length > 0) {
        setOpenKeys(parentKeys);
      }
    }
  }, [location.pathname, menus]);

  // 处理子菜单展开/收起
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={selectedKeys}
      openKeys={openKeys}
      onOpenChange={handleOpenChange}
      items={menus.length > 0 ? undefined : fallbackMenuItems}
      className="side-menu-custom"
    >
      {menus.length > 0 && renderMenuItems(menus)}
    </Menu>
  );
};

export default SideMenu; 