import React, { useEffect, useState } from 'react';
import { 
  Modal, 
  Form, 
  Input, 
  Select, 
  message, 
  Spin, 
  Button,
  InputNumber,
  Row,
  Col
} from 'antd';
import { createIssue, updateIssue } from '../../../api/issues';
import { getProjects } from '../../../api/projects';
import { getUsers } from '../../../api/users';

const { Option } = Select;
const { TextArea } = Input;

// 问题类型映射
const issueTypeMap = {
  'bug': { label: '缺陷' },
  'feature': { label: '功能' },
  'task': { label: '任务' },
  'enhancement': { label: '改进' },
  'documentation': { label: '文档' },
  'code_review': { label: '代码检视' }
};

// 严重程度映射
const severityMap = {
  'critical': { label: '致命' },
  'high': { label: '高' },
  'medium': { label: '中' },
  'low': { label: '低' }
};

interface IssueFormProps {
  visible?: boolean;
  onCancel?: () => void;
  onFinish: () => void;
  initialValues?: any;
  isEdit?: boolean;
  projects?: any[];
  users?: any[];
}

const IssueForm: React.FC<IssueFormProps> = ({ 
  visible, 
  onCancel, 
  onFinish, 
  initialValues,
  isEdit = false,
  projects,
  users
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [projectsData, setProjectsData] = useState<any[]>(projects || []);
  const [usersData, setUsersData] = useState<any[]>(users || []);
  const [showCodeReviewFields, setShowCodeReviewFields] = useState(false);

  // 初始加载
  useEffect(() => {
    if (!projects) {
      fetchProjects();
    }
    if (!users) {
      fetchUsers();
    }
    
    // 设置初始值
    if (initialValues) {
      form.setFieldsValue(initialValues);
      if (initialValues.type === 'code_review') {
        setShowCodeReviewFields(true);
      }
    }
  }, []);

  // 处理问题类型变更
  const handleIssueTypeChange = (value: string) => {
    setShowCodeReviewFields(value === 'code_review');
  };

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await getProjects();
      if (res.success) {
        setProjectsData(res.data);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await getUsers();
      if (res.success) {
        setUsersData(res.data);
      }
    } catch (error) {
      console.error('获取用户列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = async (values: any) => {
    console.log('提交表单数据:', values);
    setSubmitting(true);
    
    try {
      let response;
      if (isEdit && initialValues?.id) {
        // 更新问题
        response = await updateIssue(initialValues.id, values);
        console.log('更新问题响应:', response);
        message.success('问题更新成功');
      } else {
        // 创建问题
        response = await createIssue(values);
        console.log('创建问题响应:', response);
        message.success('问题创建成功');
      }
      onFinish();
    } catch (error) {
      console.error(isEdit ? '更新问题失败:' : '创建问题失败:', error);
      message.error(isEdit ? '更新问题失败' : '创建问题失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 手动保存按钮处理函数
  const handleSave = () => {
    console.log('点击保存按钮');
    form.submit(); // 手动触发表单提交
  };

  return (
    <Modal
      title={isEdit ? "编辑问题" : "创建问题"}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="save" type="primary" loading={submitting} onClick={handleSave}>
          {isEdit ? "保存" : "创建"}
        </Button>
      ]}
      width={700}
      destroyOnClose
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Spin />
        </div>
      ) : (
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFinish}
          initialValues={{
            priority: 'medium',
            issue_type: 'bug',
            status: 'open',
            ...initialValues,
          }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入问题标题' }]}
          >
            <Input placeholder="问题标题" />
          </Form.Item>
          
          <Form.Item
            name="project_id"
            label="所属项目"
            rules={[{ required: true, message: '请选择所属项目' }]}
          >
            <Select placeholder="选择项目">
              {(projectsData || []).map((project: any) => (
                <Option key={project.id} value={project.id}>
                  {project.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="issue_type"
                label="问题类型"
                rules={[{ required: true, message: '请选择问题类型' }]}
              >
                <Select placeholder="选择问题类型" onChange={handleIssueTypeChange}>
                  {Object.entries(issueTypeMap).map(([key, value]) => (
                    <Option key={key} value={key}>{value.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select placeholder="选择优先级">
                  <Option value="high">高</Option>
                  <Option value="medium">中</Option>
                  <Option value="low">低</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          {isEdit && (
            <Form.Item
              name="status"
              label="状态"
              rules={[{ required: true, message: '请选择状态' }]}
            >
              <Select placeholder="选择状态">
                <Option value="open">待处理</Option>
                <Option value="in_progress">处理中</Option>
                <Option value="resolved">已解决</Option>
                <Option value="closed">已关闭</Option>
              </Select>
            </Form.Item>
          )}
          
          <Form.Item
            name="assignee_id"
            label="处理人"
          >
            <Select placeholder="选择处理人" allowClear>
              {(usersData || []).map((user: any) => (
                <Option key={user.id} value={user.id}>
                  {user.username}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          {showCodeReviewFields && (
            <>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="severity"
                    label="严重程度"
                  >
                    <Select placeholder="选择严重程度">
                      {Object.entries(severityMap).map(([key, value]) => (
                        <Option key={key} value={key}>{value.label}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="commit_id"
                    label="提交ID"
                  >
                    <InputNumber style={{ width: '100%' }} placeholder="关联的提交ID" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item
                name="file_path"
                label="文件路径"
              >
                <Input placeholder="相关文件路径" />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="line_start"
                    label="起始行号"
                  >
                    <InputNumber style={{ width: '100%' }} placeholder="代码起始行" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="line_end"
                    label="结束行号"
                  >
                    <InputNumber style={{ width: '100%' }} placeholder="代码结束行" />
                  </Form.Item>
                </Col>
              </Row>
            </>
          )}
          
          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入问题描述' }]}
          >
            <TextArea rows={5} placeholder="问题的详细描述..." />
          </Form.Item>
        </Form>
      )}
    </Modal>
  );
};

export default IssueForm; 