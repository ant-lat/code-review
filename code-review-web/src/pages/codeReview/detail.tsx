import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, Row, Col, Typography, Descriptions, Tag, Button, 
  Tabs, List, Avatar, Form, Input, Space, 
  Skeleton, message, Modal, Select, Divider 
} from 'antd';
import { 
  UserOutlined, FileTextOutlined, ClockCircleOutlined, 
  MessageOutlined, HistoryOutlined, SendOutlined 
} from '@ant-design/icons';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';
import { getReviewDetail, getCodeReviewComments, addReviewComment, updateReviewStatus } from '../../api/codeReview';
import { CodeReview, CodeReviewComment, ResponseBase } from '../../api/types';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

// 扩展的代码审查详情接口，包含API响应中可能出现的额外字段
interface ExtendedCodeReview extends CodeReview {
  title?: string;
  description?: string;
  file_path?: string;
  line_start?: number;
  line_end?: number;
  creator_name?: string;
  assignee_name?: string;
  resolved_at?: string;
  priority?: string;
  severity?: string;
  issue_type?: string;
}

const CodeReviewDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  
  const [loading, setLoading] = useState(true);
  const [commentsLoading, setCommentsLoading] = useState(true);
  const [reviewDetail, setReviewDetail] = useState<ExtendedCodeReview | null>(null);
  const [comments, setComments] = useState<CodeReviewComment[]>([]);
  const [statusModalVisible, setStatusModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('open');
  
  // 状态颜色映射
  const statusColorMap: Record<string, string> = {
    'open': 'processing',
    'in_progress': 'warning',
    'resolved': 'success',
    'closed': 'default',
    'pending': 'processing',
    'completed': 'success',
    'rejected': 'error'
  };
  
  // 状态文本映射
  const statusTextMap: Record<string, string> = {
    'open': '开放中',
    'in_progress': '处理中',
    'resolved': '已解决',
    'closed': '已关闭',
    'pending': '审查中',
    'completed': '已完成',
    'rejected': '已拒绝'
  };
  
  // 优先级文本映射
  const priorityTextMap: Record<string, string> = {
    'high': '高',
    'medium': '中',
    'low': '低'
  };
  
  // 严重程度文本映射
  const severityTextMap: Record<string, string> = {
    'high': '高',
    'medium': '中',
    'low': '低'
  };
  
  // 问题类型文本映射
  const issueTypeTextMap: Record<string, string> = {
    'code_review': '代码审查',
    'bug': '缺陷',
    'feature': '功能',
    'improvement': '改进'
  };
  
  // 加载代码审查详情
  const fetchReviewDetail = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      console.log(`开始请求审查详情: /code-reviews/issues/${id}`);
      
      // 设置超时
      const timeout = 10000; // 10秒
      let attempts = 0;
      const maxAttempts = 3;
      
      const fetchWithRetry = async (): Promise<any> => {
        try {
          attempts++;
          console.log(`尝试获取审查详情，第${attempts}次请求`);
          return await getReviewDetail(parseInt(id));
        } catch (error: any) {
          if (error.message === 'canceled' && attempts < maxAttempts) {
            console.log(`请求被取消，进行第${attempts + 1}次重试`);
            // 增加延迟，避免立即重试
            await new Promise(resolve => setTimeout(resolve, 500));
            return fetchWithRetry();
          }
          throw error;
        }
      };
      
      const response = await fetchWithRetry();
      console.log('审查详情响应:', response);
      
      // 提取正确的数据
      if (response && response.data) {
        // 添加默认值处理，确保即使缺少字段也能正常显示
        const defaultData = {
          id: parseInt(id),
          project_id: 0,
          commit_id: '',
          status: 'unknown',
          reviewer_id: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          title: '无标题',
          description: '无描述',
        };
        
        const detailData = {
          ...defaultData,
          ...response.data
        };
        
        setReviewDetail(detailData as ExtendedCodeReview);
        console.log('设置审查详情数据:', detailData);
      } else {
        setReviewDetail(null);
        console.warn('审查详情数据为空');
      }
    } catch (error: any) {
      console.error('获取代码审查详情失败:', error);
      console.error('错误详情:', error.response?.data || error.message);
      message.error('获取代码审查详情失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };
  
  // 加载评论列表
  const fetchComments = async () => {
    if (!id) return;
    
    try {
      setCommentsLoading(true);
      console.log(`开始请求评论列表: /code-reviews/issues/${id}/comments`);
      
      // 设置超时和重试
      let attempts = 0;
      const maxAttempts = 3;
      
      const fetchWithRetry = async (): Promise<any> => {
        try {
          attempts++;
          console.log(`尝试获取评论列表，第${attempts}次请求`);
          return await getCodeReviewComments(parseInt(id));
        } catch (error: any) {
          if (error.message === 'canceled' && attempts < maxAttempts) {
            console.log(`请求被取消，进行第${attempts + 1}次重试`);
            // 增加延迟，避免立即重试
            await new Promise(resolve => setTimeout(resolve, 500));
            return fetchWithRetry();
          }
          throw error;
        }
      };
      
      const response = await fetchWithRetry();
      console.log('评论列表响应:', response);
      
      // 提取正确的数据
      let commentsData: CodeReviewComment[] = [];
      
      if (response && response.data) {
        if (Array.isArray(response.data)) {
          commentsData = response.data.map((comment: any) => ({
            id: comment.id || 0,
            review_id: parseInt(id),
            user_id: comment.user_id || 0,
            file_path: comment.file_path || '',
            content: comment.content || '',
            created_at: comment.created_at || new Date().toISOString(),
            user: comment.user || { username: '未知用户' }
          }));
          console.log('评论数据是数组, 长度:', response.data.length);
        } else {
          // 使用类型断言安全处理可能的嵌套数据结构
          const responseData = response.data as unknown;
          const dataObj = responseData as { items?: unknown };
          
          if (dataObj && dataObj.items && Array.isArray(dataObj.items)) {
            commentsData = dataObj.items.map((comment: any) => ({
              id: comment.id || 0,
              review_id: parseInt(id),
              user_id: comment.user_id || 0,
              file_path: comment.file_path || '',
              content: comment.content || '',
              created_at: comment.created_at || new Date().toISOString(),
              user: comment.user || { username: '未知用户' }
            }));
            console.log('评论数据在items中, 长度:', dataObj.items.length);
          } else {
            console.warn('评论数据格式异常:', responseData);
          }
        }
      } else {
        console.warn('评论列表数据为空');
      }
      
      setComments(commentsData);
    } catch (error: any) {
      console.error('获取评论列表失败:', error);
      console.error('错误详情:', error.response?.data || error.message);
      message.error('获取评论列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCommentsLoading(false);
    }
  };
  
  // 处理提交评论
  const handleSubmitComment = async (values: { content: string }) => {
    if (!id || !values.content.trim()) return;
    
    try {
      setSubmitting(true);
      const reviewId = parseInt(id);
      await addReviewComment(reviewId, {
        content: values.content,
        file_path: reviewDetail?.file_path || '',
      });
      
      message.success('评论添加成功');
      form.resetFields();
      fetchComments(); // 重新加载评论列表
    } catch (error) {
      console.error('添加评论失败:', error);
      message.error('添加评论失败');
    } finally {
      setSubmitting(false);
    }
  };
  
  // 处理更新状态
  const handleUpdateStatus = async () => {
    if (!id || !selectedStatus) return;
    
    try {
      setSubmitting(true);
      await updateReviewStatus(parseInt(id), selectedStatus);
      
      message.success('状态更新成功');
      setStatusModalVisible(false);
      fetchReviewDetail(); // 重新加载详情
    } catch (error) {
      console.error('更新状态失败:', error);
      message.error('更新状态失败');
    } finally {
      setSubmitting(false);
    }
  };
  
  // 初始加载
  useEffect(() => {
    fetchReviewDetail();
    fetchComments();
  }, [id]);
  
  // 显示提交日期的格式化
  const formatDate = (dateString?: string) => {
    if (!dateString) return '未知';
    return new Date(dateString).toLocaleString('zh-CN');
  };
  
  // 状态选项
  const statusOptions = [
    { value: 'open', label: '开放中' },
    { value: 'in_progress', label: '处理中' },
    { value: 'resolved', label: '已解决' },
    { value: 'closed', label: '已关闭' },
  ];
  
  // 在关键位置添加查询按钮
  const handleSearch = () => {
    // 实现查询逻辑
  };
  
  const clearFilters = () => {
    // 实现重置逻辑
  };
  
  return (
    <div className="code-review-container">
      <div className="code-review-search">
        <Input.Search
          placeholder="搜索代码审查问题"
          onSearch={handleSearch}
          style={{ width: 300 }}
          enterButton="查询"
        />
        <Select
          placeholder="状态筛选"
          style={{ width: 150, marginLeft: 8 }}
          onChange={(value) => setStatusFilter(value)}
          allowClear
        >
          <Select.Option value="open">未解决</Select.Option>
          <Select.Option value="in_progress">处理中</Select.Option>
          <Select.Option value="resolved">已解决</Select.Option>
          <Select.Option value="closed">已关闭</Select.Option>
        </Select>
        <Button 
          type="primary" 
          onClick={handleSearch} 
          style={{ marginLeft: 8 }}
        >
          查询
        </Button>
        <Button 
          onClick={clearFilters} 
          style={{ marginLeft: 8 }}
        >
          重置
        </Button>
      </div>
      
      <PageHeader 
        title="代码审查详情" 
        backPath="/code-review"
      />
      
      {loading ? (
        <Card>
          <Skeleton active paragraph={{ rows: 10 }} />
        </Card>
      ) : !reviewDetail ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={4}>未找到代码审查详情</Title>
            <Paragraph>该代码审查可能不存在或已被删除</Paragraph>
            <Button type="primary" onClick={() => navigate('/code-review')}>
              返回列表
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* 详情卡片 */}
          <Card 
            title={
              <Space size="middle">
                <Text strong>{reviewDetail.title || '无标题'}</Text>
                <Tag color={statusColorMap[reviewDetail.status] || 'default'}>
                  {statusTextMap[reviewDetail.status] || reviewDetail.status}
                </Tag>
              </Space>
            }
            extra={
              <Permission roles={['admin', 'reviewer', 'developer']}>
                <Space>
                  <Button 
                    type="primary"
                    onClick={() => {
                      setSelectedStatus(reviewDetail.status);
                      setStatusModalVisible(true);
                    }}
                  >
                    更新状态
                  </Button>
                </Space>
              </Permission>
            }
            style={{ marginBottom: 20 }}
          >
            <Row gutter={[16, 24]}>
              <Col span={24}>
                <Paragraph>
                  {reviewDetail.description || '无描述'}
                </Paragraph>
              </Col>
            </Row>
            
            <Divider />
            
            <Descriptions title="基本信息" column={{ xs: 1, sm: 2, md: 3 }}>
              <Descriptions.Item label="ID">{reviewDetail.id}</Descriptions.Item>
              <Descriptions.Item label="项目">{reviewDetail.project_name || '未知项目'}</Descriptions.Item>
              <Descriptions.Item label="提交">{reviewDetail.commit_id || '未知'}</Descriptions.Item>
              <Descriptions.Item label="问题类型">
                {reviewDetail.issue_type ? 
                  issueTypeTextMap[reviewDetail.issue_type] || reviewDetail.issue_type 
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="优先级">
                {reviewDetail.priority ? (
                  <Tag color={reviewDetail.priority === 'high' ? 'red' : reviewDetail.priority === 'medium' ? 'orange' : 'blue'}>
                    {priorityTextMap[reviewDetail.priority] || reviewDetail.priority}
                  </Tag>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="严重程度">
                {reviewDetail.severity ? (
                  <Tag color={reviewDetail.severity === 'high' ? 'red' : reviewDetail.severity === 'medium' ? 'orange' : 'blue'}>
                    {severityTextMap[reviewDetail.severity] || reviewDetail.severity}
                  </Tag>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="文件路径">{reviewDetail.file_path || '-'}</Descriptions.Item>
              <Descriptions.Item label="行号">
                {reviewDetail.line_start && reviewDetail.line_end
                  ? `${reviewDetail.line_start}-${reviewDetail.line_end}`
                  : reviewDetail.line_start || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建者">{reviewDetail.creator_name || '未知'}</Descriptions.Item>
              <Descriptions.Item label="指派给">{reviewDetail.reviewer_name || '未指派'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatDate(reviewDetail.created_at)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{formatDate(reviewDetail.updated_at)}</Descriptions.Item>
              {reviewDetail.resolved_at && (
                <Descriptions.Item label="解决时间">{formatDate(reviewDetail.resolved_at)}</Descriptions.Item>
              )}
            </Descriptions>
          </Card>
          
          {/* 评论、历史等选项卡 */}
          <Card>
            <Tabs defaultActiveKey="comments">
              <TabPane 
                tab={
                  <span>
                    <MessageOutlined />
                    评论
                  </span>
                } 
                key="comments"
              >
                {/* 评论列表 */}
                {commentsLoading ? (
                  <Skeleton active avatar paragraph={{ rows: 3 }} />
                ) : (
                  <>
                    <List
                      className="comment-list"
                      header={`${comments.length} 条评论`}
                      itemLayout="horizontal"
                      dataSource={comments}
                      locale={{ emptyText: '暂无评论' }}
                      renderItem={(item: CodeReviewComment) => (
                        <List.Item>
                          <List.Item.Meta
                            avatar={<Avatar icon={<UserOutlined />} alt={item.user?.username} />}
                            title={<>
                              <a>{item.user?.username || '未知用户'}</a>
                              <span style={{ marginLeft: 8, fontSize: '12px', color: 'rgba(0,0,0,0.45)' }}>
                                {formatDate(item.created_at)}
                              </span>
                            </>}
                            description={<p>{item.content}</p>}
                          />
                        </List.Item>
                      )}
                    />
                    
                    <Divider />
                    
                    {/* 添加评论表单 */}
                    <Form form={form} onFinish={handleSubmitComment}>
                      <Form.Item name="content" rules={[{ required: true, message: '请输入评论内容' }]}>
                        <TextArea rows={4} placeholder="请输入评论内容..." />
                      </Form.Item>
                      <Form.Item>
                        <Button 
                          htmlType="submit" 
                          type="primary" 
                          loading={submitting}
                          icon={<SendOutlined />}
                        >
                          发送评论
                        </Button>
                      </Form.Item>
                    </Form>
                  </>
                )}
              </TabPane>
              <TabPane 
                tab={
                  <span>
                    <HistoryOutlined />
                    历史记录
                  </span>
                } 
                key="history"
              >
                <div style={{ padding: '20px 0', textAlign: 'center' }}>
                  <Text type="secondary">历史记录功能正在开发中...</Text>
                </div>
              </TabPane>
              <TabPane 
                tab={
                  <span>
                    <FileTextOutlined />
                    代码差异
                  </span>
                } 
                key="diff"
              >
                <div style={{ padding: '20px 0', textAlign: 'center' }}>
                  <Text type="secondary">代码差异功能正在开发中...</Text>
                </div>
              </TabPane>
            </Tabs>
          </Card>
        </>
      )}
      
      {/* 更新状态弹窗 */}
      <Modal
        title="更新代码审查状态"
        open={statusModalVisible}
        onCancel={() => setStatusModalVisible(false)}
        onOk={handleUpdateStatus}
        confirmLoading={submitting}
      >
        <Form layout="vertical">
          <Form.Item label="选择新状态" required>
            <Select 
              value={selectedStatus} 
              onChange={setSelectedStatus}
              style={{ width: '100%' }}
            >
              {statusOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CodeReviewDetail; 