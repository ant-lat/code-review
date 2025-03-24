import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Space, Tag, Input, Select, Popconfirm, message, Modal, Form, Switch, Dropdown, Menu, Tooltip, Radio } from 'antd';
import { 
  SearchOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  TeamOutlined,
  EyeOutlined,
  FilterOutlined,
  ReloadOutlined,
  StarOutlined,
  StarFilled,
  DownOutlined,
  SortAscendingOutlined,
  ExportOutlined,
  FileExcelOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { CanceledError } from 'axios';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';
import { Table } from '../../components';
import { getProjects, deleteProject, createProject, updateProject } from '../../api/projects';
import type { ProjectQueryParams, PageResponse, Project } from '../../api/types';
import { formatDateTime, exportToExcel } from '../../utils';
import { cancelAllRequests } from '../../api/request';
import ProjectForm from './components/ProjectForm';
import './index.less';

const { Option } = Select;

interface PaginationType {
  current: number;
  pageSize: number;
  total?: number;
}

const ProjectsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState<PaginationType>({
    current: 1,
    pageSize: 10
  });
  const [searchText, setSearchText] = useState('');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [filterVisible, setFilterVisible] = useState(false);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [starredProjects, setStarredProjects] = useState<number[]>([]);
  const [sortField, setSortField] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const abortControllerRef = useRef<AbortController | null>(null);
  const [form] = Form.useForm();

  const navigate = useNavigate();

  // 获取项目列表数据
  const fetchProjects = async (params?: ProjectQueryParams) => {
    setLoading(true);
    try {
      const res = await getProjects(params || {
        page: pagination.current,
        page_size: pagination.pageSize,
        name: searchText || undefined,
        sort_by: sortField,
        sort_order: sortOrder,
        ...filters
      });
      
      console.log('项目列表API返回数据:', res);
      
      // 处理后端返回的数据结构
      if (res.code === 200 && res.data) {
        // 将后端返回的数据结构映射到前端需要的格式
        const projects = res.data.items.map((item: any) => ({
          id: item.id,
          name: item.name,
          description: item.description,
          repository_url: item.repository_url,
          repository_type: item.repository_type,
          branch: item.branch,
          is_active: item.status,
          created_at: item.created_at,
          updated_at: item.updated_at,
          created_by: item.creator.id,
          owner_id: item.creator.id,
          member_count: item.member_count,
          creator: item.creator
        }));

        setData(projects);
        setTotal(res.data.total);
        setPagination({
          current: res.data.page,
          pageSize: res.data.page_size,
          total: res.data.total
        });
      } else {
        message.error(res.message || '获取项目列表失败');
        setData([]);
        setTotal(0);
      }
    } catch (error) {
      if (error instanceof CanceledError) {
        console.log('请求已取消');
      } else {
        console.error('获取项目列表失败:', error);
        message.error('获取项目列表失败');
      }
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects({
      page: pagination.current,
      page_size: pagination.pageSize,
      name: searchText || undefined,
      sort_by: sortField,
      sort_order: sortOrder,
      ...filters
    });
    
    // 组件卸载时取消所有请求
    return () => {
      cancelAllRequests();
    };
  }, [pagination.current, pagination.pageSize, filters, sortField, sortOrder]);

  // 从localStorage加载收藏的项目
  useEffect(() => {
    const savedStarred = localStorage.getItem('starredProjects');
    if (savedStarred) {
      try {
        setStarredProjects(JSON.parse(savedStarred));
      } catch (e) {
        console.error('无法解析收藏的项目:', e);
      }
    }
  }, []);

  // 处理表格变化
  const handleTableChange = (pagination: any, filters: any, sorter: any) => {
    setPagination(pagination);
    
    // 处理排序
    if (sorter && sorter.field) {
      const newSortOrder = sorter.order === 'ascend' ? 'asc' as const : 'desc' as const;
      setSortOrder(newSortOrder);
      setSortField(sorter.field);
      
      const params: ProjectQueryParams = {
        ...filters,
        page: pagination.current,
        page_size: pagination.pageSize,
        sort_by: sorter.field,
        sort_order: newSortOrder
      };
      fetchProjects(params);
    }
  };

  // 处理搜索
  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    fetchProjects({
      page: pagination.current,
      page_size: pagination.pageSize,
      name: searchText || undefined,
      sort_by: sortField,
      sort_order: sortOrder,
      ...filters
    });
  };

  // 重置所有筛选条件
  const handleReset = () => {
    setSearchText('');
    setFilters({ repository_type: undefined, is_active: undefined });
    setPagination({ ...pagination, current: 1 });
    setSortField('created_at');
    setSortOrder('desc');
    setTimeout(fetchProjects, 0);
  };

  // 处理项目删除
  const handleDelete = async (id: number) => {
    try {
      await deleteProject(id);
      message.success('项目删除成功');
      fetchProjects({
        page: pagination.current,
        page_size: pagination.pageSize,
        name: searchText || undefined,
        sort_by: sortField,
        sort_order: sortOrder,
        ...filters
      });
    } catch (error) {
      console.error('删除项目失败:', error);
      message.error('删除项目失败');
    }
  };

  // 批量删除项目
  const handleBatchDelete = async () => {
    Modal.confirm({
      title: '批量删除项目',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个项目吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 这里需要实现批量删除API
          // 假设API支持批量删除
          for (const id of selectedRowKeys) {
            await deleteProject(id as number);
          }
          message.success(`成功删除 ${selectedRowKeys.length} 个项目`);
          setSelectedRowKeys([]);
          fetchProjects({
            page: pagination.current,
            page_size: pagination.pageSize,
            name: searchText || undefined,
            sort_by: sortField,
            sort_order: sortOrder,
            ...filters
          });
        } catch (error) {
          console.error('批量删除失败:', error);
          message.error('批量删除失败');
        }
      }
    });
  };

  // 处理创建/编辑完成
  const handleFormFinish = () => {
    setCreateModalVisible(false);
    setEditingProject(null);
    fetchProjects({
      page: pagination.current,
      page_size: pagination.pageSize,
      name: searchText || undefined,
      sort_by: sortField,
      sort_order: sortOrder,
      ...filters
    });
  };

  // 处理筛选变更
  const handleFilterChange = (changedValues: any) => {
    setFilters({ ...filters, ...changedValues });
  };

  // 处理收藏/取消收藏
  const toggleStar = (projectId: number) => {
    const newStarred = starredProjects.includes(projectId)
      ? starredProjects.filter(id => id !== projectId)
      : [...starredProjects, projectId];
    
    setStarredProjects(newStarred);
    localStorage.setItem('starredProjects', JSON.stringify(newStarred));
    message.success(
      starredProjects.includes(projectId) ? '已取消收藏' : '已添加到收藏'
    );
  };

  // 导出项目列表
  const handleExportExcel = () => {
    const exportData = data.map(item => ({
      '项目ID': item.id,
      '项目名称': item.name,
      '仓库类型': item.repository_type?.toUpperCase() || '-',
      '分支': item.branch || '-',
      '状态': item.is_active ? '活跃' : '已归档',
      '创建时间': formatDateTime(item.created_at),
      '更新时间': item.updated_at ? formatDateTime(item.updated_at) : '-'
    }));

    exportToExcel(exportData, '项目列表');
    message.success('项目列表导出成功');
  };

  // 表格列定义
  const columns = [
    {
      title: '收藏',
      dataIndex: 'star',
      key: 'star',
      width: 60,
      render: (_: any, record: any) => (
        <Tooltip title={starredProjects.includes(record.id) ? '取消收藏' : '添加收藏'}>
          <Button 
            type="text" 
            icon={starredProjects.includes(record.id) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />} 
            onClick={(e) => {
              e.stopPropagation();
              toggleStar(record.id);
            }}
          />
        </Tooltip>
      )
    },
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: true,
    },
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: Project) => (
        <a onClick={() => navigate(`/projects/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 300,
      ellipsis: true,
    },
    {
      title: '仓库地址',
      dataIndex: 'repository_url',
      key: 'repository_url',
      width: 300,
      ellipsis: true,
    },
    {
      title: '仓库类型',
      dataIndex: 'repository_type',
      key: 'repository_type',
      width: 100,
    },
    {
      title: '分支',
      dataIndex: 'branch',
      key: 'branch',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '成员数',
      dataIndex: 'member_count',
      key: 'member_count',
      width: 100,
    },
    {
      title: '创建者',
      dataIndex: 'creator',
      key: 'creator',
      width: 150,
      render: (creator: any) => creator?.username || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => formatDateTime(text),
    },
    {
      title: '操作',
      key: 'action',
      width: 260,
      render: (_: any, record: Project) => (
        <Space size="middle" className="action-buttons">
          <Permission codes={['project:view', 'project:view:basic']}>
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              onClick={() => navigate(`/projects/${record.id}`)}
            >
              查看
            </Button>
          </Permission>
          
          <Permission codes={['project:member:manage']} projectRoles={['owner', 'manager']} projectId={record.id}>
            <Button 
              type="link" 
              icon={<TeamOutlined />} 
              onClick={() => navigate(`/projects/${record.id}/members`)}
            >
              成员
            </Button>
          </Permission>
          
          <Permission 
            codes={['project:edit', 'project:edit:basic']} 
            projectRoles={['owner', 'manager']} 
            projectId={record.id}
          >
            <Button 
              type="link" 
              icon={<EditOutlined />}
              onClick={() => {
                setEditingProject(record);
                setCreateModalVisible(true);
              }}
            >
              编辑
            </Button>
          </Permission>
          
          <Permission codes={['project:delete']} projectRoles={['owner']} projectId={record.id}>
            <Popconfirm
              title={
                <div>
                  <div>确定要删除此项目吗？</div>
                  <div style={{ fontSize: '12px', color: '#999' }}>删除后将无法恢复，请谨慎操作！</div>
                </div>
              }
              okText="确定"
              cancelText="取消"
              onConfirm={() => handleDelete(record.id)}
            >
              <Button 
                type="link" 
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          </Permission>
        </Space>
      ),
    },
  ];

  // 筛选面板
  const filterPanel = (
    <Card style={{ marginBottom: 16 }} bordered={false} className="filter-panel">
      <Form layout="inline" onValuesChange={handleFilterChange} initialValues={filters}>
        <Form.Item name="repository_type" label="仓库类型">
          <Select 
            style={{ width: 120 }} 
            placeholder="全部" 
            allowClear 
            onChange={(value) => setFilters({...filters, repository_type: value})}
          >
            <Option value="git">Git</Option>
            <Option value="svn">SVN</Option>
            <Option value="gitlab">GitLab</Option>
            <Option value="github">GitHub</Option>
          </Select>
        </Form.Item>
        <Form.Item name="is_active" label="状态">
          <Select 
            style={{ width: 120 }} 
            placeholder="全部" 
            allowClear 
            onChange={(value) => setFilters({...filters, is_active: value})}
          >
            <Option value={true}>活跃</Option>
            <Option value={false}>已归档</Option>
          </Select>
        </Form.Item>
        <Form.Item name="starred" label="收藏">
          <Select 
            style={{ width: 120 }} 
            placeholder="全部" 
            allowClear 
            onChange={(value) => {
              if (value === 'starred') {
                // 筛选收藏的项目
                const filteredData = data.filter(item => starredProjects.includes(item.id));
                setData(filteredData);
                setTotal(filteredData.length);
              } else {
                // 重新加载所有项目
                fetchProjects({
                  page: pagination.current,
                  page_size: pagination.pageSize,
                  name: searchText || undefined,
                  sort_by: sortField,
                  sort_order: sortOrder,
                  ...filters
                });
              }
            }}
          >
            <Option value="starred">已收藏</Option>
          </Select>
        </Form.Item>
        <Form.Item name="sort" label="排序">
          <Radio.Group
            onChange={(e) => {
              const value = e.target.value;
              if (value === 'newest') {
                setSortField('created_at');
                setSortOrder('desc');
              } else if (value === 'oldest') {
                setSortField('created_at');
                setSortOrder('asc');
              } else if (value === 'name_asc') {
                setSortField('name');
                setSortOrder('asc');
              } else if (value === 'name_desc') {
                setSortField('name');
                setSortOrder('desc');
              }
            }}
            defaultValue="newest"
          >
            <Radio.Button value="newest">最新</Radio.Button>
            <Radio.Button value="oldest">最早</Radio.Button>
            <Radio.Button value="name_asc">名称↑</Radio.Button>
            <Radio.Button value="name_desc">名称↓</Radio.Button>
          </Radio.Group>
        </Form.Item>
        <Form.Item>
          <Button onClick={handleReset} icon={<ReloadOutlined />}>重置</Button>
        </Form.Item>
      </Form>
    </Card>
  );

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => {
      setSelectedRowKeys(keys);
    },
  };

  // 批量操作菜单
  const batchActionMenu = (
    <Menu>
      <Permission roles={['admin']}>
        <Menu.Item key="delete" onClick={handleBatchDelete} icon={<DeleteOutlined />} danger>
          批量删除
        </Menu.Item>
      </Permission>
      <Menu.Item key="export" onClick={handleExportExcel} icon={<FileExcelOutlined />}>
        导出选中项
      </Menu.Item>
    </Menu>
  );

  return (
    <div className="projects-page">
      <PageHeader title="项目管理" />
      
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Space>
            <Input
              placeholder="搜索项目名称"
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              allowClear
            />
            <Button type="primary" onClick={handleSearch}>搜索</Button>
            <Button 
              type={filterVisible ? 'primary' : 'default'} 
              icon={<FilterOutlined />} 
              onClick={() => setFilterVisible(!filterVisible)}
            >
              筛选
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>重置</Button>
          </Space>
          
          <Space>
            <Permission codes={['project:export']}>
              <Button 
                icon={<ExportOutlined />} 
                onClick={handleExportExcel}
              >
                导出列表
              </Button>
            </Permission>
            
            <Permission codes={['project:create', 'project:create:basic']}>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => {
                  setEditingProject(null);
                  setCreateModalVisible(true);
                }}
              >
                新建项目
              </Button>
            </Permission>
          </Space>
        </div>
        
        {filterVisible && filterPanel}
      </Card>
      
      <Card 
        title={
          <div style={{ fontWeight: 'bold' }}>
            项目列表 
            <span style={{ fontSize: '14px', fontWeight: 'normal', marginLeft: '8px' }}>
              (共 {total} 条记录)
            </span>
            {selectedRowKeys.length > 0 && (
              <span style={{ fontSize: '14px', color: '#1890ff', marginLeft: '16px' }}>
                已选择 {selectedRowKeys.length} 项
              </span>
            )}
          </div>
        }
      >
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={Array.isArray(data) ? data : []}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          locale={{ emptyText: '暂无项目数据' }}
        />
      </Card>

      {/* 项目创建/编辑表单 */}
      <ProjectForm
        visible={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          setEditingProject(null);
        }}
        onSuccess={handleFormFinish}
        editingProject={editingProject}
      />
    </div>
  );
};

export default ProjectsPage; 