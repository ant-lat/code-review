import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Tag, Input, 
  Select, Popconfirm, message, Modal, Form, 
  Drawer, Tooltip, Tabs
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, 
  EyeOutlined, TeamOutlined, BarChartOutlined,
  SearchOutlined, ReloadOutlined, GithubOutlined,
  GitlabOutlined, CodeOutlined, BranchesOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import dayjs from 'dayjs';
import { 
  fetchProjects, 
  createProject,
  updateProject,
  deleteProject
} from '../../store/slices/projectSlice';
import Authorized from '../../components/Permission';
import ProjectMemberForm from './components/ProjectMemberForm';
import './styles.less';

const { Option } = Select;
const { TabPane } = Tabs;

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { projects, total, loading } = useSelector((state: AppState) => state.project);
  
  // 本地状态
  const [searchParams, setSearchParams] = useState({
    name: '',
    repository_type: undefined,
    is_active: undefined
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10
  });
  
  // 模态框状态
  const [modalVisible, setModalVisible] = useState(false);
  const [currentProject, setCurrentProject] = useState<any>(null);
  const [form] = Form.useForm();
  const [isEdit, setIsEdit] = useState(false);
  
  // 成员抽屉
  const [memberDrawerVisible, setMemberDrawerVisible] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  
  // 初始加载
  useEffect(() => {
    loadProjects();
  }, [dispatch, pagination.current, pagination.pageSize]);
  
  // 加载项目
  const loadProjects = () => {
    const params = {
      ...searchParams,
      page: pagination.current,
      page_size: pagination.pageSize
    };
    
    dispatch(fetchProjects(params) as any);
  };
  
  // 处理搜索
  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    loadProjects();
  };
  
  // 处理重置
  const handleReset = () => {
    setSearchParams({
      name: '',
      repository_type: undefined,
      is_active: undefined
    });
    setPagination({ ...pagination, current: 1 });
    setTimeout(loadProjects, 0);
  };
  
  // 打开创建模态框
  const showCreateModal = () => {
    setIsEdit(false);
    setCurrentProject(null);
    form.resetFields();
    setModalVisible(true);
  };
  
  // 打开编辑模态框
  const showEditModal = (project: any) => {
    setIsEdit(true);
    setCurrentProject(project);
    form.setFieldsValue({
      name: project.name,
      description: project.description,
      repository_url: project.repository_url,
      repository_type: project.repository_type,
      branch: project.branch,
      is_active: project.is_active
    });
    setModalVisible(true);
  };
  
  // 处理模态框确认
  const handleModalOk = () => {
    form
      .validateFields()
      .then(values => {
        if (isEdit && currentProject) {
          // 更新项目
          dispatch(updateProject({
            id: currentProject.id,
            ...values
          }) as any).then(() => {
            message.success('项目已更新');
            setModalVisible(false);
            loadProjects();
          });
        } else {
          // 创建项目
          dispatch(createProject(values) as any).then(() => {
            message.success('项目已创建');
            setModalVisible(false);
            loadProjects();
          });
        }
      })
      .catch(info => {
        console.log('验证失败:', info);
      });
  };
  
  // 处理删除项目
  const handleDeleteProject = (id: number) => {
    dispatch(deleteProject(id) as any).then(() => {
      message.success('项目已删除');
      loadProjects();
    });
  };
  
  // 打开成员管理抽屉
  const showMemberDrawer = (projectId: number) => {
    setSelectedProjectId(projectId);
    setMemberDrawerVisible(true);
  };
  
  // 关闭成员管理抽屉
  const closeMemberDrawer = () => {
    setMemberDrawerVisible(false);
    setSelectedProjectId(null);
  };
  
  // 获取仓库类型图标
  const getRepositoryIcon = (type: string) => {
    switch (type) {
      case 'github':
        return <GithubOutlined />;
      case 'gitlab':
        return <GitlabOutlined />;
      default:
        return <CodeOutlined />;
    }
  };
  
  // 表格列
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          {getRepositoryIcon(record.repository_type)}
          <a onClick={() => navigate(`/projects/${record.id}`)}>{text}</a>
        </Space>
      ),
    },
    {
      title: '仓库类型',
      dataIndex: 'repository_type',
      key: 'repository_type',
      render: (type: string) => {
        const typeMap: Record<string, { color: string, label: string }> = {
          git: { color: 'blue', label: 'Git' },
          svn: { color: 'orange', label: 'SVN' }
        };
        
        const { color, label } = typeMap[type] || { color: 'default', label: type };
        
        return <Tag color={color}>{label}</Tag>;
      },
    },
    {
      title: '分支',
      dataIndex: 'branch',
      key: 'branch',
      render: (branch: string) => (
        <Space>
          <BranchesOutlined />
          {branch}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        isActive ? (
          <Tag color="green">活跃</Tag>
        ) : (
          <Tag color="red">已归档</Tag>
        )
      ),
    },
    {
      title: '成员数',
      dataIndex: 'member_count',
      key: 'member_count',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: any) => (
        <Space size="small" className="action-btns">
          <Authorized permissions={["project:view"]}>
            <Button
              type="primary"
              ghost
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/projects/${record.id}`)}
            >
              查看
            </Button>
          </Authorized>
          
          <Authorized permissions={["project:edit"]}>
            <Button
              type="primary"
              ghost
              size="small"
              icon={<EditOutlined />}
              onClick={() => showEditModal(record)}
            >
              编辑
            </Button>
          </Authorized>
          
          <Authorized permissions={["project:member:manage"]}>
            <Button
              type="default"
              size="small"
              icon={<TeamOutlined />}
              onClick={() => showMemberDrawer(record.id)}
            >
              成员
            </Button>
          </Authorized>
          
          <Authorized permissions={["project:delete"]}>
            <Popconfirm
              title="确定要删除此项目吗？此操作不可逆。"
              onConfirm={() => handleDeleteProject(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="primary"
                danger
                size="small"
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          </Authorized>
        </Space>
      ),
    },
  ];
  
  // 过滤表单
  const filterForm = (
    <div className="filter-form">
      <Space wrap size="middle">
        <Input
          placeholder="项目名称"
          value={searchParams.name}
          onChange={e => setSearchParams({ ...searchParams, name: e.target.value })}
          style={{ width: 200 }}
          allowClear
          prefix={<SearchOutlined />}
        />
        
        <Select
          placeholder="仓库类型"
          value={searchParams.repository_type}
          onChange={value => setSearchParams({ ...searchParams, repository_type: value })}
          style={{ width: 150 }}
          allowClear
        >
          <Option value="github">GitHub</Option>
          <Option value="gitlab">GitLab</Option>
          <Option value="svn">SVN</Option>
          <Option value="local">本地</Option>
        </Select>
        
        <Select
          placeholder="状态"
          value={searchParams.is_active}
          onChange={value => setSearchParams({ ...searchParams, is_active: value })}
          style={{ width: 120 }}
          allowClear
        >
          <Option value={true}>活跃</Option>
          <Option value={false}>已归档</Option>
        </Select>
        
        <div className="filter-buttons">
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            搜索
          </Button>
          
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </div>
      </Space>
    </div>
  );
  
  return (
    <div className="project-list-container">
      <Card
        title="项目管理"
        extra={
          <Authorized permissions={["project:add"]}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              新建项目
            </Button>
          </Authorized>
        }
      >
        {filterForm}
        
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: total => `共 ${total} 个项目`,
            onChange: (page, pageSize) => {
              setPagination({
                current: page,
                pageSize: pageSize || 10
              });
            }
          }}
        />
      </Card>
      
      {/* 项目表单模态框 */}
      <Modal
        title={isEdit ? '编辑项目' : '创建项目'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        maskClosable={false}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ is_active: true, repository_type: 'github', branch: 'main' }}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="项目描述"
          >
            <Input.TextArea placeholder="请输入项目描述" rows={4} />
          </Form.Item>
          
          <Form.Item
            name="repository_url"
            label="仓库地址"
            rules={[{ required: true, message: '请输入仓库地址' }]}
          >
            <Input placeholder="请输入仓库地址" />
          </Form.Item>
          
          <Form.Item
            name="repository_type"
            label="仓库类型"
            rules={[{ required: true, message: '请选择仓库类型' }]}
          >
            <Select placeholder="请选择仓库类型">
              <Option value="github">GitHub</Option>
              <Option value="gitlab">GitLab</Option>
              <Option value="svn">SVN</Option>
              <Option value="local">本地</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="branch"
            label="分支"
            rules={[{ required: true, message: '请输入分支名称' }]}
          >
            <Input placeholder="请输入分支名称，如 main 或 master" />
          </Form.Item>
          
          <Form.Item
            name="is_active"
            valuePropName="checked"
            label="项目状态"
          >
            <Select>
              <Option value={true}>活跃</Option>
              <Option value={false}>归档</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 项目成员抽屉 */}
      <Drawer
        title="项目成员管理"
        width={700}
        placement="right"
        onClose={closeMemberDrawer}
        open={memberDrawerVisible}
      >
        {selectedProjectId && (
          <ProjectMemberForm projectId={selectedProjectId} onSuccess={closeMemberDrawer} visible={false} onClose={function (): void {
            throw new Error('Function not implemented.');
          } } existingMembers={[]} />
        )}
      </Drawer>
    </div>
  );
};

export default ProjectList; 