import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Select, message, Popconfirm } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getAllProjectRoles, assignProjectRole, removeProjectRole } from '../../../api/roles';

const { Option } = Select;

interface ProjectMember {
  id: number;
  user_id: number;
  username: string;
  email: string;
  roles: Array<{
    id: number;
    name: string;
  }>;
}

interface ProjectRole {
  id: number;
  name: string;
  description?: string;
}

interface MemberListProps {
  projectId: number;
  members: ProjectMember[];
  onMemberUpdate: () => void;
}

const MemberList: React.FC<MemberListProps> = ({ projectId, members, onMemberUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [availableRoles, setAvailableRoles] = useState<ProjectRole[]>([]);

  // 获取项目可用角色列表
  const fetchAvailableRoles = async () => {
    try {
      const res = await getAllProjectRoles();
      if (res.code === 200 && res.data) {
        setAvailableRoles(res.data);
      }
    } catch (error) {
      console.error('获取项目角色列表失败:', error);
      message.error('获取项目角色列表失败');
    }
  };

  useEffect(() => {
    fetchAvailableRoles();
  }, []);

  // 处理角色变更
  const handleRoleChange = async (userId: number, roleId: number) => {
    setLoading(true);
    try {
      await assignProjectRole(projectId, userId, roleId);
      message.success('角色分配成功');
      onMemberUpdate();
    } catch (error) {
      console.error('角色分配失败:', error);
      message.error('角色分配失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理移除角色
  const handleRemoveRole = async (userId: number, roleId: number) => {
    setLoading(true);
    try {
      await removeProjectRole(projectId, userId, roleId);
      message.success('角色移除成功');
      onMemberUpdate();
    } catch (error) {
      console.error('角色移除失败:', error);
      message.error('角色移除失败');
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<ProjectMember> = [
    {
      title: '用户信息',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: ProjectMember) => (
        <div>
          <div>{text}</div>
          <div style={{ fontSize: '12px', color: '#999' }}>{record.email}</div>
        </div>
      ),
    },
    {
      title: '角色',
      key: 'roles',
      render: (_, record: ProjectMember) => (
        <Space>
          {record.roles.map(role => (
            <Space key={role.id} size={4}>
              <span>{role.name}</span>
              <Popconfirm
                title="确定要移除此角色吗？"
                onConfirm={() => handleRemoveRole(record.user_id, role.id)}
                okText="确定"
                cancelText="取消"
              >
                <DeleteOutlined style={{ cursor: 'pointer', color: '#ff4d4f' }} />
              </Popconfirm>
            </Space>
          ))}
          <Select
            style={{ width: 120 }}
            placeholder="添加角色"
            onChange={(value) => handleRoleChange(record.user_id, value)}
          >
            {availableRoles
              .filter(role => !record.roles.some(r => r.id === role.id))
              .map(role => (
                <Option key={role.id} value={role.id}>
                  {role.name}
                </Option>
              ))
            }
          </Select>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={members}
      rowKey="user_id"
      loading={loading}
      pagination={false}
    />
  );
};

export default MemberList; 