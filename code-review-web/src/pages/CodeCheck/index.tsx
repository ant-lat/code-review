import React, { useState, useEffect } from 'react';
import { Card, Button, Form, Select, Input, Space, Tag, message, Spin, Progress, Row, Col, Statistic } from 'antd';
import { ScanOutlined, FileSearchOutlined, CodeOutlined, WarningOutlined, BugOutlined } from '@ant-design/icons';
import { getProjects } from '../../api/projects';
import { Project } from '../../api/types';
import { Table } from '../../components'; // 导入自定义Table组件

// 定义代码检查响应接口
interface CodeCheckResponse {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  results?: {
    issues: Array<{
      id: string;
      file: string;
      line: number;
      column: number;
      severity: 'high' | 'medium' | 'low';
      message: string;
      rule: string;
    }>;
    summary: {
      totalIssues: number;
      highSeverity: number;
      mediumSeverity: number;
      lowSeverity: number;
    };
  };
  created_at: string;
  metrics?: {
    complexity: number;
    cyclomatic_complexity: number;
    duplicated_lines: number;
    maintainability: number;
    test_coverage: number;
    code_smells: number;
    security_vulnerabilities: number;
  };
  report_url?: string;
}

const { TextArea } = Input;

const CodeCheck: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [scanResults, setScanResults] = useState<CodeCheckResponse | null>(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);

  // 获取项目列表
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await getProjects({ limit: 100 });
        setProjects(res.data.items || []);
      } catch (error) {
        console.error('获取项目列表失败:', error);
        message.error('获取项目列表失败');
      }
    };
    fetchProjects();
  }, []);

  // 启动代码检查
  const startCodeCheck = async (values: any) => {
    setScanning(true);
    setScanResults(null);
    try {
      // 模拟调用API，实际项目中应替换为真实的API调用
      // const response = await codeAPI.check(values);
      setTimeout(() => {
        const mockResult: CodeCheckResponse = {
          id: Date.now().toString(),
          status: 'running',
          created_at: new Date().toISOString()
        };
        setScanResults(mockResult);
        
        // 启动轮询检查状态
        const interval = setInterval(() => checkScanStatus(mockResult.id), 2000);
        setStatusCheckInterval(interval);
      }, 1000);
    } catch (error) {
      console.error('启动代码检查失败:', error);
      message.error('启动代码检查失败');
      setScanning(false);
    }
  };

  // 检查扫描状态
  const checkScanStatus = (id: string) => {
    // 模拟API调用检查状态
    // 实际项目中应该替换为真实的API调用
    setTimeout(() => {
      // 随机决定扫描是否完成
      const isCompleted = Math.random() > 0.5;
      
      if (isCompleted) {
        if (statusCheckInterval) {
          clearInterval(statusCheckInterval);
          setStatusCheckInterval(null);
        }
        
        const mockResults: CodeCheckResponse = {
          id,
          status: 'completed',
          created_at: new Date().toISOString(),
          results: {
            issues: Array(Math.floor(Math.random() * 20)).fill(0).map((_, i) => ({
              id: `issue-${i}`,
              file: `src/components/Component${i}.tsx`,
              line: Math.floor(Math.random() * 100) + 1,
              column: Math.floor(Math.random() * 50) + 1,
              severity: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)] as 'high' | 'medium' | 'low',
              message: `Issue ${i} description`,
              rule: `rule-${i}`
            })),
            summary: {
              totalIssues: Math.floor(Math.random() * 30),
              highSeverity: Math.floor(Math.random() * 10),
              mediumSeverity: Math.floor(Math.random() * 15),
              lowSeverity: Math.floor(Math.random() * 5)
            }
          },
          metrics: {
            complexity: Math.floor(Math.random() * 100),
            cyclomatic_complexity: Math.floor(Math.random() * 100),
            duplicated_lines: Math.floor(Math.random() * 50),
            maintainability: Math.floor(Math.random() * 100),
            test_coverage: Math.floor(Math.random() * 100),
            code_smells: Math.floor(Math.random() * 5),
            security_vulnerabilities: Math.floor(Math.random() * 1)
          },
          report_url: `/reports/${id}`
        };
        
        setScanResults(mockResults);
        setScanning(false);
        message.success('代码检查完成');
      }
    }, 500);
  };

  const renderMetrics = () => {
    if (!scanResults || !scanResults.metrics) return null;
    
    return (
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic
              title="代码复杂度"
              value={scanResults.metrics.cyclomatic_complexity}
              prefix={<CodeOutlined />}
              valueStyle={{ color: scanResults.metrics.cyclomatic_complexity > 50 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="代码异味"
              value={scanResults.metrics.code_smells}
              prefix={<WarningOutlined />}
              valueStyle={{ color: scanResults.metrics.code_smells > 10 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="安全漏洞"
              value={scanResults.metrics.security_vulnerabilities}
              prefix={<BugOutlined />}
              valueStyle={{ color: scanResults.metrics.security_vulnerabilities > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  const renderResults = () => {
    if (!scanResults || scanResults.status !== 'completed') return null;
    
    return (
      <div style={{ marginTop: 24 }}>
        {renderMetrics()}
        
        {scanResults.report_url && (
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Button
              type="primary"
              icon={<FileSearchOutlined />}
              onClick={() => window.open(scanResults.report_url, '_blank')}
            >
              查看详细报告
            </Button>
          </div>
        )}
        
        <Table
          dataSource={scanResults.results?.issues || []}
          columns={issueColumns}
          rowKey="id"
          style={{ marginTop: 24 }}
          pagination={{ pageSize: 10 }}
        />
      </div>
    );
  };

  // 问题表格列定义
  const issueColumns = [
    {
      title: '文件',
      dataIndex: 'file',
      key: 'file',
    },
    {
      title: '位置',
      key: 'position',
      render: (text: any, record: any) => `第${record.line}行, 第${record.column}列`,
    },
    {
      title: '严重性',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={
          severity === 'high' ? 'red' :
          severity === 'medium' ? 'orange' : 'blue'
        }>
          {severity === 'high' ? '高' :
           severity === 'medium' ? '中' : '低'}
        </Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '规则',
      dataIndex: 'rule',
      key: 'rule',
    },
  ];

  return (
    <div className="code-check-container">
      <Card title="代码质量检查">
        <Form form={form} onFinish={startCodeCheck} layout="vertical">
          <Form.Item
            name="project_id"
            label="选择项目"
            rules={[{ required: true, message: '请选择项目' }]}
          >
            <Select>
              {projects.map(project => (
                <Select.Option key={project.id} value={project.id}>
                  {project.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="scan_type"
            label="扫描类型"
            rules={[{ required: true, message: '请选择扫描类型' }]}
          >
            <Select>
              <Select.Option value="full">完整扫描</Select.Option>
              <Select.Option value="incremental">增量扫描</Select.Option>
              <Select.Option value="multi-repo">多仓库扫描</Select.Option>
              <Select.Option value="cross-repo">跨仓库对比</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues?.scan_type !== currentValues?.scan_type
            }
          >
            {({ getFieldValue }) => {
              const scanType = getFieldValue('scan_type');
              if (scanType === 'multi-repo' || scanType === 'cross-repo') {
                return (
                  <Form.Item
                    name="comparison_strategy"
                    label="对比策略"
                    rules={[{ required: true, message: '请选择对比策略' }]}
                  >
                    <Select>
                      <Select.Option value="branch-diff">分支差异</Select.Option>
                      <Select.Option value="cross-repo-diff">跨仓库差异</Select.Option>
                    </Select>
                  </Form.Item>
                );
              }
              return null;
            }}
          </Form.Item>

          <Form.Item
            name="target_branch"
            label="目标分支"
          >
            <Input placeholder="可选，默认为main分支" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              icon={<ScanOutlined />}
              loading={scanning}
              onClick={() => form.submit()}
            >
              开始扫描
            </Button>
          </Form.Item>
        </Form>

        {scanning ? (
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>正在进行代码扫描，请稍候...</p>
          </div>
        ) : (
          renderResults()
        )}
      </Card>
    </div>
  );
};

export default CodeCheck; 