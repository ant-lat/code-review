import React, { useState, useEffect } from 'react';
import { Card, Select, Button, Tabs, Spin, Empty, Row, Col, Statistic, Divider, Typography, Table } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import { getAnalysisHistory, compareAnalysisResults } from '../../../api/codeAnalysis';

const { Option } = Select;
const { Title, Text } = Typography;

interface AnalysisHistoryCompareProps {
  projectId: number;
}

interface AnalysisResult {
  id: number;
  project_id: number;
  commit_id: string;
  started_at: string;
  completed_at: string;
  status: string;
  summary?: string;
}

interface ComparisonResult {
  code_quality: {
    before: any;
    after: any;
    diff: any;
  };
  code_metrics: {
    before: any;
    after: any;
    diff: any;
  };
  issues: {
    new: any[];
    fixed: any[];
    unchanged: any[];
  };
}

const AnalysisHistoryCompare: React.FC<AnalysisHistoryCompareProps> = ({ projectId }) => {
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([]);
  const [beforeId, setBeforeId] = useState<number | null>(null);
  const [afterId, setAfterId] = useState<number | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [activeTab, setActiveTab] = useState('code_quality');

  const fetchAnalysisHistory = async () => {
    try {
      setLoading(true);
      const response = await getAnalysisHistory(projectId);
      setAnalysisHistory(response.data || []);
      
      if (response.data?.length >= 2) {
        setBeforeId(response.data[1].id);
        setAfterId(response.data[0].id);
      }
    } catch (error) {
      console.error('获取分析历史失败', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!beforeId || !afterId) return;
    
    try {
      setCompareLoading(true);
      const result = await compareAnalysisResults(beforeId, afterId);
      setComparisonResult(result.data);
    } catch (error) {
      console.error('比较分析结果失败', error);
    } finally {
      setCompareLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchAnalysisHistory();
    }
  }, [projectId]);

  const renderDiffValue = (before: number, after: number) => {
    const diff = after - before;
    if (diff > 0) {
      return (
        <Text type="danger">
          <ArrowUpOutlined /> +{diff.toFixed(2)}
        </Text>
      );
    } else if (diff < 0) {
      return (
        <Text type="success">
          <ArrowDownOutlined /> {diff.toFixed(2)}
        </Text>
      );
    } else {
      return (
        <Text>
          <MinusOutlined /> 0
        </Text>
      );
    }
  };

  const renderCodeQualityTab = () => {
    if (!comparisonResult?.code_quality) return <Empty description="暂无对比数据" />;
    
    const { before, after, diff } = comparisonResult.code_quality;
    
    return (
      <div>
        <Row gutter={24}>
          <Col span={8}>
            <Card title="代码质量评分">
              <Statistic
                title="变化"
                value={after.score - before.score}
                precision={2}
                valueStyle={{ color: after.score >= before.score ? '#3f8600' : '#cf1322' }}
                prefix={after.score >= before.score ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="分"
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="前" value={before.score} precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="后" value={after.score} precision={2} />
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="代码问题数">
              <Statistic
                title="变化"
                value={before.issues_count - after.issues_count}
                precision={0}
                valueStyle={{ color: after.issues_count <= before.issues_count ? '#3f8600' : '#cf1322' }}
                prefix={after.issues_count <= before.issues_count ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
                suffix="个"
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="前" value={before.issues_count} />
                </Col>
                <Col span={12}>
                  <Statistic title="后" value={after.issues_count} />
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="重复代码率">
              <Statistic
                title="变化"
                value={after.duplication_rate - before.duplication_rate}
                precision={2}
                valueStyle={{ color: after.duplication_rate <= before.duplication_rate ? '#3f8600' : '#cf1322' }}
                prefix={after.duplication_rate <= before.duplication_rate ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
                suffix="%"
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="前" value={before.duplication_rate} precision={2} suffix="%" />
                </Col>
                <Col span={12}>
                  <Statistic title="后" value={after.duplication_rate} precision={2} suffix="%" />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  const renderCodeMetricsTab = () => {
    if (!comparisonResult?.code_metrics) return <Empty description="暂无对比数据" />;
    
    const { before, after } = comparisonResult.code_metrics;
    
    return (
      <div>
        <Row gutter={24}>
          <Col span={8}>
            <Card title="代码行数">
              <Statistic
                title="变化"
                value={after.lines - before.lines}
                valueStyle={{ color: '#1890ff' }}
                prefix={after.lines > before.lines ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="行"
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="前" value={before.lines} />
                </Col>
                <Col span={12}>
                  <Statistic title="后" value={after.lines} />
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="文件数">
              <Statistic
                title="变化"
                value={after.files - before.files}
                valueStyle={{ color: '#1890ff' }}
                prefix={after.files > before.files ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="个"
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="前" value={before.files} />
                </Col>
                <Col span={12}>
                  <Statistic title="后" value={after.files} />
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="函数数">
              <Statistic
                title="变化"
                value={after.functions - before.functions}
                valueStyle={{ color: '#1890ff' }}
                prefix={after.functions > before.functions ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="个"
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="前" value={before.functions} />
                </Col>
                <Col span={12}>
                  <Statistic title="后" value={after.functions} />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  const renderIssuesTab = () => {
    if (!comparisonResult?.issues) return <Empty description="暂无对比数据" />;
    
    const { new: newIssues, fixed: fixedIssues } = comparisonResult.issues;
    
    const newIssuesColumns = [
      { title: '问题', dataIndex: 'message', key: 'message' },
      { title: '文件', dataIndex: 'file', key: 'file' },
      { title: '行号', dataIndex: 'line', key: 'line' },
      { title: '严重性', dataIndex: 'severity', key: 'severity' }
    ];
    
    const fixedIssuesColumns = [
      { title: '问题', dataIndex: 'message', key: 'message' },
      { title: '文件', dataIndex: 'file', key: 'file' },
      { title: '行号', dataIndex: 'line', key: 'line' },
      { title: '严重性', dataIndex: 'severity', key: 'severity' }
    ];
    
    return (
      <div>
        <Title level={4}>新增问题 ({newIssues.length})</Title>
        <Table 
          dataSource={newIssues} 
          columns={newIssuesColumns} 
          rowKey="id"
          pagination={{ pageSize: 5 }}
        />
        
        <Divider />
        
        <Title level={4}>已修复问题 ({fixedIssues.length})</Title>
        <Table 
          dataSource={fixedIssues} 
          columns={fixedIssuesColumns} 
          rowKey="id"
          pagination={{ pageSize: 5 }}
        />
      </div>
    );
  };

  const renderTabContent = () => {
    if (compareLoading) return <Spin size="large" />;
    if (!comparisonResult) return <Empty description="请选择两次分析结果进行比较" />;
    
    switch (activeTab) {
      case 'code_quality':
        return renderCodeQualityTab();
      case 'code_metrics':
        return renderCodeMetricsTab();
      case 'issues':
        return renderIssuesTab();
      default:
        return <Empty description="未知标签页" />;
    }
  };

  return (
    <Card title="分析历史对比">
      {loading ? (
        <Spin />
      ) : (
        <>
          <div style={{ marginBottom: 20 }}>
            <Row gutter={16}>
              <Col span={10}>
                <div style={{ marginBottom: 8 }}>基准分析:</div>
                <Select
                  style={{ width: '100%' }}
                  placeholder="选择基准分析结果"
                  value={beforeId}
                  onChange={setBeforeId}
                >
                  {analysisHistory.map(item => (
                    <Option key={item.id} value={item.id}>
                      {item.commit_id.substring(0, 8)} ({new Date(item.completed_at).toLocaleString()})
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col span={10}>
                <div style={{ marginBottom: 8 }}>比较分析:</div>
                <Select
                  style={{ width: '100%' }}
                  placeholder="选择比较分析结果"
                  value={afterId}
                  onChange={setAfterId}
                >
                  {analysisHistory.map(item => (
                    <Option key={item.id} value={item.id}>
                      {item.commit_id.substring(0, 8)} ({new Date(item.completed_at).toLocaleString()})
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col span={4}>
                <div style={{ marginBottom: 8 }}>&nbsp;</div>
                <Button 
                  type="primary" 
                  onClick={handleCompare} 
                  disabled={!beforeId || !afterId || beforeId === afterId}
                  loading={compareLoading}
                  style={{ width: '100%' }}
                >
                  比较
                </Button>
              </Col>
            </Row>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'code_quality',
                label: '代码质量',
                children: null
              },
              {
                key: 'code_metrics',
                label: '代码指标',
                children: null
              },
              {
                key: 'issues',
                label: '问题变化',
                children: null
              }
            ]}
          />
          
          <div className="tab-content" style={{ marginTop: 16 }}>
            {renderTabContent()}
          </div>
        </>
      )}
    </Card>
  );
};

export default AnalysisHistoryCompare; 