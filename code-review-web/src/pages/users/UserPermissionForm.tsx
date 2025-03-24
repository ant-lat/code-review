import React, { useEffect, useState } from 'react';
import { Form, Checkbox, Button, message, Spin, Tabs, Card, Tree, Space } from 'antd';
import { useDispatch, useSelector } from 'react-redux';
import { fetchUserById } from '../../store/slices/userSlice';
import { fetchPermissionGroups, fetchPermissions } from '../../store/slices/roleSlice';
import type { Permission } from '../../api/types';
import { assignUserPermissions, getUserPermissions } from '../../api/users';

const { TabPane } = Tabs;
const { DirectoryTree } = Tree;

interface UserPermissionFormProps {
  userId: number;
  onSuccess?: () => void;
}

interface TreePermission {
  title: string;
  key: string;
  children?: TreePermission[];
}

const UserPermissionForm: React.FC<UserPermissionFormProps> = ({ userId, onSuccess }) => {
  const dispatch = useDispatch();
  const { permissionGroups, loading: roleLoading } = useSelector((state: AppState) => state.role);
  const { users } = useSelector((state: AppState) => state.user);
  
  const [userPermissions, setUserPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('1');
  const [form] = Form.useForm();

  // 获取用户和权限信息
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // 获取用户详情
        dispatch(fetchUserById(userId) as any);
        
        // 获取权限分组
        dispatch(fetchPermissionGroups() as any);
        
        // 获取用户权限
        const res = await getUserPermissions(userId);
        setUserPermissions(res.data.map((p: Permission) => p.code));
      } catch (error) {
        message.error('获取用户权限信息失败');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [dispatch, userId]);
  
  // 获取用户名
  const user = users.find((u: {id: number, username: string}) => u.id === userId);
  const username = user ? user.username : '加载中...';
  
  // 将权限数据转换为树形结构
  const generatePermissionTree = (): TreePermission[] => {
    return permissionGroups.map((group: {group: string, permissions: Array<{name: string, code: string}>}) => ({
      title: group.group,
      key: `group-${group.group}`,
      children: group.permissions.map((permission: {name: string, code: string}) => ({
        title: permission.name,
        key: permission.code,
      }))
    }));
  };
  
  // 处理表单提交
  const handleSubmit = async (values: { permissions: string[] }) => {
    setSubmitting(true);
    try {
      // 查找选中的权限ID列表
      const permissionIds: number[] = [];
      
      for (const code of values.permissions) {
        for (const group of permissionGroups) {
          const permission = group.permissions.find((p: {code: string, id: number}) => p.code === code);
          if (permission) {
            permissionIds.push(permission.id);
            break;
          }
        }
      }
      
      await assignUserPermissions(userId, {
        permission_ids: permissionIds
      });
      
      message.success('用户权限已更新');
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      message.error('更新用户权限失败');
      console.error('更新权限失败:', error);
    } finally {
      setSubmitting(false);
    }
  };
  
  // 处理树选择变化
  const handleTreeCheck = (checkedKeys: any) => {
    const checkedPermissions = checkedKeys.filter((key: string) => !key.startsWith('group-'));
    form.setFieldsValue({ permissions: checkedPermissions });
  };
  
  // 计算树选中的键
  const getCheckedKeys = () => {
    const permissions = form.getFieldValue('permissions') || userPermissions;
    // 添加组节点，如果组内所有权限都被选中
    const groupKeys: string[] = [];
    
    permissionGroups.forEach((group: {group: string, permissions: Array<{code: string}>}) => {
      const groupPermCodes = group.permissions.map((p: {code: string}) => p.code);
      const isAllChecked = groupPermCodes.every((code: string) => permissions.includes(code));
      if (isAllChecked && groupPermCodes.length > 0) {
        groupKeys.push(`group-${group.group}`);
      }
    });
    
    return [...permissions, ...groupKeys];
  };
  
  // 初始化表单值
  useEffect(() => {
    if (userPermissions.length > 0) {
      form.setFieldsValue({ permissions: userPermissions });
    }
  }, [form, userPermissions]);
  
  if (loading || roleLoading) {
    return <Spin tip="加载中..." />;
  }
  
  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{ permissions: userPermissions }}
    >
      <div style={{ marginBottom: 16 }}>
        <h3>用户: {username}</h3>
        <p>您可以为此用户分配特定权限，覆盖其角色默认权限。</p>
      </div>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="树形视图" key="1">
          <Card style={{ marginBottom: 16 }}>
            <DirectoryTree
              checkable
              checkedKeys={getCheckedKeys()}
              onCheck={handleTreeCheck}
              treeData={generatePermissionTree()}
              defaultExpandAll
            />
          </Card>
        </TabPane>
        <TabPane tab="列表视图" key="2">
          <Form.Item name="permissions" valuePropName="value">
            <Checkbox.Group style={{ width: '100%' }}>
              {permissionGroups.map((group: {group: string, permissions: Array<{code: string, name: string}>}) => (
                <Card title={group.group} key={group.group} style={{ marginBottom: 16 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {group.permissions.map((permission: {code: string, name: string}) => (
                      <Checkbox
                        key={permission.code}
                        value={permission.code}
                      >
                        {permission.name} <small>({permission.code})</small>
                      </Checkbox>
                    ))}
                  </Space>
                </Card>
              ))}
            </Checkbox.Group>
          </Form.Item>
        </TabPane>
      </Tabs>
      
      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={submitting}>
            保存权限
          </Button>
          <Button onClick={onSuccess}>取消</Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default UserPermissionForm; 