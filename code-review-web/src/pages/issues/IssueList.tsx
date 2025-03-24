import React, { useState, useEffect } from 'react';
import { Table, Tag, Space, Button, Input, Pagination, Select } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';
import { getIssues } from '../../api/issues';
import { Issue } from '../../api/types';

const { Search } = Input;
const { Option } = Select;

interface IssueListProps {
  projectId?: number;
}

const IssueList: React.FC<IssueListProps> = ({ projectId }) => {
  const [searchText, setSearchText] = useState('');
  const [loading, setLoading] = useState(false);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10
  });
  const [filters, setFilters] = useState({
    severity: undefined as string | undefined,
    status: undefined as string | undefined
  });

  // 获取数据
  useEffect(() => {
    const fetchIssues = async () => {
      setLoading(true);
      try {
        const params = {
          page: pagination.current,
          page_size: pagination.pageSize,
          search: searchText || undefined,
          severity: filters.severity,
          status: filters.status,
          project_id: projectId
        };

        const response = await getIssues(params);
        setIssues(response.data || []);
        setTotal(response.total || 0);
      } catch (error) {
        console.error('获取问题列表失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchIssues();
  }, [pagination, searchText, filters, projectId]);

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
    setPagination({ ...pagination, current: 1 });
  };

  // 处理筛选
  const handleFilterChange = (field: string, value: any) => {
    setFilters({ ...filters, [field]: value });
    setPagination({ ...pagination, current: 1 });
  };

  // 处理分页变化
  const handlePageChange = (page: number, pageSize?: number) => {
    setPagination({
      current: page,
      pageSize: pageSize || pagination.pageSize
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => {
        const color = {
          high: 'red',
          medium: 'orange',
          low: 'green',
        }[severity] || 'default';
        return <Tag color={color}>{severity ? severity.toUpperCase() : '-'}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { color: string, text: string }> = {
          open: { color: 'red', text: '待处理' },
          in_progress: { color: 'blue', text: '处理中' },
          resolved: { color: 'green', text: '已解决' },
          closed: { color: 'gray', text: '已关闭' },
        };
        const { color, text } = statusMap[status] || { color: 'default', text: status || '-' };
        return <Tag color={color}>{text}</Tag>;
      }
    },
    {
      title: '负责人',
      dataIndex: 'assignee_name',
      key: 'assignee_name',
      render: (name: string) => name || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Issue) => (
        <Space size="middle">
          <a href={`/issues/${record.id}`}>查看</a>
          <a href={`/issues/${record.id}/edit`}>编辑</a>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />}>
            新建问题
          </Button>
          <Search
            placeholder="搜索问题"
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            style={{ width: 200 }}
          />
          <Select
            placeholder="严重程度"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => handleFilterChange('severity', value)}
          >
            <Option value="high">高</Option>
            <Option value="medium">中</Option>
            <Option value="low">低</Option>
          </Select>
          <Select
            placeholder="状态"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => handleFilterChange('status', value)}
          >
            <Option value="open">待处理</Option>
            <Option value="in_progress">处理中</Option>
            <Option value="resolved">已解决</Option>
            <Option value="closed">已关闭</Option>
          </Select>
        </Space>
      </div>
      <Table 
        columns={columns} 
        dataSource={issues} 
        rowKey="id" 
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: total,
          onChange: handlePageChange,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`
        }}
      />
    </div>
  );
};

export default IssueList; 