import React, { useEffect, useState } from 'react';
import { Badge, Button, Dropdown, List, Tabs, Tooltip, Empty, message } from 'antd';
import { useDispatch, useSelector } from 'react-redux';
import { BellOutlined, CheckOutlined } from '@ant-design/icons';
import { fetchNotifications, fetchUnreadCount, markAllAsRead } from '../../store/slices/notificationSlice';
import { Notification } from '../../api/notifications';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import './NotificationMenu.less';
import { useNavigate } from 'react-router-dom';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const NotificationMenu: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('all');

  const { notifications, unreadCount, loading } = useSelector((state: AppState) => state.notification);

  useEffect(() => {
    // 获取未读通知数量
    dispatch(fetchUnreadCount() as any);
    
    // 初始加载通知
    if (open) {
      dispatch(fetchNotifications({
        page: 1,
        page_size: 5,
        unread_only: activeTab === 'unread'
      }) as any);
    }
  }, [dispatch, open, activeTab]);

  // 处理通知点击
  const handleNotificationClick = (notification: Notification) => {
    // 根据通知类型跳转到不同页面
    if (notification.link) {
      navigate(notification.link);
    } else if (notification.issue_id) {
      navigate(`/issues/${notification.issue_id}`);
    }
    setOpen(false);
  };

  // 标记所有通知为已读
  const handleMarkAllAsRead = () => {
    dispatch(markAllAsRead() as any);
    message.success('所有通知已标记为已读');
  };

  // 查看所有通知
  const handleViewAll = () => {
    navigate('/notifications');
    setOpen(false);
  };

  // 通知内容渲染
  const notificationList = (
    <div className="notification-dropdown">
      <div className="notification-header">
        <h3>通知</h3>
        <Button
          type="link"
          onClick={handleMarkAllAsRead}
          icon={<CheckOutlined />}
          disabled={unreadCount === 0}
        >
          全部已读
        </Button>
      </div>
      
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key)}
        items={[
          { key: 'all', label: '全部' },
          { key: 'unread', label: `未读 (${unreadCount})` }
        ]}
      />
      
      <div className="notification-content">
        {loading ? (
          <div className="notification-loading">加载中...</div>
        ) : notifications && notifications.length > 0 ? (
          <List
            dataSource={notifications as Notification[]}
            renderItem={(item: Notification) => (
              <List.Item
                className={`notification-item ${!item.is_read ? 'notification-unread' : ''}`}
                onClick={() => handleNotificationClick(item)}
              >
                <div className="notification-icon">
                  {/* 可以根据通知类型添加不同图标 */}
                  <BellOutlined />
                </div>
                <div className="notification-details">
                  <div className="notification-title">{item.title}</div>
                  <div className="notification-content">{item.content}</div>
                  <div className="notification-time">{dayjs(item.created_at).fromNow()}</div>
                </div>
              </List.Item>
            )}
          />
        ) : (
          <Empty description="暂无通知" />
        )}
      </div>
      
      <div className="notification-footer">
        <Button type="link" onClick={handleViewAll}>
          查看所有通知
        </Button>
      </div>
    </div>
  );

  return (
    <Dropdown
      dropdownRender={() => notificationList}
      trigger={['click']}
      open={open}
      onOpenChange={setOpen}
      placement="bottomRight"
    >
      <div className="notification-bell">
        <Tooltip title="通知中心">
          <Badge count={unreadCount} overflowCount={99}>
            <BellOutlined style={{ fontSize: '18px', cursor: 'pointer' }} />
          </Badge>
        </Tooltip>
      </div>
    </Dropdown>
  );
};

export default NotificationMenu; 