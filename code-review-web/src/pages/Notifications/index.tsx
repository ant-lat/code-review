import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Card, Table, Button, Space, Tag, Tooltip, 
  Popconfirm, Input, DatePicker, Select, 
  Typography, message, Badge, Tabs 
} from 'antd';
import { 
  BellOutlined, CheckOutlined, DeleteOutlined, 
  FilterOutlined, SearchOutlined, ReloadOutlined 
} from '@ant-design/icons';
import { Notification } from '../../api/notifications';
import { 
  fetchNotifications, fetchUnreadCount, 
  markAsRead, markAllAsRead, deleteNotification,
  deleteMultipleNotifications, fetchNotificationTypes
} from '../../store/slices/notificationSlice';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { useNavigate } from 'react-router-dom';
import './style.less';
import { getEnumList, getEnumItem } from '../../utils/enumUtils';
import Authorized from '../../components/Permission/index';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const NotificationsPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // 从Redux存储获取通知数据
  const { 
    notifications, unreadCount, loading, total, 
    notificationTypes, error 
  } = useSelector((state: AppState) => state.notification);
  
  // 本地状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [tabKey, setTabKey] = useState('all');
  
  // 过滤条件
  const [filters, setFilters] = useState({
    search: '',
    notificationType: undefined as string | undefined,
    dateRange: undefined as [dayjs.Dayjs, dayjs.Dayjs] | undefined,
  });
  
  // 初始化加载
  useEffect(() => {
    dispatch(fetchNotificationTypes() as any);
    loadNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch]);
  
  // 当过滤条件、页码或标签页变更时重新加载通知
  useEffect(() => {
    loadNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, pageSize, tabKey, filters]);
  
  // 显示错误消息
  useEffect(() => {
    if (error) {
      message.error(error);
    }
  }, [error]);
  
  // 加载通知列表
  const loadNotifications = () => {
    const params: any = {
      page: currentPage,
      page_size: pageSize,
      unread_only: tabKey === 'unread',
      notification_type: filters.notificationType,
      search: filters.search || undefined,
    };
    
    if (filters.dateRange) {
      params.from_date = filters.dateRange[0].format('YYYY-MM-DD');
      params.to_date = filters.dateRange[1].format('YYYY-MM-DD');
    }
    
    dispatch(fetchNotifications(params) as any);
    dispatch(fetchUnreadCount() as any);
  };
  
  // 处理行选择
  const onSelectChange = (newSelectedRowKeys: React.Key[]) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };
  
  // 处理标记为已读
  const handleMarkAsRead = (ids: number[]) => {
    dispatch(markAsRead(ids) as any);
    message.success('通知已标记为已读');
    setSelectedRowKeys([]);
  };
  
  // 处理删除通知
  const handleDelete = (ids: number[]) => {
    if (ids.length === 1) {
      dispatch(deleteNotification(ids[0]) as any);
    } else {
      dispatch(deleteMultipleNotifications(ids) as any);
    }
    message.success('通知已删除');
    setSelectedRowKeys([]);
  };
  
  // 处理标记所有为已读
  const handleMarkAllAsRead = () => {
    dispatch(markAllAsRead(filters.notificationType) as any);
    message.success('所有通知已标记为已读');
  };
  
  // 处理通知点击
  const handleNotificationClick = (notification: Notification) => {
    // 如果未读，则标记为已读
    if (!notification.is_read) {
      dispatch(markAsRead([notification.id]) as any);
    }
    
    // 根据通知类型导航到相应页面
    if (notification.link) {
      navigate(notification.link);
    } else if (notification.issue_id) {
      navigate(`/issues/${notification.issue_id}`);
    }
  };
  
  // 处理过滤条件重置
  const handleReset = () => {
    setFilters({
      search: '',
      notificationType: undefined,
      dateRange: undefined,
    });
    setCurrentPage(1);
  };
  
  // 获取通知类型列表（使用枚举工具）
  const notificationTypeList = getEnumList('notificationType');
  
  // 表格列定义
  const columns = [
    {
      title: '状态',
      dataIndex: 'is_read',
      key: 'is_read',
      width: 80,
      render: (isRead: boolean) => (
        isRead ? 
          <Tag color="default">已读</Tag> : 
          <Badge status="processing" text={<Tag color="blue">未读</Tag>} />
      ),
    },
    {
      title: '类型',
      dataIndex: 'notification_type',
      key: 'notification_type',
      width: 120,
      render: (type: string) => {
        // 使用枚举工具获取类型信息
        const typeInfo = getEnumItem('notificationType', type);
        return <Tag color={typeInfo?.color || 'purple'}>{typeInfo?.label || type}</Tag>;
      },
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: Notification) => (
        <a onClick={() => handleNotificationClick(record)}>
          {title}
        </a>
      ),
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (content: string) => (
        <Tooltip placement="topLeft" title={content}>
          <span>{content}</span>
        </Tooltip>
      ),
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
          {dayjs(date).fromNow()}
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Notification) => (
        <Space size="middle">
          {!record.is_read && (
            <Button
              type="text"
              icon={<CheckOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                handleMarkAsRead([record.id]);
              }}
            >
              已读
            </Button>
          )}
          <Authorized permissions="notification:delete">
            <Popconfirm
              title="确定要删除这条通知吗？"
              onConfirm={(e) => {
                e?.stopPropagation();
                handleDelete([record.id]);
              }}
              okText="是"
              cancelText="否"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={(e) => e.stopPropagation()}
              >
                删除
              </Button>
            </Popconfirm>
          </Authorized>
        </Space>
      ),
    },
  ];
  
  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
  };
  
  // 批量操作按钮
  const batchActions = (
    <Space size="middle">
      <Button
        icon={<CheckOutlined />}
        disabled={selectedRowKeys.length === 0}
        onClick={() => handleMarkAsRead(selectedRowKeys.map(key => Number(key)))}
      >
        标记已读
      </Button>
      <Authorized permissions="notification:delete">
        <Popconfirm
          title="确定要删除选中的通知吗？"
          onConfirm={() => handleDelete(selectedRowKeys.map(key => Number(key)))}
          okText="是"
          cancelText="否"
        >
          <Button
            icon={<DeleteOutlined />}
            disabled={selectedRowKeys.length === 0}
            danger
          >
            批量删除
          </Button>
        </Popconfirm>
      </Authorized>
      <Button
        icon={<CheckOutlined />}
        onClick={handleMarkAllAsRead}
      >
        全部已读
      </Button>
    </Space>
  );
  
  // 过滤表单
  const filterForm = (
    <div className="notification-filter">
      <Space wrap>
        <Input
          placeholder="搜索通知"
          value={filters.search}
          onChange={(e) => setFilters({...filters, search: e.target.value})}
          prefix={<SearchOutlined />}
          style={{ width: 200 }}
          allowClear
        />
        <Select
          placeholder="通知类型"
          value={filters.notificationType}
          onChange={(value) => setFilters({...filters, notificationType: value})}
          style={{ width: 150 }}
          allowClear
        >
          {notificationTypeList.map(type => (
            <Option key={type.value} value={type.value}>{type.label}</Option>
          ))}
        </Select>
        <RangePicker
          placeholder={['开始日期', '结束日期']}
          value={filters.dateRange}
          onChange={(dates) => setFilters({...filters, dateRange: dates as [dayjs.Dayjs, dayjs.Dayjs]})}
        />
        <Button icon={<FilterOutlined />} onClick={loadNotifications}>过滤</Button>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>重置</Button>
      </Space>
    </div>
  );
  
  return (
    <div className="notification-page">
      <Card>
        <div className="notification-header">
          <Title level={4}><BellOutlined /> 通知中心</Title>
          <div>{batchActions}</div>
        </div>
        
        {filterForm}
        
        <Tabs activeKey={tabKey} onChange={setTabKey}>
          <TabPane tab="全部通知" key="all" />
          <TabPane tab={`未读通知 (${unreadCount})`} key="unread" />
        </Tabs>
        
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={notifications as Notification[]}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条通知`,
            onChange: (page, size) => {
              setCurrentPage(page);
              if (size !== pageSize) {
                setPageSize(size);
              }
            },
          }}
          onRow={(record: Notification) => ({
            onClick: () => handleNotificationClick(record),
            className: record.is_read ? '' : 'unread-row',
          })}
        />
      </Card>
    </div>
  );
};

export default NotificationsPage; 