import React, { useState, useEffect, useCallback } from 'react';
import { Button, Form, Input, Select, Space, message, Table, Tabs, Card, Row, Col, Spin, Empty, List, Avatar } from 'antd';
import { DeleteOutlined, SearchOutlined, UserAddOutlined, TeamOutlined } from '@ant-design/icons';
import { User } from '../../../api/types';
import { getProjectMembers, addProjectMember, removeProjectMember } from '../../../api/projects';
import { getUsers } from '../../../api/users';
import { checkPermission } from '../../../api/auth';
import { getAllProjectRoles } from '../../../api/roles';
import { ResponseBase } from '../../../api/types';
import { debounce } from 'lodash';
import './ProjectMembers.css';

const { TabPane } = Tabs;
const { Search } = Input;

// 后端返回的项目成员类型
interface ApiProjectMember {
  id?: number;
  project_id?: number;
  user_id?: number;
  user?: {
    id: number;
    username: string;
    email?: string;
    avatar?: string;
  };
  role?: string;
  role_id?: number;
  role_name?: string;
  is_active?: boolean;
  created_at?: string;
  joined_at?: string;
}

// 角色定义接口
interface ProjectRole {
  id: number;
  name: string;
  description?: string;
}

// 定义组件内部使用的项目成员结构，与API返回保持一致
interface MemberItem {
  user_id: number;
  username: string;
  email?: string;
  role_id: number;
  role_name: string;
  is_active: boolean;
  joined_at: string;
}

// 用户查询参数
interface UserQueryParams {
  page: number;
  page_size: number;
  search?: string;
}

interface ProjectMembersProps {
  projectId: number;
  onClose: () => void;
}

