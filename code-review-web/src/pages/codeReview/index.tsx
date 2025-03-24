import React, { useState, useEffect } from 'react';
import { Button, Card, Space, Tag, Input, Select, DatePicker, message } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/PageHeader';
import Permission from '../../components/Permission';
import { getCodeReviews } from '../../api/codeReview';
import { CodeReview, PageResponse } from '../../api/types';
import dayjs from 'dayjs';
import { Table } from '../../components'; // 导入自定义Table组件

const { RangePicker } = DatePicker;
const { Option } = Select;

const CodeReviewPage: React.FC = () => {
  const [data, setData] = useState<CodeReview[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [searchParams, setSearchParams] = useState({
    status: undefined as string | undefined,
    dateRange: undefined as [dayjs.Dayjs, dayjs.Dayjs] | undefined,
    page: 1,
    pageSize: 10
  });
  const navigate = useNavigate();
  
  // 转换搜索参数为API请求参数
  const getApiParams = () => {
    const params: any = {
      page: searchParams.page,
      page_size: searchParams.pageSize,
      status: searchParams.status
    };
    
    if (searchParams.dateRange && searchParams.dateRange.length === 2) {
      params.start_date = searchParams.dateRange[0].format('YYYY-MM-DD');
      params.end_date = searchParams.dateRange[1].format('YYYY-MM-DD');
    }
    
    return params;
  };
  
  // 加载数据
  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getCodeReviews(getApiParams());
      console.log('代码审查API返回数据:', res);
      
      // 处理嵌套结构的响应数据
      let finalData = [];
      let totalItems = 0;
      
      if (res && res.data) {
        // 处理双层嵌套结构 {data:{data:[...]}}
        if (res.data.data && Array.isArray(res.data.data)) {
          finalData = res.data.data;
          totalItems = res.data.page_info?.total || finalData.length;
          console.log('提取到的列表数据:', finalData);
        } 
        // 处理普通结构 {data:[...]}
        else if (Array.isArray(res.data)) {
          finalData = res.data;
          totalItems = finalData.length;
        } 
        // 处理分页结构 {data:{items:[...]}}
        else if (res.data.items && Array.isArray(res.data.items)) {
          finalData = res.data.items;
          totalItems = res.data.total || res.data.page_info?.total || 0;
        } 
        else {
          console.warn('未识别的响应格式:', res);
          message.error('获取数据失败：未识别的响应格式');
        }
      } else {
        console.error('API返回无效响应:', res);
        message.error('获取数据失败：无效响应');
      }
      
      // 设置数据
      setData(finalData);
      setTotal(totalItems);
    } catch (error: any) {
      console.error('获取代码审查列表失败:', error);
      // 如果不是被取消的请求才显示错误消息
      if (error.name !== 'CanceledError') {
        message.error('获取代码审查列表失败');
      }
      setData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };
  
  // 组件挂载或搜索参数变化时加载数据
  useEffect(() => {
    loadData();
  }, [searchParams]);
  
  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchParams({ ...searchParams, page: 1 });
  };
  
  // 处理状态筛选
  const handleStatusChange = (value: string) => {
    setSearchParams({ ...searchParams, status: value === 'all' ? undefined : value, page: 1 });
  };
  
  // 处理日期范围筛选
  const handleDateRangeChange = (dates: any) => {
    setSearchParams({ ...searchParams, dateRange: dates, page: 1 });
  };
  
  // 处理分页变化
  const handlePageChange = (page: number, pageSize?: number) => {
    setSearchParams({ 
      ...searchParams, 
      page, 
      pageSize: pageSize || searchParams.pageSize 
    });
  };
  
  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '项目',
      dataIndex: 'project_name',
      key: 'project_name',
      width: 120,
    },
    {
      title: '问题类型',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 100,
      render: (type: string) => {
        let text = type;
        switch(type) {
          case 'code_review': text = '代码审查'; break;
          case 'bug': text = '缺陷'; break;
          case 'feature': text = '功能'; break;
          case 'improvement': text = '改进'; break;
          default: text = type || '-';
        }
        return text;
      }
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 90,
      render: (priority: string) => {
        let color = 'default';
        let text = priority || '-';
        
        switch (priority) {
          case 'high':
            color = 'red';
            text = '高';
            break;
          case 'medium':
            color = 'orange';
            text = '中';
            break;
          case 'low':
            color = 'blue';
            text = '低';
            break;
        }
        
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 90,
      render: (severity: string) => {
        let color = 'default';
        let text = severity || '-';
        
        switch (severity) {
          case 'high':
            color = 'red';
            text = '高';
            break;
          case 'medium':
            color = 'orange';
            text = '中';
            break;
          case 'low':
            color = 'blue';
            text = '低';
            break;
        }
        
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '提交ID',
      dataIndex: 'commit_id',
      key: 'commit_id',
      width: 90,
      render: (hash: any): string => {
        // 处理数字或字符串类型的commit_id
        if (hash === null || hash === undefined) return '-';
        if (typeof hash === 'string' && hash.length > 7) {
          return hash.substring(0, 7);
        }
        // 数字或短字符串直接返回
        return String(hash);
      },
    },
    {
      title: '文件路径',
      dataIndex: 'file_path',
      key: 'file_path',
      ellipsis: true,
      width: 150,
    },
    {
      title: '行号',
      key: 'line_range',
      width: 90,
      render: (_: unknown, record: any) => {
        if (record.line_start && record.line_end) {
          return `${record.line_start}-${record.line_end}`;
        } else if (record.line_start) {
          return record.line_start;
        }
        return '-';
      }
    },
    {
      title: '创建人',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 100,
    },
    {
      title: '指派人',
      dataIndex: 'assignee_name',
      key: 'assignee_name',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        let color = 'default';
        let text = '未知';
        
        switch (status) {
          case 'pending':
            color = 'processing';
            text = '审查中';
            break;
          case 'completed':
            color = 'success';
            text = '已完成';
            break;
          case 'rejected':
            color = 'error';
            text = '已拒绝';
            break;
          case 'open':
            color = 'processing';
            text = '开放中';
            break;
          case 'in_progress':
            color = 'processing';
            text = '处理中';
            break;
          case 'resolved':
            color = 'success';
            text = '已解决';
            break;
          case 'closed':
            color = 'default';
            text = '已关闭';
            break;
        }
        
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 150,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '解决时间',
      dataIndex: 'resolved_at',
      key: 'resolved_at',
      width: 150,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 120,
      render: (_: unknown, record: CodeReview) => (
        <Space size="middle">
          <Button type="link" onClick={() => navigate(`/code-review/${record.id}`)}>
            查看
          </Button>
          <Permission roles={['admin', 'reviewer']}>
            <Button type="link" onClick={() => console.log('编辑', record.id)}>
              编辑
            </Button>
          </Permission>
        </Space>
      ),
    },
  ];
  
  return (
    <div>
      <PageHeader title="代码审查" />
      
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Space size="large">
            <Input
              placeholder="搜索审查"
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              onPressEnter={(e) => handleSearch((e.target as HTMLInputElement).value)}
            />
            <Select defaultValue="all" style={{ width: 120 }} onChange={handleStatusChange}>
              <Option value="all">全部状态</Option>
              <Option value="open">未解决</Option>
              <Option value="in_progress">处理中</Option>
              <Option value="resolved">已解决</Option>
              <Option value="closed">已关闭</Option>
            </Select>
            <RangePicker 
              placeholder={['开始日期', '结束日期']} 
              onChange={handleDateRangeChange}
            />
          </Space>
          
          <Permission roles={['admin', 'reviewer']}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => console.log('新建审查')}>
              新建审查
            </Button>
          </Permission>
        </div>
      </Card>
      
      <Card>
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1500 }}  // 添加水平滚动支持
          pagination={{
            total: total,
            current: searchParams.page,
            pageSize: searchParams.pageSize,
            onChange: handlePageChange,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  );
};

export default CodeReviewPage; 