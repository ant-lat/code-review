import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, 
  Tabs, 
  Descriptions, 
  Tag, 
  Spin, 
  Button, 
  message, 
  Space,
  Statistic,
  Row,
  Col,
  Timeline,
  Avatar
} from 'antd';
import {
  EditOutlined,
  TeamOutlined,
  BugOutlined,
  CodeOutlined,
  ClockCircleOutlined,
  UserOutlined
} from '@ant-design/icons';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';
import { getProjectById, getProjectStats, getProjectActivities } from '../../api/projects';
import { formatDateTime, formatRelativeTime } from '../../utils';
import ProjectForm from './components/ProjectForm';
import ProjectMembers from './components/ProjectMembers';

const { TabPane } = Tabs;

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = parseInt(id || '0');

  const [loading, setLoading] = useState(true);
  const [projectData, setProjectData] = useState<any>(null);
  const [statsData, setStatsData] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [statsLoading, setStatsLoading] = useState(false);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);

  // 递归提取数据函数
  const extractData = (response: any): any => {
    try {
      // 如果是null或undefined，返回null
      if (response == null) return null;
      
      // 如果是数组，直接返回
      if (Array.isArray(response)) return response;
      
      // 如果是对象，检查是否有data或items字段
      if (typeof response === 'object') {
        // 检查data字段
        if (response.data !== undefined) {
          // 递归处理data字段
          return extractData(response.data);
        }
        
        // 检查items字段
        if (response.items !== undefined && Array.isArray(response.items)) {
          return response.items;
        }
        
        // 如果没有data或items字段，返回原对象
        return response;
      }
      
      // 其他情况返回原始值
      return response;
    } catch (error) {
      console.error('提取数据时出错:', error);
      return null;
    }
  };

  // 获取项目详情
  const fetchProjectDetail = async () => {
    setLoading(true);
    try {
      const response = await getProjectById(projectId);
      console.log('原始项目详情数据:', response);
      
      // 提取数据
      const extractedData = extractData(response);
      console.log('提取后的项目详情数据:', extractedData);
      
      if (extractedData) {
        setProjectData(extractedData);
      } else {
        message.warning('无法解析项目详情数据');
      }
    } catch (error) {
      console.error('获取项目详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取项目统计信息
  const fetchProjectStats = async () => {
    setStatsLoading(true);
    try {
      const response = await getProjectStats(projectId);
      console.log('原始项目统计数据:', response);
      
      // 提取数据 - 对于统计信息特殊处理
      let statsData = null;
      if (response) {
        if (response.data) {
          // 数据在data字段中
          statsData = response.data;
        } else if (response.code === 200) {
          // 响应本身可能包含数据，但需要过滤掉响应元数据
          // 创建一个新对象，只保留业务数据
          const { code, message, timestamp, ...businessData } = response as any;
          
          // 检查businessData是否有意义的内容
          if (Object.keys(businessData).length > 0) {
            statsData = businessData;
          }
        }
      }
      
      console.log('提取后的项目统计数据:', statsData);
      
      if (statsData) {
        setStatsData(statsData);
      } else {
        message.warning('无法解析项目统计数据');
      }
    } catch (error) {
      console.error('获取项目统计失败:', error);
    } finally {
      setStatsLoading(false);
    }
  };

  // 获取项目活动历史
  const fetchProjectActivities = async () => {
    setActivitiesLoading(true);
    try {
      const response = await getProjectActivities(projectId, { page: 1, page_size: 10 });
      console.log('原始项目活动数据:', response);
      
      // 提取数据
      const extractedData = extractData(response);
      console.log('提取后的项目活动数据:', extractedData);
      
      // 确保是数组
      if (extractedData) {
        const activitiesList = Array.isArray(extractedData) ? extractedData : 
                              (extractedData.items && Array.isArray(extractedData.items)) ? extractedData.items : [];
        setActivities(activitiesList);
      } else {
        setActivities([]);
      }
    } catch (error) {
      console.error('获取项目活动失败:', error);
      setActivities([]);
    } finally {
      setActivitiesLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      Promise.all([
        fetchProjectDetail(),
        fetchProjectStats(),
        fetchProjectActivities()
      ]).catch(error => {
        console.error('加载项目数据时出错:', error);
      });
    }
  }, [projectId]);

  // 处理表单提交后的操作
  const handleFormFinish = () => {
    setEditModalVisible(false);
    fetchProjectDetail();
  };

  // 渲染项目基本信息
  const renderBasicInfo = () => {
    if (!projectData) return null;

    return (
      <Card 
        title="基本信息" 
        extra={
          <Permission roles={['admin']} projectRoles={['owner']} projectId={projectId}>
            <Button 
              type="primary" 
              icon={<EditOutlined />} 
              onClick={() => setEditModalVisible(true)}
            >
              编辑项目
            </Button>
          </Permission>
        }
      >
        <Descriptions bordered column={2}>
          <Descriptions.Item label="项目名称">{projectData.name}</Descriptions.Item>
          <Descriptions.Item label="项目ID">{projectData.id}</Descriptions.Item>
          <Descriptions.Item label="仓库类型">
            <Tag color={
              projectData.repository_type === 'git' ? 'blue' :
              projectData.repository_type === 'svn' ? 'green' : 'default'
            }>
              {projectData.repository_type?.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="项目状态">
            <Tag color={projectData.is_active ? 'success' : 'default'}>
              {projectData.is_active ? '活跃' : '已归档'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="仓库地址" span={2}>
            {projectData.repository_url}
          </Descriptions.Item>
          <Descriptions.Item label="分支">{projectData.branch}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{formatDateTime(projectData.created_at)}</Descriptions.Item>
          <Descriptions.Item label="项目描述" span={2}>
            {projectData.description || '暂无描述'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  // 渲染项目统计信息
  const renderStats = () => {
    if (statsLoading) return <Spin />;
    if (!statsData) return null;

    return (
      <Card title="项目统计">
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <Statistic 
              title="代码审查" 
              value={statsData.review_count || 0} 
              prefix={<CodeOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="问题总数" 
              value={statsData.issue_count || 0} 
              prefix={<BugOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="已解决问题" 
              value={statsData.closed_issue_count || 0} 
              prefix={<BugOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="团队成员" 
              value={statsData.member_count || 0} 
              prefix={<TeamOutlined />} 
            />
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染活动历史
  const renderActivities = () => {
    if (activitiesLoading) return <Spin />;

    return (
      <Card title="近期活动">
        <Timeline>
          {activities.map((activity) => (
            <Timeline.Item 
              key={activity.id} 
              dot={
                activity.type === 'commit' ? <CodeOutlined style={{ fontSize: '16px' }} /> :
                activity.type === 'issue' ? <BugOutlined style={{ fontSize: '16px' }} /> :
                <ClockCircleOutlined style={{ fontSize: '16px' }} />
              }
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <div>
                    <Space>
                      <Avatar size="small" icon={<UserOutlined />} />
                      <b>{activity.user_name}</b>
                    </Space>
                    <span style={{ marginLeft: 8 }}>{activity.action}</span>
                    {activity.type === 'commit' && (
                      <a 
                        onClick={() => navigate(`/code-review/${activity.detail_id}`)}
                        style={{ marginLeft: 8 }}
                      >
                        {activity.title}
                      </a>
                    )}
                    {activity.type === 'issue' && (
                      <a 
                        onClick={() => navigate(`/issues/${activity.detail_id}`)}
                        style={{ marginLeft: 8 }}
                      >
                        {activity.title}
                      </a>
                    )}
                  </div>
                  {activity.description && (
                    <p style={{ color: 'rgba(0, 0, 0, 0.45)', margin: '4px 0 0 0' }}>
                      {activity.description}
                    </p>
                  )}
                </div>
                <span style={{ color: 'rgba(0, 0, 0, 0.45)' }}>
                  {formatRelativeTime(activity.created_at)}
                </span>
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </Card>
    );
  };

  const breadcrumbItems = [
    { title: '项目管理', path: '/projects' },
    { title: projectData?.name || '项目详情' }
  ];

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  return (
    <div className="project-detail">
      <PageHeader 
        title={projectData?.name} 
        breadcrumb={breadcrumbItems}
        extra={
          <Space>
            <Button 
              icon={<BugOutlined />} 
              onClick={() => navigate(`/issues?projectId=${projectId}`)}
            >
              问题列表
            </Button>
            <Permission roles={['admin']} projectRoles={['owner', 'manager']} projectId={projectId}>
              <Button 
                icon={<TeamOutlined />} 
                onClick={() => navigate(`/projects/${projectId}/members`)}
              >
                成员管理
              </Button>
            </Permission>
          </Space>
        }
      />

      <Tabs defaultActiveKey="overview">
        <TabPane tab="概览" key="overview">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {renderBasicInfo()}
            {renderStats()}
            {renderActivities()}
          </Space>
        </TabPane>
        <TabPane tab="成员" key="members">
          <ProjectMembers projectId={projectId} onClose={() => {}} />
        </TabPane>
        <TabPane tab="问题" key="issues">
          <Card>
            <div style={{ padding: '20px 0', textAlign: 'center' }}>
              <Button 
                type="primary" 
                onClick={() => navigate(`/issues?projectId=${projectId}`)}
              >
                查看所有问题
              </Button>
            </div>
          </Card>
        </TabPane>
      </Tabs>

      {/* 项目编辑表单 */}
      <ProjectForm
        visible={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onFinish={handleFormFinish}
        initialValues={projectData}
      />
    </div>
  );
};

export default ProjectDetail; 