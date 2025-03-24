import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Space, 
  Input, 
  Select, 
  Tag, 
  message,
  Tooltip,
  Badge,
  Dropdown,
  Menu,
  DatePicker,
  Row,
  Col,
  Modal,
  TableProps
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { 
  SearchOutlined, 
  PlusOutlined, 
  SyncOutlined, 
  ExclamationCircleOutlined,
  QuestionCircleOutlined,
  CheckCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
  EditOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { CanceledError } from 'axios';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';
import { getIssues, deleteIssue } from '../../api/issues';
import { getProjects } from '../../api/projects';
import { getUsers } from '../../api/users';
import { formatDateTime, formatRelativeTime } from '../../utils';
import { cancelAllRequests } from '../../api/request';
import IssueForm from './components/IssueForm';
import { Table } from '../../components'; // 导入自定义Table组件
import './issues.css';

const { Option } = Select;
const { RangePicker } = DatePicker;

// 状态映射
const statusMap: Record<string, {color: string; label: string}> = {
  'open': { color: '#1890ff', label: '待处理' },
  'in_progress': { color: '#faad14', label: '处理中' },
  'resolved': { color: '#52c41a', label: '已解决' },
  'closed': { color: '#d9d9d9', label: '已关闭' },
};

// 优先级映射
const priorityMap: Record<string, {color: string; label: string}> = {
  'high': { color: '#f5222d', label: '高' },
  'medium': { color: '#faad14', label: '中' },
  'low': { color: '#52c41a', label: '低' },
};

// 问题类型映射
const issueTypeMap: Record<string, {label: string}> = {
  'bug': { label: '缺陷' },
  'feature': { label: '功能' },
  'task': { label: '任务' },
  'enhancement': { label: '改进' },
  'documentation': { label: '文档' },
  'code_review': { label: '代码检视' },
};

interface TagItem {
  id: number;
  name: string;
  color: string;
}

interface IssueItem {
  id: number;
  title: string;
  project_id: number;
  project_name: string;
  status: string;
  priority: string;
  issue_type?: string;
  creator_id?: number;
  creator_name?: string;  // 兼容reporter_name
  reporter_id?: number;   // 兼容Issue类型
  reporter_name?: string; // 兼容Issue类型
  assignee_id?: number;
  assignee_name?: string;
  created_at: string;
  updated_at: string;
  tags?: TagItem[];
  severity?: string;      // 兼容Issue类型
  description?: string;   // 兼容Issue类型
  closed_at?: string;     // 兼容Issue类型
  due_date?: string;      // 兼容Issue类型
  labels?: string[];      // 兼容Issue类型
  related_issues?: number[]; // 兼容Issue类型
  [key: string]: any;     // 添加索引签名，允许其他任意属性
}

const IssuesPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<IssueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 });
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentIssue, setCurrentIssue] = useState<IssueItem | null>(null);
  
  // 加载状态
  const [projectLoading, setProjectLoading] = useState(false);
  const [userLoading, setUserLoading] = useState(false);
  
  // 数据列表
  const [projects, setProjects] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  
  // 筛选条件 - 与后端API参数对齐
  const [projectId, setProjectId] = useState<number | undefined>(
    queryParams.get('projectId') ? Number(queryParams.get('projectId')) : undefined
  );
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [priority, setPriority] = useState<string | undefined>(undefined);
  const [assigneeId, setAssigneeId] = useState<number | undefined>(undefined);
  const [creatorId, setCreatorId] = useState<number | undefined>(undefined);
  const [issueType, setIssueType] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<any>(undefined);
  const [keyword, setKeyword] = useState('');
  
  // 排序
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // 是否显示高级筛选
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);

  // 获取问题列表
  const fetchIssues = async () => {
    setLoading(true);
    try {
      // 从日期范围中提取创建时间范围
      let createdAfter, createdBefore;
      if (dateRange && dateRange[0] && dateRange[1]) {
        createdAfter = dateRange[0].format('YYYY-MM-DD');
        createdBefore = dateRange[1].format('YYYY-MM-DD');
      }
      
      // 调用API，参数与后端完全匹配
      const res = await getIssues({
        page: pagination.current,
        page_size: pagination.pageSize,
        project_id: projectId,
        status,
        priority,
        assignee_id: assigneeId,
        creator_id: creatorId,
        issue_type: issueType,
        created_after: createdAfter,
        created_before: createdBefore,
        keyword: keyword || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      });
      
      // 确保响应数据是正确的格式
      if (res && res.data) {
        // 处理嵌套响应格式
        let issueItems: IssueItem[] = [];
        let totalItems = 0;
        
        // 转换函数：从API的Issue类型转换为组件的IssueItem类型
        const mapIssueToIssueItem = (item: any): IssueItem => ({
          id: item.id,
          title: item.title,
          project_id: item.project_id,
          project_name: item.project_name || '',
          status: item.status,
          priority: item.priority || 'medium',
          issue_type: item.issue_type,
          creator_name: item.reporter_name || item.creator_name || '',
          reporter_id: item.reporter_id,
          reporter_name: item.reporter_name,
          creator_id: item.creator_id || item.reporter_id,
          assignee_id: item.assignee_id,
          assignee_name: item.assignee_name,
          created_at: item.created_at,
          updated_at: item.updated_at || item.created_at,
          tags: item.tags || [],
          severity: item.severity,
          description: item.description,
          closed_at: item.closed_at,
          due_date: item.due_date,
          labels: item.labels,
          related_issues: item.related_issues,
          ...item // 包含任何其他可能的字段
        });
        
        if (Array.isArray(res.data)) {
          // 标准格式
          issueItems = res.data.map(mapIssueToIssueItem);
          totalItems = res.total || 0;
        } else if (typeof res.data === 'object') {
          // 嵌套格式，适配PageResponse格式
          const nestedData = res.data as any;
          if (nestedData.items && Array.isArray(nestedData.items)) {
            issueItems = nestedData.items.map(mapIssueToIssueItem);
            totalItems = nestedData.total || 0;
          } else if (nestedData.data && Array.isArray(nestedData.data)) {
            issueItems = nestedData.data.map(mapIssueToIssueItem);
            
            // 尝试从不同位置获取总数
            if (nestedData.page_info && typeof nestedData.page_info.total === 'number') {
              totalItems = nestedData.page_info.total;
            } else if (typeof nestedData.total === 'number') {
              totalItems = nestedData.total;
            } else if (typeof res.total === 'number') {
              totalItems = res.total;
            }
          }
        }
        
        // 设置数据
        setData(issueItems);
        setTotal(totalItems);
        
        console.log('问题列表数据:', issueItems);
      } else {
        console.warn('问题列表数据格式不符合预期:', res);
        setData([]);
        setTotal(0);
      }
    } catch (error) {
      // 如果是取消请求导致的错误，不显示错误信息
      if (!(error instanceof CanceledError)) {
        console.error('获取问题列表失败:', error);
        message.error('获取问题列表失败');
      }
      // 保持数据为数组类型
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取项目列表
  const fetchProjects = async () => {
    setProjectLoading(true);
    try {
      const res = await getProjects();
      
      // 避免在组件卸载后设置状态
      if (!projectLoading) return;
      
      // 处理不同的响应格式
      let projectList: any[] = [];
      
      if (res && res.data) {
        if (typeof res.data === 'object' && res.data.items && Array.isArray(res.data.items)) {
          projectList = res.data.items;
        } else if (Array.isArray(res.data)) {
          projectList = res.data;
        } else {
          console.warn('项目数据格式不符合预期:', res);
        }
      }
      
      setProjects(projectList);
    } catch (error) {
      // 如果是取消请求导致的错误，不显示错误信息
      if (!(error instanceof CanceledError)) {
        console.error('获取项目列表错误:', error);
        message.error('获取项目列表失败');
      }
      setProjects([]);
    } finally {
      setProjectLoading(false);
    }
  };

  // 获取用户列表
  const fetchUsers = async () => {
    setUserLoading(true);
    try {
      const res = await getUsers();
      let userList: any[] = [];
      
      if (res && res.data) {
        if (typeof res.data === 'object' && res.data.items && Array.isArray(res.data.items)) {
          userList = res.data.items;
        } else if (Array.isArray(res.data)) {
          userList = res.data;
        }
      }
      
      setUsers(userList);
    } catch (error) {
      if (!(error instanceof CanceledError)) {
        console.error('获取用户列表失败:', error);
        message.error('获取用户列表失败');
      }
    } finally {
      setUserLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchProjects();
    fetchUsers();
    
    // 组件卸载时取消请求
    return () => {
      controller.abort();
      cancelAllRequests();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchIssues();
    
    // 组件卸载时取消请求
    return () => {
      controller.abort();
      cancelAllRequests();
    };
  }, [
    pagination.current, 
    pagination.pageSize, 
    projectId, 
    status, 
    priority, 
    assigneeId, 
    creatorId,
    issueType,
    sortBy,
    sortOrder
  ]);

  // 处理表格变化
  const handleTableChange: TableProps<IssueItem>['onChange'] = (pagination, filters, sorter) => {
    setPagination(pagination as any);
    
    // 处理排序
    if (sorter && 'field' in sorter && 'order' in sorter) {
      const sortInfo = sorter as { field: string; order: string };
      if (sortInfo.field && sortInfo.order) {
        setSortBy(sortInfo.field);
        setSortOrder(sortInfo.order === 'ascend' ? 'asc' : 'desc');
      }
    }
  };

  // 处理搜索
  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    fetchIssues();
  };

  // 重置筛选条件
  const handleReset = () => {
    setProjectId(undefined);
    setStatus(undefined);
    setPriority(undefined);
    setAssigneeId(undefined);
    setCreatorId(undefined);
    setIssueType(undefined);
    setDateRange(undefined);
    setKeyword('');
    setSortBy('created_at');
    setSortOrder('desc');
    setPagination({ ...pagination, current: 1 });
  };
  
  // 处理编辑问题
  const handleEditIssue = (record: IssueItem) => {
    setCurrentIssue(record);
    setEditModalVisible(true);
  };

  // 根据优先级返回图标
  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <ExclamationCircleOutlined style={{ color: '#f5222d' }} />;
      case 'medium':
        return <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />;
      case 'low':
        return <QuestionCircleOutlined style={{ color: '#1890ff' }} />;
      default:
        return <QuestionCircleOutlined />;
    }
  };

  // 处理项目选择变化
  const handleProjectChange = (value: number | undefined) => {
    setProjectId(value);
    setPagination({ ...pagination, current: 1 });
  };

  // 处理创建完成
  const handleCreateFinish = () => {
    setCreateModalVisible(false);
    setPagination({ ...pagination, current: 1 });
    fetchIssues();
  };
  
  // 处理编辑完成
  const handleEditFinish = () => {
    setEditModalVisible(false);
    fetchIssues();
  };

  // 处理表格行点击
  const handleRowClick = (record: IssueItem) => {
    return {
      onClick: () => {
        navigate(`/issues/${record.id}`);
      },
    };
  };

  // 点击编辑按钮
  const handleEdit = (record: IssueItem) => {
    setCurrentIssue(record);
    setEditModalVisible(true);
  };

  // 点击删除按钮
  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个问题吗？此操作不可逆。',
      okText: '确认',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          // 实际删除逻辑
          const res = await deleteIssue(id);
          if (res.success) {
            message.success('删除成功');
            fetchData(pagination.current, pagination.pageSize);
          } else {
            message.error(res.message || '删除失败');
          }
        } catch (error) {
          console.error('删除问题时出错:', error);
          message.error('删除失败');
        }
      }
    });
  };

  // 表格列定义
  const columns: ColumnsType<IssueItem> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
      sorter: true,
      sortOrder: sortBy === 'id' 
        ? (sortOrder === 'asc' ? 'ascend' : 'descend') 
        : undefined,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text: string, record: IssueItem) => (
        <Space>
          {getPriorityIcon(record.priority)}
          <a onClick={() => navigate(`/issues/${record.id}`)}>{text}</a>
          {record.tags && record.tags.length > 0 && (
            <span>
              {record.tags.slice(0, 2).map((tag) => (
                <Tag key={tag.id} color={tag.color || '#1890ff'} style={{ marginLeft: 4 }}>
                  {tag.name}
                </Tag>
              ))}
              {record.tags.length > 2 && <Tag>+{record.tags.length - 2}</Tag>}
            </span>
          )}
        </Space>
      ),
    },
    {
      title: '项目',
      dataIndex: 'project_name',
      key: 'project_name',
      width: 140,
      ellipsis: true,
      render: (text: string, record: IssueItem) => (
        <Tooltip title="查看项目">
          <Button 
            type="link" 
            size="small" 
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/projects/${record.project_id}`);
            }}
          >
            {text}
          </Button>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      sorter: true,
      sortOrder: sortBy === 'status' 
        ? (sortOrder === 'asc' ? 'ascend' : 'descend') 
        : undefined,
      render: (status: string) => (
        <Badge 
          status={(statusMap[status]?.color || 'default') as any} 
          text={statusMap[status]?.label || status}
          className="status-badge"
        />
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 90,
      sorter: true,
      sortOrder: sortBy === 'priority' 
        ? (sortOrder === 'asc' ? 'ascend' : 'descend') 
        : undefined,
      render: (priority: string) => (
        <Tag 
          color={priorityMap[priority]?.color || 'default'}
          className="priority-tag"
        >
          {priorityMap[priority]?.label || priority}
        </Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 90,
      sorter: true,
      sortOrder: sortBy === 'issue_type' 
        ? (sortOrder === 'asc' ? 'ascend' : 'descend') 
        : undefined,
      render: (type: string) => issueTypeMap[type]?.label || type || '-',
    },
    {
      title: '创建者',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 100,
      ellipsis: true,
    },
    {
      title: '被分配人',
      dataIndex: 'assignee_name',
      key: 'assignee_name',
      width: 100,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      sorter: true,
      sortOrder: sortBy === 'created_at' 
        ? (sortOrder === 'asc' ? 'ascend' : 'descend') 
        : undefined,
      render: (date: string) => formatDateTime(date),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 150,
      sorter: true,
      sortOrder: sortBy === 'updated_at' 
        ? (sortOrder === 'asc' ? 'ascend' : 'descend') 
        : undefined,
      render: (date: string) => (
        <Tooltip title={formatDateTime(date)}>
          {formatRelativeTime(date)}
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (text: string, record: IssueItem) => (
        <div>
          <Permission roles={['admin', 'developer', 'user']}>
            <Button 
              className="action-button edit-button"
              type="link" 
              onClick={(e) => {
                e.stopPropagation();
                handleEditIssue(record);
              }}
            >
              编辑
            </Button>
          </Permission>
          <Permission roles={['admin']}>
            <Button 
              className="action-button delete-button"
              type="link" 
              danger 
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(record.id);
              }}
            >
              删除
            </Button>
          </Permission>
        </div>
      ),
    },
  ];

  return (
    <div className="issues-page">
      <div className="page-header">
        <div className="page-title">问题列表</div>
        <div className="page-actions">
          <Permission roles={['admin', 'developer', 'user']}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              新建问题
            </Button>
          </Permission>
        </div>
      </div>

      <Card className="filter-card">
        <div className="basic-filters">
          <Space wrap size="middle">
            <div className="filter-item">
              <span className="filter-label">项目：</span>
              <Select
                style={{ width: 180 }}
                placeholder="请选择项目"
                value={projectId}
                onChange={handleProjectChange}
                loading={projectLoading}
                allowClear
              >
                <Option value={undefined}>全部项目</Option>
                {projects.map(project => (
                  <Option key={project.id} value={project.id}>
                    {project.name}
                  </Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <span className="filter-label">状态：</span>
              <Select
                style={{ width: 120 }}
                placeholder="状态"
                value={status}
                onChange={value => setStatus(value)}
                allowClear
              >
                {Object.entries(statusMap).map(([key, value]) => (
                  <Option key={key} value={key}>{value.label}</Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <span className="filter-label">优先级：</span>
              <Select
                style={{ width: 120 }}
                placeholder="优先级"
                value={priority}
                onChange={value => setPriority(value)}
                allowClear
              >
                {Object.entries(priorityMap).map(([key, value]) => (
                  <Option key={key} value={key}>{value.label}</Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <Input
                placeholder="搜索问题标题或描述"
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                onPressEnter={handleSearch}
                style={{ width: 200 }}
                suffix={
                  <SearchOutlined onClick={handleSearch} style={{ cursor: 'pointer' }} />
                }
              />
            </div>
            <Button type="primary" onClick={handleSearch}>
              搜索
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleReset}
              title="重置筛选条件"
            >
              重置
            </Button>
            <Button 
              type={showAdvancedFilter ? "primary" : "default"}
              icon={<FilterOutlined />} 
              onClick={() => setShowAdvancedFilter(!showAdvancedFilter)}
            >
              高级筛选
            </Button>
          </Space>
        </div>

        {showAdvancedFilter && (
          <div className="advanced-filters" style={{ marginTop: 16 }}>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <div className="filter-item">
                  <span className="filter-label">问题类型：</span>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="问题类型"
                    value={issueType}
                    onChange={value => setIssueType(value)}
                    allowClear
                  >
                    {Object.entries(issueTypeMap).map(([key, value]) => (
                      <Option key={key} value={key}>{value.label}</Option>
                    ))}
                  </Select>
                </div>
              </Col>
              <Col span={6}>
                <div className="filter-item">
                  <span className="filter-label">指派给：</span>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="指派给"
                    value={assigneeId}
                    onChange={value => setAssigneeId(value)}
                    loading={userLoading}
                    allowClear
                  >
                    {users.map(user => (
                      <Option key={user.id} value={user.id}>{user.username}</Option>
                    ))}
                  </Select>
                </div>
              </Col>
              <Col span={6}>
                <div className="filter-item">
                  <span className="filter-label">创建者：</span>
                  <Select
                    style={{ width: '100%' }}
                    placeholder="创建者"
                    value={creatorId}
                    onChange={value => setCreatorId(value)}
                    loading={userLoading}
                    allowClear
                  >
                    {users.map(user => (
                      <Option key={user.id} value={user.id}>{user.username}</Option>
                    ))}
                  </Select>
                </div>
              </Col>
              <Col span={12}>
                <div className="filter-item">
                  <span className="filter-label">创建时间：</span>
                  <RangePicker
                    style={{ width: '100%' }}
                    value={dateRange}
                    onChange={value => setDateRange(value)}
                  />
                </div>
              </Col>
              <Col span={12}>
                <div className="filter-item">
                  <span className="filter-label">排序：</span>
                  <Select
                    style={{ width: 160 }}
                    value={sortBy}
                    onChange={value => setSortBy(value)}
                  >
                    <Option value="created_at">创建时间</Option>
                    <Option value="updated_at">更新时间</Option>
                    <Option value="priority">优先级</Option>
                    <Option value="status">状态</Option>
                    <Option value="id">ID</Option>
                  </Select>
                  <Select
                    style={{ width: 120, marginLeft: 8 }}
                    value={sortOrder}
                    onChange={value => setSortOrder(value)}
                  >
                    <Option value="asc">升序</Option>
                    <Option value="desc">降序</Option>
                  </Select>
                </div>
              </Col>
            </Row>
          </div>
        )}
      </Card>

      <Card className="issues-table">
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          onRow={handleRowClick}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => setPagination({ current: page, pageSize: pageSize || 10 }),
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title="创建问题"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        <IssueForm 
          onFinish={handleCreateFinish}
          projects={projects}
          users={users}
        />
      </Modal>
      
      <Modal
        title="编辑问题"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        {currentIssue && (
          <IssueForm 
            initialValues={currentIssue}
            onFinish={handleEditFinish} 
            projects={projects}
            users={users}
            isEdit
          />
        )}
      </Modal>
    </div>
  );
};

export default IssuesPage; 