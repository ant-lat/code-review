import React, { useState, useEffect } from 'react';
import { List, Typography, Tag, Timeline, Spin, Empty, message } from 'antd';
import { ClockCircleOutlined, UserOutlined, EditOutlined, CommentOutlined, TagOutlined } from '@ant-design/icons';
import moment from 'moment';
import { getIssueHistory } from '../../../api/issues';

const { Text } = Typography;

interface IssueHistoryProps {
  issueId: number;
}

interface HistoryItem {
  id: number;
  issue_id: number;
  user_id: number;
  username: string;
  field: string;
  old_value: string;
  new_value: string;
  created_at: string;
}

const IssueHistoryList: React.FC<IssueHistoryProps> = ({ issueId }) => {
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await getIssueHistory(issueId);
      setHistory(response.data || []);
    } catch (error) {
      message.error('获取问题历史记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (issueId) {
      fetchHistory();
    }
  }, [issueId]);

  // 获取字段中文名称
  const getFieldName = (field: string): string => {
    const fieldMap: Record<string, string> = {
      'title': '标题',
      'description': '描述',
      'status': '状态',
      'priority': '优先级',
      'assignee_id': '负责人',
      'issue_type': '问题类型',
      'tags': '标签'
    };
    return fieldMap[field] || field;
  };

  // 获取状态颜色
  const getStatusColor = (status: string): string => {
    const statusMap: Record<string, string> = {
      'open': 'blue',
      'in_progress': 'gold',
      'resolved': 'green',
      'closed': 'green',
      'reopened': 'volcano'
    };
    return statusMap[status] || 'default';
  };

  // 获取优先级颜色
  const getPriorityColor = (priority: string): string => {
    const priorityMap: Record<string, string> = {
      'low': 'gray',
      'medium': 'blue',
      'high': 'orange',
      'critical': 'red'
    };
    return priorityMap[priority] || 'default';
  };

  // 根据字段类型格式化显示值
  const formatValue = (field: string, value: string): React.ReactNode => {
    if (!value && value !== '0') return <Text type="secondary">无</Text>;
    
    switch (field) {
      case 'status':
        return <Tag color={getStatusColor(value)}>{value}</Tag>;
      case 'priority':
        return <Tag color={getPriorityColor(value)}>{value}</Tag>;
      case 'tags':
        try {
          const tags = JSON.parse(value);
          return (
            <>
              {tags.map((tag: string, index: number) => (
                <Tag key={index}>{tag}</Tag>
              ))}
            </>
          );
        } catch {
          return value;
        }
      default:
        return value;
    }
  };

  // 获取历史项的图标
  const getHistoryIcon = (field: string) => {
    switch (field) {
      case 'status':
        return <ClockCircleOutlined />;
      case 'assignee_id':
        return <UserOutlined />;
      case 'title':
      case 'description':
        return <EditOutlined />;
      case 'tags':
        return <TagOutlined />;
      default:
        return <CommentOutlined />;
    }
  };

  if (loading) return <Spin size="large" />;
  if (history.length === 0) return <Empty description="暂无历史记录" />;

  return (
    <div className="issue-history">
      <Timeline>
        {history.map((item) => (
          <Timeline.Item key={item.id} dot={getHistoryIcon(item.field)}>
            <div className="history-item">
              <div>
                <Text strong>{item.username}</Text>
                <Text> 修改了 </Text>
                <Text strong>{getFieldName(item.field)}</Text>
              </div>
              
              <div style={{ margin: '8px 0' }}>
                <div style={{ display: 'flex', marginBottom: 8 }}>
                  <div style={{ width: 80 }}>旧值:</div>
                  <div>{formatValue(item.field, item.old_value)}</div>
                </div>
                <div style={{ display: 'flex' }}>
                  <div style={{ width: 80 }}>新值:</div>
                  <div>{formatValue(item.field, item.new_value)}</div>
                </div>
              </div>
              
              <Text type="secondary">
                {moment(item.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Text>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    </div>
  );
};

export default IssueHistoryList; 