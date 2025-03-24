import React from 'react';
import NotificationsPage from '../pages/Notifications';

// 导出通知页面路由配置
export const notificationRoute = {
  path: '/notifications',
  element: <NotificationsPage />,
};

// 导出所有路由配置
export const routes = [
  notificationRoute,
  // 可以在这里添加其他路由
];

export default routes; 