import React, { useState } from 'react';
import { Card, Table, Modal, Button, Space, Select, RangePicker, Tooltip, Tag, Title } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import moment from 'moment';
import IssueForm from './IssueForm';

const { Option } = Select;

const IssueList: React.FC = () => {
  const [dataSource, setDataSource] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 });
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentIssue, setCurrentIssue] = useState(null);
  const [filters, setFilters] = useState({
    projectId: '',
    status: '',
    type: '',
    priority: '',
    assigneeId: '',
    creatorId: '',
    startTime: '',
    endTime: '',
  });
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [statusOptions, setStatusOptions] = useState([]);
  const [typeOptions, setTypeOptions] = useState([]);
  const [priorityOptions, setPriorityOptions] = useState([]);

  const handleTableChange = (newPagination) => {
    setPagination(newPagination);
    fetchData();
  };

  const handleSearch = () => {
    setPagination({ current: 1, pageSize: 10 });
    fetchData();
  };

  const handleReset = () => {
    setFilters({
      projectId: '',
      status: '',
      type: '',
      priority: '',
      assigneeId: '',
      creatorId: '',
      startTime: '',
      endTime: '',
    });
    setPagination({ current: 1, pageSize: 10 });
    fetchData();
  };

  const handleDateRangeChange = (dates) => {
    if (dates && dates.length === 2) {
      setFilters({
        ...filters,
        startTime: dates[0].format('YYYY-MM-DD'),
        endTime: dates[1].format('YYYY-MM-DD'),
      });
    } else {
      setFilters({
        ...filters,
        startTime: '',
        endTime: '',
      });
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters({
      ...filters,
      [field]: value,
    });
  };

  const handleCreateIssue = (issue) => {
    // Implementation of handleCreateIssue
  };

  const handleUpdateIssue = (issue) => {
    // Implementation of handleUpdateIssue
  };

  const confirmDelete = (record) => {
    // Implementation of confirmDelete
  };

  const fetchData = () => {
    // Implementation of fetchData
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      width: '20%',
      render: (text, record) => (
        <Tooltip title={text}>
          <a
            onClick={() => {
              setCurrentIssue(record);
              setEditModalVisible(true);
            }}
            className="issue-title-link"
          >
            {text}
          </a>
        </Tooltip>
      ),
    },
    {
      title: '项目',
      dataIndex: 'projectName',
      key: 'projectName',
      width: '14%',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Tag color="processing" className="project-tag">
            {text}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: '10%',
      render: (status) => {
        const statusInfo = getStatusInfo(status);
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
      },
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: '10%',
      render: (type) => {
        const typeInfo = getTypeInfo(type);
        return (
          <Tag color={typeInfo.color} icon={typeInfo.icon}>
            {typeInfo.text}
          </Tag>
        );
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: '10%',
      render: (priority) => {
        const priorityInfo = getPriorityInfo(priority);
        return (
          <Tag color={priorityInfo.color} icon={priorityInfo.icon}>
            {priorityInfo.text}
          </Tag>
        );
      },
    },
    {
      title: '创建者',
      dataIndex: 'creatorName',
      key: 'creatorName',
      width: '10%',
      render: (text) => <span className="creator-name">{text}</span>,
    },
    {
      title: '经办人',
      dataIndex: 'assigneeName',
      key: 'assigneeName',
      width: '10%',
      render: (text) => (
        <span className="assignee-name">
          {text || <span className="no-assignee">未分配</span>}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      key: 'createTime',
      width: '12%',
      render: (text) => <span className="create-time">{formatDate(text)}</span>,
    },
    {
      title: '操作',
      key: 'action',
      width: '8%',
      render: (_, record) => (
        <Space size="middle" className="action-buttons">
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setCurrentIssue(record);
                setEditModalVisible(true);
              }}
              className="edit-button"
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              icon={<DeleteOutlined />}
              onClick={() => confirmDelete(record)}
              className="delete-button"
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="issue-list-container">
      <Card bordered={false} className="issue-list-card">
        <div className="issue-list-header">
          <div className="issue-list-title">
            <Title level={4}>问题列表</Title>
            <span className="issue-count">共 {totalCount} 个问题</span>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
            className="create-issue-button"
          >
            创建问题
          </Button>
        </div>

        <div className="issue-list-filter">
          <div className="filter-row">
            <div className="filter-item">
              <span className="filter-label">项目：</span>
              <Select
                placeholder="选择项目"
                style={{ width: 180 }}
                allowClear
                value={filters.projectId}
                onChange={(value) => handleFilterChange('projectId', value)}
                className="project-filter"
              >
                {projects.map((project) => (
                  <Option key={project.id} value={project.id}>
                    {project.name}
                  </Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <span className="filter-label">状态：</span>
              <Select
                placeholder="选择状态"
                style={{ width: 140 }}
                allowClear
                value={filters.status}
                onChange={(value) => handleFilterChange('status', value)}
                className="status-filter"
              >
                {statusOptions.map((option) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <span className="filter-label">类型：</span>
              <Select
                placeholder="选择类型"
                style={{ width: 140 }}
                allowClear
                value={filters.type}
                onChange={(value) => handleFilterChange('type', value)}
                className="type-filter"
              >
                {typeOptions.map((option) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <span className="filter-label">优先级：</span>
              <Select
                placeholder="选择优先级"
                style={{ width: 140 }}
                allowClear
                value={filters.priority}
                onChange={(value) => handleFilterChange('priority', value)}
                className="priority-filter"
              >
                {priorityOptions.map((option) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </div>
          </div>
          <div className="filter-row">
            <div className="filter-item">
              <span className="filter-label">经办人：</span>
              <Select
                placeholder="选择经办人"
                style={{ width: 160 }}
                allowClear
                value={filters.assigneeId}
                onChange={(value) => handleFilterChange('assigneeId', value)}
                className="assignee-filter"
              >
                {users.map((user) => (
                  <Option key={user.id} value={user.id}>
                    {user.name}
                  </Option>
                ))}
              </Select>
            </div>
            <div className="filter-item">
              <span className="filter-label">创建者：</span>
              <Select
                placeholder="选择创建者"
                style={{ width: 160 }}
                allowClear
                value={filters.creatorId}
                onChange={(value) => handleFilterChange('creatorId', value)}
                className="creator-filter"
              >
                {users.map((user) => (
                  <Option key={user.id} value={user.id}>
                    {user.name}
                  </Option>
                ))}
              </Select>
            </div>
            <div className="filter-item date-filter">
              <span className="filter-label">创建时间：</span>
              <RangePicker
                value={
                  filters.startTime && filters.endTime
                    ? [moment(filters.startTime), moment(filters.endTime)]
                    : null
                }
                onChange={handleDateRangeChange}
                className="date-range-picker"
              />
            </div>
            <div className="filter-actions">
              <Button
                type="primary"
                onClick={handleSearch}
                icon={<SearchOutlined />}
                className="search-button"
              >
                搜索
              </Button>
              <Button
                onClick={handleReset}
                icon={<ReloadOutlined />}
                className="reset-button"
              >
                重置
              </Button>
            </div>
          </div>
        </div>

        <Table
          columns={columns}
          dataSource={dataSource}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: totalCount,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: handleTableChange,
            onShowSizeChange: handleTableChange,
          }}
          onChange={handleTableChange}
          className="issue-table"
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title="创建问题"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
        className="issue-modal"
      >
        <IssueForm
          projects={projects}
          users={users}
          onFinish={handleCreateIssue}
          onCancel={() => setCreateModalVisible(false)}
        />
      </Modal>

      <Modal
        title="编辑问题"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
        className="issue-modal"
      >
        {currentIssue && (
          <IssueForm
            initialValues={currentIssue}
            projects={projects}
            users={users}
            onFinish={handleUpdateIssue}
            onCancel={() => setEditModalVisible(false)}
          />
        )}
      </Modal>
    </div>
  );
};

export default IssueList; 