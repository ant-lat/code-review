import React from 'react';
import { Tabs, Card } from 'antd';
import PageHeader from '../../components/PageHeader';
import PasswordChange from './PasswordChange';

const { TabPane } = Tabs;

const SettingsPage: React.FC = () => {
  return (
    <div>
      <PageHeader title="系统设置" />
      
      <Card>
        <Tabs defaultActiveKey="security">
          <TabPane tab="基本设置" key="general">
            <div style={{ padding: '20px' }}>
              <h3>基本设置</h3>
              <p>系统基本设置内容，尚未实现。</p>
            </div>
          </TabPane>
          <TabPane tab="安全设置" key="security">
            <div style={{ padding: '20px' }}>
              <PasswordChange />
            </div>
          </TabPane>
          <TabPane tab="权限管理" key="permissions">
            <div style={{ padding: '20px' }}>
              <h3>权限管理</h3>
              <p>系统权限管理内容，尚未实现。</p>
            </div>
          </TabPane>
          <TabPane tab="集成设置" key="integrations">
            <div style={{ padding: '20px' }}>
              <h3>集成设置</h3>
              <p>第三方系统集成设置，尚未实现。</p>
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SettingsPage; 