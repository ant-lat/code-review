import React from 'react';
import { Modal, Form, Input, Select, message } from 'antd';
import { createProject, updateProject } from '../../../api/projects';
import type { ProjectCreateParams, ProjectUpdateParams } from '../../../api/types';

const { Option } = Select;

export interface ProjectFormProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  editingProject?: any;
}

const ProjectForm: React.FC<ProjectFormProps> = ({
  visible,
  onCancel,
  onSuccess,
  editingProject
}) => {
  const [form] = Form.useForm();
  const isEdit = !!editingProject;

  React.useEffect(() => {
    if (visible && editingProject) {
      form.setFieldsValue({
        name: editingProject.name,
        description: editingProject.description,
        repository_url: editingProject.repository_url,
        repository_type: editingProject.repository_type,
        branch: editingProject.branch,
        is_active: editingProject.is_active
      });
    }
  }, [visible, editingProject, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (isEdit) {
        await updateProject(editingProject.id, values as ProjectUpdateParams);
        message.success('项目更新成功');
      } else {
        await createProject(values as ProjectCreateParams);
        message.success('项目创建成功');
      }
      
      form.resetFields();
      onSuccess();
    } catch (error) {
      console.error('提交失败:', error);
      message.error('操作失败，请重试');
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑项目' : '新建项目'}
      open={visible}
      onCancel={() => {
        form.resetFields();
        onCancel();
      }}
      onOk={handleSubmit}
      okText={isEdit ? '更新' : '创建'}
      cancelText="取消"
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          repository_type: 'git',
          branch: 'main',
          is_active: true
        }}
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
        >
          <Select>
            <Option value="git">Git</Option>
            <Option value="svn">SVN</Option>
            <Option value="gitlab">GitLab</Option>
            <Option value="github">GitHub</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="branch"
          label="默认分支"
        >
          <Input placeholder="请输入默认分支" />
        </Form.Item>

        <Form.Item
          name="is_active"
          label="项目状态"
        >
          <Select>
            <Option value={true}>活跃</Option>
            <Option value={false}>归档</Option>
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ProjectForm; 