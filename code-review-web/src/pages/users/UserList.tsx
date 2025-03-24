import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Tag, Button, Space, Input, Select, 
  Popconfirm, message, Modal, Form, Tooltip, Drawer
} from 'antd';
import { 
  UserOutlined, PlusOutlined, EditOutlined, 
  DeleteOutlined, KeyOutlined, LockOutlined, 
  UnlockOutlined, SearchOutlined, ReloadOutlined, UserAddOutlined
} from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import dayjs from 'dayjs';
import { 
  fetchUsers, 
  createUser, 
  updateUser, 
  deleteUser, 
  toggleUserStatus, 
  resetUserPassword 
} from '../../store/slices/userSlice';
import { fetchRoles } from '../../store/slices/roleSlice';
import Authorized from '../../components/Permission';
import UserPermissionForm from './UserPermissionForm';
import { getEnumLabel, getEnumColor } from '../../utils/enumUtils';
import { User } from '../../api/types';
import './styles.less';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';

// 扩展User接口，添加所需属性
interface ExtendedUser extends User {
  is_superuser?: boolean;
  roles?: Array<{id: number, name: string}>;
  status: string;
}

const { Option } = Select;

const UserList: React.FC = () => {
  const dispatch = useDispatch();
  const { users, total, loading } = useSelector((state: AppState) => state.user);
  const { roles } = useSelector((state: AppState) => state.role);
  
  // 本地状态
  const [searchParams, setSearchParams] = useState({
    username: '',
    email: '',
    status: undefined
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10
  });
  const [userForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [modalVisible, setModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isEdit, setIsEdit] = useState(false);
  
  // 权限抽屉
  const [permissionDrawerVisible, setPermissionDrawerVisible] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  
  // 初始加载
  useEffect(() => {
    loadUsers();
    dispatch(fetchRoles() as any);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch, pagination.current, pagination.pageSize]);
  
  // 加载用户
  const loadUsers = () => {
    const params = {
      ...searchParams,
      page: pagination.current,
      page_size: pagination.pageSize
    };
    
    dispatch(fetchUsers(params) as any);
  };
  
  // 处理搜索
  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    loadUsers();
  };
  
  // 处理重置
  const handleReset = () => {
    setSearchParams({
      username: '',
      email: '',
      status: undefined
    });
    setPagination({ ...pagination, current: 1 });
    setTimeout(loadUsers, 0);
  };
  
  // 打开创建模态框
  const showCreateModal = () => {
    setIsEdit(false);
    setCurrentUser(null);
    userForm.resetFields();
    setModalVisible(true);
  };
  
  // 打开编辑模态框
  const showEditModal = (user: User) => {
    setIsEdit(true);
    setCurrentUser(user);
    userForm.setFieldsValue({
      username: user.username,
      email: user.email,
      role: user.role
    });
    setModalVisible(true);
  };
  
  // 打开重置密码模态框
  const showResetPasswordModal = (user: User) => {
    setCurrentUser(user);
    passwordForm.resetFields();
    setPasswordModalVisible(true);
  };
  
  // 处理模态框确认
  const handleModalOk = () => {
    userForm
      .validateFields()
      .then(values => {
        if (isEdit && currentUser) {
          // 更新用户
          dispatch(updateUser({
            id: currentUser.id,
            ...values
          }) as any).then(() => {
            message.success('用户已更新');
            setModalVisible(false);
            loadUsers();
          });
        } else {
          // 创建用户
          dispatch(createUser(values) as any).then(() => {
            message.success('用户已创建');
            setModalVisible(false);
            loadUsers();
          });
        }
      })
      .catch(info => {
        console.log('验证失败:', info);
      });
  };
  
  // 处理重置密码确认
  const handleResetPassword = () => {
    passwordForm
      .validateFields()
      .then(values => {
        if (currentUser) {
          dispatch(resetUserPassword({
            user_id: currentUser.id,
            new_password: values.new_password,
            confirm_password: values.confirm_password
          }) as any).then(() => {
            message.success('密码已重置');
            setPasswordModalVisible(false);
          });
        }
      })
      .catch(info => {
        console.log('验证失败:', info);
      });
  };
  
  // 处理删除用户
  const handleDeleteUser = (id: number) => {
    dispatch(deleteUser(id) as any).then(() => {
      message.success('用户已删除');
      loadUsers();
    });
  };
  
  // 处理切换用户状态
  const handleToggleStatus = (id: number, isActive: boolean) => {
    dispatch(toggleUserStatus({
      id,
      isActive: !isActive
    }) as any).then(() => {
      message.success(`用户已${!isActive ? '启用' : '禁用'}`);
      loadUsers();
    });
  };
  
  // 打开权限抽屉
  const showPermissionDrawer = (userId: number) => {
    setSelectedUserId(userId);
    setPermissionDrawerVisible(true);
  };
  
  // 关闭权限抽屉
  const closePermissionDrawer = () => {
    setPermissionDrawerVisible(false);
    setSelectedUserId(null);
  };
  
  // 表格列
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: ExtendedUser) => (
        <Space>
          <UserOutlined />
          <span>{text}</span>
          {record.is_superuser && <Tag color="gold">管理员</Tag>}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      render: (phone: string) => phone || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string, text: string }> = {
          'active': { color: 'green', text: '正常' },
          'inactive': { color: 'red', text: '已禁用' },
          'pending': { color: 'orange', text: '待激活' }
        };
        
        return <Tag color={statusConfig[status]?.color || 'default'}>
          {statusConfig[status]?.text || status}
        </Tag>;
      },
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: any[]) => (
        <Space>
          {(roles || []).map(role => (
            <Tag key={role.id} color="blue">{role.name}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
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
      render: (_: any, record: User) => (
        <Space size="small">
          <Authorized permissions={["user:edit"]}>
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => showEditModal(record)}
            >
              编辑
            </Button>
          </Authorized>
          
          <Authorized permissions={["user:edit"]}>
            <Button
              type="text"
              icon={<KeyOutlined />}
              onClick={() => showResetPasswordModal(record)}
            >
              重置密码
            </Button>
          </Authorized>
          
          <Authorized permissions={["user:edit"]}>
            <Tooltip title={record.is_active ? '禁用' : '启用'}>
              <Button
                type="text"
                icon={record.is_active ? <LockOutlined /> : <UnlockOutlined />}
                onClick={() => handleToggleStatus(record.id, record.is_active)}
                danger={record.is_active}
              >
                {record.is_active ? '禁用' : '启用'}
              </Button>
            </Tooltip>
          </Authorized>
          
          <Authorized permissions={["user:permission:manage"]}>
            <Button
              type="text"
              onClick={() => showPermissionDrawer(record.id)}
            >
              权限
            </Button>
          </Authorized>
          
          <Authorized permissions={["user:delete"]}>
            <Popconfirm
              title="确定要删除此用户吗？此操作不可逆。"
              onConfirm={() => handleDeleteUser(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
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
      <Space wrap>
        <Input
          placeholder="用户名"
          value={searchParams.username}
          onChange={e => setSearchParams({ ...searchParams, username: e.target.value })}
          style={{ width: 200 }}
          prefix={<UserOutlined />}
          allowClear
        />
        
        <Input
          placeholder="邮箱"
          value={searchParams.email}
          onChange={e => setSearchParams({ ...searchParams, email: e.target.value })}
          style={{ width: 200 }}
          allowClear
        />
        
        <Select
          placeholder="状态"
          value={searchParams.status}
          onChange={value => setSearchParams({ ...searchParams, status: value })}
          style={{ width: 120 }}
          allowClear
        >
          <Option value="active">正常</Option>
          <Option value="inactive">已禁用</Option>
          <Option value="pending">待激活</Option>
        </Select>
        
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
          搜索
        </Button>
        
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
      </Space>
    </div>
  );
  
  return (
    <div className="user-list-container">
      <PageHeader 
        title="用户管理" 
        subTitle="系统用户和权限管理"
      />
      
      <Card
        title="用户管理"
        extra={
          <Authorized permissions={["user:add"]}>
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={showCreateModal}
            >
              添加用户
            </Button>
          </Authorized>
        }
      >
        {filterForm}
        
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: total => `共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              setPagination({
                current: page,
                pageSize: pageSize || 10
              });
            }
          }}
        />
      </Card>
      
      {/* 用户表单模态框 */}
      <Modal
        title={isEdit ? '编辑用户' : '创建用户'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        maskClosable={false}
      >
        <Form
          form={userForm}
          layout="vertical"
          initialValues={{ is_active: true }}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          
          {!isEdit && (
            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6位' }
              ]}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
          )}
          
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色">
              {roles.map((role: {id: number, name: string}) => (
                <Option key={role.id} value={role.name}>{role.name}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 重置密码模态框 */}
      <Modal
        title="重置密码"
        open={passwordModalVisible}
        onOk={handleResetPassword}
        onCancel={() => setPasswordModalVisible(false)}
        maskClosable={false}
      >
        <p>您正在为用户 <strong>{currentUser?.username}</strong> 重置密码</p>
        
        <Form
          form={passwordForm}
          layout="vertical"
        >
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          
          <Form.Item
            name="confirm_password"
            label="确认密码"
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请确认新密码" />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 用户权限抽屉 */}
      <Drawer
        title="用户权限管理"
        width={600}
        placement="right"
        onClose={closePermissionDrawer}
        open={permissionDrawerVisible}
      >
        {selectedUserId && (
          <UserPermissionForm userId={selectedUserId} onSuccess={closePermissionDrawer} />
        )}
      </Drawer>
    </div>
  );
};

export default UserList; 