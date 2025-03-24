import React, { useState, useEffect } from 'react';
import { Modal, Form, Select, message } from 'antd';
import { getUsers } from '../../../api/users';
import { addProjectMember, getProjectRoles } from '../../../api/projects';
import { User } from '../../../api/types';

interface ProjectMemberFormProps {
  projectId: number;
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
  existingMembers: User[];
}

const ProjectMemberForm: React.FC<ProjectMemberFormProps> = ({ 
  projectId, 
  visible, 
  onClose, 
  onSuccess,
  existingMembers
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [projectRoles, setProjectRoles] = useState<any[]>([]);

  useEffect(() => {
    if (visible) {
      fetchAvailableUsers();
      fetchProjectRoles();
      form.resetFields();
    }
  }, [visible, existingMembers]);

  const fetchAvailableUsers = async () => {
    try {
      setLoading(true);
      const response = await getUsers();
      // 过滤掉已经是项目成员的用户
      const filteredUsers = response.data?.filter(
        (user: User) => !existingMembers.some(member => member.id === user.id)
      ) || [];
      setAvailableUsers(filteredUsers);
    } catch (error) {
      message.error('获取可用用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectRoles = async () => {
    try {
      setLoading(true);
      const response = await getProjectRoles();
      setProjectRoles(response.data || []);
    } catch (error) {
      message.error('获取项目角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: { user_id: number; role_id: number }) => {
    try {
      setLoading(true);
      await addProjectMember(projectId, values.user_id, values.role_id);
      message.success('添加成员成功');
      onSuccess();
      onClose();
    } catch (error) {
      message.error('添加成员失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="添加项目成员"
      open={visible}
      onOk={() => form.submit()}
      onCancel={onClose}
      confirmLoading={loading}
    >
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Form.Item
          name="user_id"
          label="选择用户"
          rules={[{ required: true, message: '请选择用户' }]}
        >
          <Select
            loading={loading}
            placeholder="请选择用户"
            filterOption={(input, option) =>
              (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
            }
            options={availableUsers.map(user => ({
              value: user.id,
              label: `${user.username} (${user.email})`
            }))}
          />
        </Form.Item>
        <Form.Item
          name="role_id"
          label="项目角色"
          rules={[{ required: true, message: '请选择角色' }]}
        >
          <Select placeholder="请选择角色">
            {projectRoles.map(role => (
              <Select.Option key={role.id} value={role.id}>{role.name}</Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ProjectMemberForm; 