import React, { useState, useEffect, ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, 
  Descriptions, 
  Tag, 
  Space, 
  Button, 
  Tabs, 
  Timeline, 
  Input, 
  Form,
  Select,
  message,
  Spin,
  Avatar,
  Divider,
  Breadcrumb,
  Tooltip,
  Badge
} from 'antd';
import {
  EditOutlined,
  ProjectOutlined,
  UserOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  HistoryOutlined,
  BranchesOutlined,
  SendOutlined,
  ExclamationCircleOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';
import { 
  getIssueById, 
  updateIssueStatus, 
  getIssueComments, 
  addIssueComment,
  getIssueHistory,
  getIssueCommits
} from '../../api/issues';
import { formatDateTime, formatRelativeTime } from '../../utils';
import IssueForm from './components/IssueForm';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

// 优先级配置
type PriorityType = 'high' | 'medium' | 'low';
type PriorityConfig = {
  [key in PriorityType]: { 
    color: string; 
    label: string; 
    icon: React.ReactNode; 
  }
};

const priorityConfig: PriorityConfig = {
  high: { color: 'red', label: '高', icon: <ExclamationCircleOutlined style={{ color: '#f5222d' }} /> },
  medium: { color: 'orange', label: '中', icon: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} /> },
  low: { color: 'blue', label: '低', icon: <QuestionCircleOutlined style={{ color: '#1890ff' }} /> },
};

// 状态配置
type StatusType = 'open' | 'in_progress' | 'resolved' | 'closed';
type StatusConfig = {
  [key in StatusType]: { 
    color: string; 
    label: string; 
  }
};

const statusConfig: StatusConfig = {
  open: { color: 'processing', label: '待处理' },
  in_progress: { color: 'warning', label: '处理中' },
  resolved: { color: 'success', label: '已解决' },
  closed: { color: 'default', label: '已关闭' },
};

const IssueDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const issueId = parseInt(id || '0');

  const [form] = Form.useForm();
  const [statusForm] = Form.useForm();
  
  const [loading, setLoading] = useState(true);
  const [issueData, setIssueData] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [commits, setCommits] = useState<any[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [commitsLoading, setCommitsLoading] = useState(false);
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [statusSubmitting, setStatusSubmitting] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);

  // 深度解析响应数据，支持多层嵌套
  const extractData = (responseData: any): any => {
    try {
      // 如果是null或undefined，返回null
      if (responseData == null) return null;
      
      // 如果是数组，直接返回
      if (Array.isArray(responseData)) return responseData;
      
      // 如果是对象，检查是否有data或items字段
      if (typeof responseData === 'object') {
        // 检查data字段
        if (responseData.data !== undefined) {
          // 递归处理data字段
          return extractData(responseData.data);
        }
        
        // 检查items字段
        if (responseData.items !== undefined && Array.isArray(responseData.items)) {
          return responseData.items;
        }
        
        // 如果没有data或items字段，返回原对象
        return responseData;
      }
      
      // 其他情况返回原始值
      return responseData;
    } catch (error) {
      console.error('提取数据时出错:', error);
      return null;
    }
  };

  // 获取问题详情
  const fetchIssueDetail = async () => {
    setLoading(true);
    try {
      const res = await getIssueById(issueId);
      // 使用通用解析方法提取数据
      const issueDetail = extractData(res.data);
      console.log('问题详情数据:', issueDetail);
      
      if (issueDetail) {
        setIssueData(issueDetail);
        statusForm.setFieldsValue({ status: issueDetail.status });
      } else {
        message.warning('返回的问题详情数据格式不正确');
        setIssueData(null);
      }
    } catch (error) {
      console.error('获取问题详情失败:', error);
      // 不显示错误消息，因为在某些情况下，API可能返回成功但数据格式不符合预期
    } finally {
      setLoading(false);
    }
  };

  // 获取问题评论
  const fetchComments = async () => {
    setCommentsLoading(true);
    try {
      const res = await getIssueComments(issueId);
      // 使用通用解析方法提取数据
      const commentList = extractData(res.data) || [];
      console.log('评论数据:', commentList);
      setComments(Array.isArray(commentList) ? commentList : []);
    } catch (error) {
      console.error('获取问题评论失败:', error);
      // 设置空数组而不是显示错误消息
      setComments([]);
    } finally {
      setCommentsLoading(false);
    }
  };

  // 获取问题历史记录
  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await getIssueHistory(issueId);
      // 使用通用解析方法提取数据
      const historyList = extractData(res.data) || [];
      console.log('历史记录数据:', historyList);
      setHistory(Array.isArray(historyList) ? historyList : []);
    } catch (error) {
      console.error('获取问题历史记录失败:', error);
      // 设置空数组而不是显示错误消息
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 获取关联的代码提交
  const fetchCommits = async () => {
    setCommitsLoading(true);
    try {
      const res = await getIssueCommits(issueId);
      // 使用通用解析方法提取数据
      const commitList = extractData(res.data) || [];
      console.log('代码提交数据:', commitList);
      setCommits(Array.isArray(commitList) ? commitList : []);
    } catch (error) {
      console.error('获取关联代码提交失败:', error);
      // 设置空数组而不是显示错误消息
      setCommits([]);
    } finally {
      setCommitsLoading(false);
    }
  };

  useEffect(() => {
    if (issueId) {
      // 使用Promise.all并行获取所有数据
      const fetchData = async () => {
        try {
          setLoading(true);
          // 首先获取问题详情，因为其他数据依赖于它
          await fetchIssueDetail();
          
          // 并行获取其他数据
          await Promise.all([
            fetchComments(),
            fetchHistory(),
            fetchCommits()
          ]);
        } catch (error) {
          console.error('加载页面数据失败:', error);
        } finally {
          setLoading(false);
        }
      };
      
      fetchData();
    }
    
    // 清理函数
    return () => {
      // 如果需要取消请求，可以在这里添加取消逻辑
    };
  }, [issueId]);

  // 提交评论
  const handleCommentSubmit = async (values: any) => {
    setCommentSubmitting(true);
    try {
      // 确保content是字符串类型
      const content = values.content as string;
      await addIssueComment(issueId, content);
      message.success('评论添加成功');
      form.resetFields();
      fetchComments();
    } catch (error) {
      console.error('添加评论失败:', error);
      message.error('添加评论失败');
    } finally {
      setCommentSubmitting(false);
    }
  };

  // 更新问题状态
  const handleStatusChange = async (values: any) => {
    setStatusSubmitting(true);
    try {
      await updateIssueStatus(issueId, values.status);
      message.success('问题状态更新成功');
      fetchIssueDetail();
      fetchHistory();
    } catch (error) {
      console.error('更新问题状态失败:', error);
      message.error('更新问题状态失败');
    } finally {
      setStatusSubmitting(false);
    }
  };

  // 安全获取配置值
  const getStatusColor = (status: string): string => {
    return (statusConfig as any)[status]?.color || 'default';
  };

  const getStatusLabel = (status: string): string => {
    return (statusConfig as any)[status]?.label || status;
  };

  const getPriorityColor = (priority: string): string => {
    return (priorityConfig as any)[priority]?.color || 'default';
  };

  const getPriorityLabel = (priority: string): string => {
    return (priorityConfig as any)[priority]?.label || priority;
  };

  const getPriorityIcon = (priority: string): React.ReactNode => {
    return (priorityConfig as any)[priority]?.icon || null;
  };

  // 渲染问题信息
  const renderIssueInfo = () => {
    if (!issueData) return null;

    return (
      <Card>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="问题ID">{issueData.id}</Descriptions.Item>
          <Descriptions.Item label="当前状态">
            <Badge 
              status={getStatusColor(issueData.status) as any} 
              text={getStatusLabel(issueData.status)} 
            />
          </Descriptions.Item>
          
          <Descriptions.Item label="所属项目">
            <Button 
              type="link" 
              icon={<ProjectOutlined />} 
              onClick={() => navigate(`/projects/${issueData.project_id}`)}
            >
              {issueData.project_name}
            </Button>
          </Descriptions.Item>
          
          <Descriptions.Item label="优先级">
            <Tag color={getPriorityColor(issueData.priority)}>
              {getPriorityLabel(issueData.priority)}
            </Tag>
          </Descriptions.Item>
          
          <Descriptions.Item label="创建者">
            <Space>
              <Avatar size="small" icon={<UserOutlined />} />
              {issueData.creator_name}
            </Space>
          </Descriptions.Item>
          
          <Descriptions.Item label="指派给">
            {issueData.assignee_name ? (
              <Space>
                <Avatar size="small" icon={<UserOutlined />} />
                {issueData.assignee_name}
              </Space>
            ) : '未指派'}
          </Descriptions.Item>
          
          <Descriptions.Item label="创建时间">{formatDateTime(issueData.created_at)}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{formatDateTime(issueData.updated_at)}</Descriptions.Item>
          
          <Descriptions.Item label="描述" span={2}>
            <div style={{ whiteSpace: 'pre-wrap' }}>{issueData.description}</div>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  // 渲染评论列表
  const renderComments = () => {
    if (commentsLoading) return <Spin />;

    return (
      <div>
        {comments.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'rgba(0,0,0,0.45)' }}>
            暂无评论
          </div>
        ) : (
          comments.map(comment => (
            <div key={comment.id} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                <Avatar icon={<UserOutlined />} style={{ marginRight: 12 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                      <b>{comment.creator_name}</b>
                      {comment.file_path && (
                        <Tag style={{ marginLeft: 8 }}>
                          {comment.file_path}
                          {comment.line_number ? `:${comment.line_number}` : ''}
                        </Tag>
                      )}
                    </div>
                    <span style={{ color: 'rgba(0,0,0,0.45)' }}>
                      {formatRelativeTime(comment.created_at)}
                    </span>
                  </div>
                  <div style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{comment.content}</div>
                </div>
              </div>
              <Divider style={{ margin: '12px 0' }} />
            </div>
          ))
        )}

        <Form form={form} onFinish={handleCommentSubmit}>
          <Form.Item
            name="content"
            rules={[{ required: true, message: '请输入评论内容' }]}
          >
            <TextArea rows={3} placeholder="添加评论..." />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Button 
              type="primary" 
              htmlType="submit" 
              icon={<SendOutlined />} 
              loading={commentSubmitting}
            >
              发送
            </Button>
          </Form.Item>
        </Form>
      </div>
    );
  };

  // 渲染历史记录
  const renderHistory = () => {
    if (historyLoading) return <Spin />;

    return (
      <Timeline>
        {history.map((item, index) => (
          <Timeline.Item 
            key={index} 
            dot={<HistoryOutlined style={{ fontSize: '16px' }} />}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <Space>
                  <Avatar size="small" icon={<UserOutlined />} />
                  <b>{item.user_name}</b>
                </Space>
                <span style={{ marginLeft: 8 }}>{item.action}</span>
                {item.field && (
                  <span style={{ marginLeft: 4 }}>
                    字段 <b>{item.field}</b>: {item.old_value} → {item.new_value}
                  </span>
                )}
              </div>
              <span style={{ color: 'rgba(0,0,0,0.45)' }}>
                {formatDateTime(item.created_at)}
              </span>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    );
  };

  // 渲染关联提交
  const renderCommits = () => {
    if (commitsLoading) return <Spin />;

    return (
      <div>
        {commits.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'rgba(0,0,0,0.45)' }}>
            暂无关联提交
          </div>
        ) : (
          <Timeline>
            {commits.map(commit => (
              <Timeline.Item 
                key={commit.id} 
                dot={<BranchesOutlined style={{ fontSize: '16px' }} />}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <Tooltip title="查看代码提交">
                      <Button 
                        type="link" 
                        onClick={() => navigate(`/code-review/${commit.id}`)}
                        style={{ padding: 0 }}
                      >
                        {commit.commit_id.substring(0, 8)}: {commit.commit_message}
                      </Button>
                    </Tooltip>
                    <div style={{ color: 'rgba(0,0,0,0.45)', marginTop: 4 }}>
                      <Space>
                        <Avatar size="small" icon={<UserOutlined />} />
                        {commit.author_name}
                      </Space>
                      <span style={{ marginLeft: 16 }}>
                        文件变化: {commit.files_changed} | 添加: {commit.insertions} | 删除: {commit.deletions}
                      </span>
                    </div>
                  </div>
                  <span style={{ color: 'rgba(0,0,0,0.45)' }}>
                    {formatDateTime(commit.commit_time)}
                  </span>
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        )}
      </div>
    );
  };

  const breadcrumbItems = [
    { title: '问题跟踪', path: '/issues' },
    { title: issueData?.title || '问题详情' }
  ];

  // 如果数据加载中，显示加载状态
  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  // 准备页面标题和操作组件作为ReactNode
  const pageTitle = (
    <Space>
      {getPriorityIcon(issueData?.priority || '')}
      {issueData?.title}
    </Space>
  );

  const pageExtra = (
    <Space>
      <Permission roles={['admin', 'developer', 'reviewer']} projectRoles={['owner', 'manager', 'member']} projectId={issueData?.project_id}>
        <Form
          form={statusForm}
          layout="inline"
          onFinish={handleStatusChange}
          initialValues={{ status: issueData?.status }}
        >
          <Form.Item name="status" label="状态" style={{ marginBottom: 0 }}>
            <Select style={{ width: 120 }} disabled={statusSubmitting}>
              <Option value="open">待处理</Option>
              <Option value="in_progress">处理中</Option>
              <Option value="resolved">已解决</Option>
              <Option value="closed">已关闭</Option>
            </Select>
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={statusSubmitting}
            >
              更新状态
            </Button>
          </Form.Item>
        </Form>
      </Permission>
      
      <Permission roles={['admin']} projectRoles={['owner', 'manager']} projectId={issueData?.project_id}>
        <Button 
          icon={<EditOutlined />} 
          onClick={() => setEditModalVisible(true)}
        >
          编辑问题
        </Button>
      </Permission>
    </Space>
  );

  return (
    <div className="issue-detail">
      <PageHeader 
        title={pageTitle}
        breadcrumb={breadcrumbItems}
        extra={pageExtra}
      />

      <div style={{ marginBottom: 16 }}>
        {renderIssueInfo()}
      </div>

      <Tabs defaultActiveKey="comments">
        <TabPane tab={<span><MessageOutlined /> 评论</span>} key="comments">
          {renderComments()}
        </TabPane>
        <TabPane tab={<span><HistoryOutlined /> 历史记录</span>} key="history">
          {renderHistory()}
        </TabPane>
        <TabPane tab={<span><BranchesOutlined /> 关联提交</span>} key="commits">
          {renderCommits()}
        </TabPane>
      </Tabs>

      {/* 编辑问题表单 */}
      <IssueForm
        visible={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onFinish={() => {
          setEditModalVisible(false);
          fetchIssueDetail();
          fetchHistory();
        }}
        initialValues={issueData}
      />
    </div>
  );
};

export default IssueDetail; 