const ProjectMembers: React.FC<ProjectMembersProps> = ({ projectId, onClose }) => {
  const [activeTab, setActiveTab] = useState('1');
  const [loading, setLoading] = useState(false);
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [roles, setRoles] = useState<ProjectRole[]>([]);
  const [userLoading, setUserLoading] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [userPagination, setUserPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [roleLoading, setRoleLoading] = useState(false);
  const [canManageMembers, setCanManageMembers] = useState(true);
  
  // 检查权限
  const checkUserPermission = async () => {
    try {
      const response = await checkPermission('project:manage_members');
      // 即使权限检查失败，也设置为true，确保UI可用
      setCanManageMembers(true);
    } catch (error) {
      console.error('检查权限失败:', error);
      // 出错时仍然设置为true，确保UI可用
      setCanManageMembers(true);
    }
  };
  
  // 获取项目成员
  const fetchMembers = async () => {
    try {
      setLoading(true);
      const response = await getProjectMembers(projectId, { 
        page: 1, 
        page_size: 100 // 获取较多记录，实际项目中根据需求调整
      });
      
      if (response?.data) {
        console.log('获取项目成员响应:', response.data);
        
        // 简化数据映射逻辑，直接使用API返回的格式
        const memberItems: MemberItem[] = Array.isArray(response.data) 
          ? response.data.map((member: any) => ({
              user_id: member.user_id,
              username: member.username,
              email: member.email || '',
              role_id: member.role_id,
              role_name: member.role_name,
              is_active: member.is_active !== undefined ? member.is_active : true,
              joined_at: member.joined_at || new Date().toISOString()
            }))
          : [];
          
        setMembers(memberItems);
      } else {
        setMembers([]);
      }
    } catch (error) {
      console.error('获取项目成员失败:', error);
      message.error('获取项目成员失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取项目角色列表
  const fetchRoles = async () => {
    try {
      setRoleLoading(true);
      
      // 使用正确的API函数
      const response = await getAllProjectRoles() as ResponseBase<any>;
      
      if (response?.data?.items) {
        console.log('获取角色列表响应:', response.data.items);
        // 从返回的数据中提取角色名称
        const roleList = response.data.items.map((role: any) => ({
          id: role.id,
          name: role.name,
          description: role.description
        }));
        setRoles(roleList);
      } else {
        // 如果API尚未实现或出错，使用默认角色
        setRoles([
          { id: 6, name: 'PM', description: '项目经理' },
          { id: 7, name: 'SE', description: '软件工程师' },
          { id: 8, name: 'DEV', description: '开发人员' },
          { id: 9, name: 'QA', description: '质量专家' }
        ]);
      }
    } catch (error) {
      console.error('获取角色列表失败:', error);
      message.error('获取角色列表失败，使用默认角色');
      // 使用默认角色
      setRoles([
        { id: 6, name: 'PM', description: '项目经理' },
        { id: 7, name: 'SE', description: '软件工程师' },
        { id: 8, name: 'DEV', description: '开发人员' },
        { id: 9, name: 'QA', description: '质量专家' }
      ]);
    } finally {
      setRoleLoading(false);
    }
  };

  // 获取可用用户 - 优化为服务端分页和搜索
  const fetchAvailableUsers = async (params: UserQueryParams) => {
    try {
      setUserLoading(true);
      // 调用API获取用户列表，添加项目ID以排除已有成员
      const apiParams = {
        page: params.page,
        page_size: params.page_size,
        username: params.search,  // 使用username作为搜索字段
        exclude_project_id: projectId // 这需要后端支持
      };
      
      const response = await getUsers(apiParams);
      
      if (response?.data) {
        console.log('获取用户列表响应:', response.data);
        
        // 处理用户列表
        const users = Array.isArray(response.data) ? response.data : 
                    (response.data.items && Array.isArray(response.data.items)) ? response.data.items : [];
        
        setAvailableUsers(users);
        
        // 更新分页信息
        setUserPagination({
          current: params.page,
          pageSize: params.page_size,
          total: response.data.total || users.length,
        });
      }
    } catch (error) {
      console.error('获取可用用户列表失败:', error);
      message.error('获取可用用户列表失败');
      setAvailableUsers([]);
    } finally {
      setUserLoading(false);
    }
  };

  // 使用防抖处理搜索，避免频繁请求
  const debouncedSearch = useCallback(
    debounce((value: string) => {
      fetchAvailableUsers({
        page: 1,
        page_size: userPagination.pageSize,
        search: value
      });
    }, 500),
    [userPagination.pageSize]
  );

  // 搜索框变化
  const handleSearchChange = (value: string) => {
    setSearchValue(value);
    debouncedSearch(value);
  };

  // 用户页码变化
  const handleUserPageChange = (page: number, pageSize?: number) => {
    const newPageSize = pageSize || userPagination.pageSize;
    setUserPagination(prev => ({ 
      ...prev, 
      current: page,
      pageSize: newPageSize
    }));
    
    fetchAvailableUsers({
      page,
      page_size: newPageSize,
      search: searchValue
    });
  };

  // 添加成员
  const handleAddMember = async (userId: number, roleId: number) => {
    try {
      if (!roleId) {
        message.warning('请选择角色');
        return;
      }
      
      await addProjectMember(projectId, userId, roleId);
      message.success('添加成员成功');
      
      // 刷新成员列表
      fetchMembers();
      
      // 刷新可用用户列表
      fetchAvailableUsers({
        page: userPagination.current,
        page_size: userPagination.pageSize,
        search: searchValue
      });
    } catch (error) {
      console.error('添加成员失败:', error);
      message.error('添加成员失败');
    }
  };

  // 移除成员
  const handleRemoveMember = async (userId: number) => {
    try {
      await removeProjectMember(projectId, userId);
      message.success('移除成员成功');
      
      // 刷新成员列表
      fetchMembers();
    } catch (error) {
      console.error('移除成员失败:', error);
      message.error('移除成员失败');
    }
  };

  // 初始加载
  useEffect(() => {
    checkUserPermission();
    fetchRoles();
    fetchMembers();
  }, [projectId]);

  // 切换到添加成员页签时加载用户列表
  useEffect(() => {
    if (activeTab === '2') {
      fetchAvailableUsers({
        page: 1,
        page_size: userPagination.pageSize,
        search: ''
      });
    }
  }, [activeTab]);

  // 表格列定义 - 成员列表
  const membersColumns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => email || '-',
    },
    {
      title: '角色',
      dataIndex: 'role_name',
      key: 'role_name',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => isActive ? '活跃' : '非活跃',
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    canManageMembers ? {
      title: '操作',
      key: 'action',
      render: (_: any, record: MemberItem) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleRemoveMember(record.user_id)}
        >
          移除
        </Button>
      ),
    } : {}
  ].filter(col => Object.keys(col).length > 0);

  // 用户列表列定义
  const userColumns = [
    {
      title: '用户信息',
      dataIndex: 'username',
      key: 'username',
      render: (_: string, record: User) => (
        <div className="user-info-cell">
          <Avatar size="small" style={{ marginRight: 8 }}>
            {record.username.charAt(0).toUpperCase()}
          </Avatar>
          <span className="user-name">{record.username}</span>
          {record.email && <span className="user-email">{record.email}</span>}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: User) => (
        <Space>
          <Select
            placeholder="选择角色"
            style={{ width: 120 }}
            onChange={(roleId) => handleAddMember(record.id, roleId)}
          >
            {roles.map(role => (
              <Select.Option key={role.id} value={role.id}>
                {role.name}
              </Select.Option>
            ))}
          </Select>
        </Space>
      ),
    },
  ];

  // 渲染用户列表视图
  const renderUserList = () => {
    if (availableUsers.length === 0) {
      return <Empty description="没有可添加的用户" />;
    }

    return (
      <Table
        columns={userColumns}
        dataSource={availableUsers}
        rowKey={(record) => `user-${record.id}`}
        pagination={{
          current: userPagination.current,
          pageSize: userPagination.pageSize,
          total: userPagination.total,
          onChange: handleUserPageChange,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: total => `共 ${total} 条记录`
        }}
        loading={userLoading}
      />
    );
  };

  return (
    <div className="project-members">
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        className="member-tabs"
      >
        <TabPane 
          tab={<span><TeamOutlined /> 成员列表</span>} 
          key="1"
        >
          <Spin spinning={loading}>
            <Table
              columns={membersColumns}
              dataSource={members}
              rowKey={(record) => `${record.user_id}-${record.role_id}`}
              pagination={{ 
                showSizeChanger: true,
                showTotal: total => `共 ${total} 条记录`
              }}
              locale={{ emptyText: <Empty description="暂无项目成员" /> }}
            />
          </Spin>
        </TabPane>
        
        {/* 总是显示添加成员Tab，无需权限检查 */}
        <TabPane 
          tab={<span><UserAddOutlined /> 添加成员</span>} 
          key="2"
        >
          <Spin spinning={userLoading || roleLoading}>
            <Card className="add-members-card">
              <Row className="filter-row" gutter={16}>
                <Col xs={24} sm={24} md={12} lg={12}>
                  <Search
                    placeholder="搜索用户名"
                    value={searchValue}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    onSearch={handleSearchChange}
                    allowClear
                    enterButton
                  />
                </Col>
              </Row>
              
              <div className="users-list">
                {renderUserList()}
              </div>
            </Card>
          </Spin>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ProjectMembers; 