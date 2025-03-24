import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tabs, Statistic, Row, Col, Progress, Select, Spin } from 'antd';
import { 
  CodeOutlined, 
  BugOutlined, 
  WarningOutlined, 
  CheckCircleOutlined, 
  BarChartOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';

const { TabPane } = Tabs;
const { Option } = Select;

// 模拟项目数据
const projects = [
  { id: 1, name: '项目一' },
  { id: 2, name: '项目二' },
  { id: 3, name: '项目三' },
];

// 模拟分析记录数据
const analysisList = [
  { 
    id: 1, 
    project_id: 1, 
    commit_id: 'abc123', 
    analyzed_at: '2025-03-13T10:15:00Z',
    complexity: 75,
    bug_count: 12,
    warning_count: 28,
    code_quality: 'B',
  },
  { 
    id: 2, 
    project_id: 1, 
    commit_id: 'def456', 
    analyzed_at: '2025-03-12T14:30:00Z',
    complexity: 68,
    bug_count: 15,
    warning_count: 32,
    code_quality: 'C',
  },
  { 
    id: 3, 
    project_id: 2, 
    commit_id: 'ghi789', 
    analyzed_at: '2025-03-11T09:45:00Z',
    complexity: 82,
    bug_count: 5,
    warning_count: 17,
    code_quality: 'A',
  },
];

const CodeAnalysisPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(analysisList);
  const [currentProject, setCurrentProject] = useState<number | undefined>(undefined);
  const [activeKey, setActiveKey] = useState('overview');
  const navigate = useNavigate();
  
  // 处理项目选择
  const handleProjectChange = (projectId: number) => {
    setCurrentProject(projectId);
    if (projectId) {
      // 根据项目筛选分析记录
      setData(analysisList.filter(item => item.project_id === projectId));
    } else {
      setData(analysisList);
    }
  };
  
  // 模拟运行分析
  const handleRunAnalysis = () => {
    if (!currentProject) {
      return;
    }
    
    setLoading(true);
    // 这里应该是实际的API调用
    setTimeout(() => {
      setLoading(false);
      // 模拟新增一条分析记录
      const newAnalysis = {
        id: Date.now(),
        project_id: currentProject,
        commit_id: Math.random().toString(36).substring(2, 8),
        analyzed_at: new Date().toISOString(),
        complexity: Math.floor(Math.random() * 30) + 70,
        bug_count: Math.floor(Math.random() * 20),
        warning_count: Math.floor(Math.random() * 40),
        code_quality: ['A', 'B', 'C'][Math.floor(Math.random() * 3)],
      };
      
      setData([newAnalysis, ...data]);
    }, 2000);
  };
  
  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '项目',
      dataIndex: 'project_id',
      key: 'project_id',
      render: (projectId: number) => {
        const project = projects.find(p => p.id === projectId);
        return project ? project.name : `项目 ${projectId}`;
      },
    },
    {
      title: '提交哈希',
      dataIndex: 'commit_id',
      key: 'commit_id',
      render: (hash: string) => hash.substring(0, 7),
    },
    {
      title: '复杂度',
      dataIndex: 'complexity',
      key: 'complexity',
    },
    {
      title: 'Bug数',
      dataIndex: 'bug_count',
      key: 'bug_count',
    },
    {
      title: '警告数',
      dataIndex: 'warning_count',
      key: 'warning_count',
    },
    {
      title: '代码质量',
      dataIndex: 'code_quality',
      key: 'code_quality',
      render: (quality: string) => {
        let color = '';
        switch (quality) {
          case 'A':
            color = 'green';
            break;
          case 'B':
            color = 'blue';
            break;
          case 'C':
            color = 'orange';
            break;
          default:
            color = 'red';
        }
        return <span style={{ color }}>{quality}</span>;
      },
    },
    {
      title: '分析时间',
      dataIndex: 'analyzed_at',
      key: 'analyzed_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="link" onClick={() => navigate(`/code-analysis/${record.id}`)}>
            查看详情
          </Button>
        </Space>
      ),
    },
  ];
  
  // 最新的分析记录
  const latestAnalysis = data.length > 0 ? data[0] : null;
  
  return (
    <div>
      <PageHeader title="代码分析" />
      
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Space size="large">
            <span>选择项目：</span>
            <Select
              style={{ width: 200 }}
              placeholder="请选择项目"
              onChange={handleProjectChange}
              allowClear
            >
              {projects.map(project => (
                <Option key={project.id} value={project.id}>{project.name}</Option>
              ))}
            </Select>
          </Space>
          
          <Permission roles={['admin', 'developer']}>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              disabled={!currentProject || loading}
              loading={loading}
              onClick={handleRunAnalysis}
            >
              运行分析
            </Button>
          </Permission>
        </div>
      </Card>
      
      <Tabs activeKey={activeKey} onChange={setActiveKey}>
        <TabPane tab="概览" key="overview">
          {latestAnalysis ? (
            <Card>
              <Row gutter={16}>
                <Col span={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="代码复杂度"
                      value={latestAnalysis.complexity}
                      prefix={<CodeOutlined />}
                      suffix="/ 100"
                    />
                    <Progress
                      percent={latestAnalysis.complexity}
                      status={
                        latestAnalysis.complexity > 80 ? 'exception' :
                        latestAnalysis.complexity > 60 ? 'normal' : 'success'
                      }
                      showInfo={false}
                      style={{ marginTop: 8 }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="Bug数量"
                      value={latestAnalysis.bug_count}
                      prefix={<BugOutlined />}
                      valueStyle={{ color: latestAnalysis.bug_count > 10 ? '#cf1322' : '#3f8600' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="警告数量"
                      value={latestAnalysis.warning_count}
                      prefix={<WarningOutlined />}
                      valueStyle={{ color: latestAnalysis.warning_count > 20 ? '#faad14' : '#3f8600' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="代码质量"
                      value={latestAnalysis.code_quality}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ 
                        color: 
                          latestAnalysis.code_quality === 'A' ? '#3f8600' : 
                          latestAnalysis.code_quality === 'B' ? '#1890ff' : 
                          latestAnalysis.code_quality === 'C' ? '#faad14' : '#cf1322'
                      }}
                    />
                  </Card>
                </Col>
              </Row>
            </Card>
          ) : (
            <Card>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                {loading ? (
                  <Spin tip="分析中..." />
                ) : (
                  <div>
                    <p>暂无分析数据</p>
                    <Button type="primary" onClick={() => setActiveKey('history')}>查看历史分析</Button>
                  </div>
                )}
              </div>
            </Card>
          )}
        </TabPane>
        <TabPane tab="历史记录" key="history">
          <Card>
            <Table
              columns={columns}
              dataSource={data}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
        <TabPane tab="热点分析" key="hotspots">
          <Card>
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <p style={{ marginTop: 16 }}>热点分析功能正在开发中...</p>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default CodeAnalysisPage; 