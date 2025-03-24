import React, { useState, useEffect } from 'react';
import { Button, Modal, Form, Input, Select, Space, message, Tag, Breadcrumb, Switch } from 'antd';
import { PlusOutlined, HomeOutlined, SearchOutlined } from '@ant-design/icons';
import { User } from '../../api/types';
import { getUsers, createUser, updateUser, deleteUser, toggleUserStatus } from '../../api/users';
import './index.less';
import { Table } from '../../components';

const Users: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedRows, setSelectedRows] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params: any = {
        page: currentPage,
        page_size: pageSize
      };
      
      if (searchKeyword) {
        params.username = searchKeyword;
      }
      
      const response = await getUsers(params);
      if (response.data && response.data.items) {
        setData(response.data.items);
        setTotal(response.data.total || 0);
      } else if (Array.isArray(response.data)) {
        setData(response.data);
        setTotal(response.data.length || 0);
      } else {
        setData([]);
        setTotal(0);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [currentPage, pageSize]);

  const handleCreate = async (values: any) => {
    try {
      await createUser({
        user_id: values.user_id,
        username: values.username,
        phone: values.phone,
        role_id: values.role_id,
        email: values.email || `${values.user_id}@example.com`,
      });
      message.success('创建用户成功');
      setCreateModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      message.error('创建用户失败');
    }
  };

  const handleEdit = async (values: any) => {
    if (!selectedUser) return;
    
    try {
      await updateUser(selectedUser.id, {
        user_id: values.user_id,
        username: values.username,
        email: values.email,
        phone: values.phone,
        is_active: values.is_active
      });
      message.success('编辑用户成功');
      setEditModalVisible(false);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      message.error('编辑用户失败');
    }
  };

  const handleDelete = async (userId: number) => {
    try {
      await deleteUser(userId);
      message.success('删除用户成功');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      message.error('删除用户失败');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRows.length === 0) return;
    
    try {
      await Promise.all(selectedRows.map(user => deleteUser(user.id)));
      message.success(`成功删除 ${selectedRows.length} 个用户`);
      setSelectedRows([]);
      fetchUsers();
    } catch (error) {
      console.error('Error batch deleting users:', error);
      message.error('批量删除用户失败');
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    fetchUsers();
  };

  const handleToggleStatus = async (userId: number, isActive: boolean) => {
    try {
      await toggleUserStatus(userId, isActive);
      message.success(`用户${isActive ? '启用' : '禁用'}成功`);
      fetchUsers();
    } catch (error) {
      console.error('Error toggling user status:', error);
      message.error(`用户${isActive ? '启用' : '禁用'}失败`);
    }
  };

  const columns = [
    {
      title: '登录账号',
      dataIndex: 'user_id',
      key: 'user_id',
    },
    {
      title: '姓名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      render: (phone: string) => phone || '-',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: string[]) => (
        <>
          {roles && roles.length > 0 ? (
            roles.map(role => (
              <Tag color={role === 'admin' ? 'blue' : 'green'} key={role}>
                {role}
              </Tag>
            ))
          ) : (
            '-'
          )}
        </>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean, record: User) => (
        <Switch 
          checked={isActive} 
          onChange={(checked) => handleToggleStatus(record.id, checked)}
          size="small"
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Space size="middle">
          <Button 
            type="link" 
            className="edit-btn"
            onClick={() => {
              setSelectedUser(record);
              form.setFieldsValue({
                user_id: record.user_id,
                username: record.username,
                email: record.email,
                phone: record.phone,
                is_active: record.is_active
              });
              setEditModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            danger 
            onClick={(e) => {
              e.stopPropagation();
              Modal.confirm({
                title: '确认删除',
                content: `确定要删除用户 ${record.user_id} (${record.username}) 吗？`,
                onOk: () => handleDelete(record.id)
              });
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // 表单校验规则 - 确保至少有一个不为空
  const validateEmailOrPhone = (_: any, value: string, callback: Function) => {
    const formValues = form.getFieldsValue();
    const { phone, email } = formValues;
    
    if (!phone && !email) {
      callback('邮箱和手机号至少填写一个');
    } else {
      callback();
    }
  };

  return (
    <div className="users-container">
      <div className="page-header">
        <Breadcrumb>
          <Breadcrumb.Item>系统管理</Breadcrumb.Item>
          <Breadcrumb.Item>权限管理</Breadcrumb.Item>
          <Breadcrumb.Item>用户列表</Breadcrumb.Item>
        </Breadcrumb>
      </div>

      <div className="main-content">
        <div className="table-header">
          <div className="left">
            用户列表
          </div>
          <div className="right">
            <Input.Search
              placeholder="搜索用户名、邮箱"
              style={{ width: 200, marginRight: 8 }}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onSearch={handleSearch}
              allowClear
            />
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                form.resetFields();
                setCreateModalVisible(true);
              }}>
                新增
              </Button>
              <Button danger disabled={selectedRows.length === 0} onClick={handleBatchDelete}>删除</Button>
            </Space>
          </div>
        </div>

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          rowSelection={{
            type: 'checkbox',
            onChange: (_, selectedRows) => setSelectedRows(selectedRows),
          }}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            onChange: (page, pageSize) => {
              setCurrentPage(page);
              setPageSize(pageSize || 20);
            },
          }}
        />
      </div>

      {/* 新增用户弹窗 */}
      <Modal
        title="新增用户"
        open={createModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="user_id"
            label="登录账号"
            rules={[{ required: true, message: '请输入登录账号' }]}
          >
            <Input placeholder="请输入登录账号" />
          </Form.Item>
          <Form.Item
            name="username"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { type: 'email', message: '请输入有效的邮箱地址' },
              { validator: validateEmailOrPhone }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
              { validator: validateEmailOrPhone }
            ]}
          >
            <Input placeholder="请输入手机号码" />
          </Form.Item>
          <Form.Item
            name="role_id"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色">
              <Select.Option value={1}>管理员</Select.Option>
              <Select.Option value={2}>普通用户</Select.Option>
              <Select.Option value={3}>开发者</Select.Option>
              <Select.Option value={4}>审核员</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户弹窗 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setEditModalVisible(false);
          form.resetFields();
        }}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEdit}
        >
          <Form.Item
            name="user_id"
            label="登录账号"
            rules={[{ required: true, message: '请输入登录账号' }]}
          >
            <Input placeholder="请输入登录账号" />
          </Form.Item>
          <Form.Item
            name="username"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { type: 'email', message: '请输入有效的邮箱地址' },
              { validator: validateEmailOrPhone }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
              { validator: validateEmailOrPhone }
            ]}
          >
            <Input placeholder="请输入手机号码" />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users; 