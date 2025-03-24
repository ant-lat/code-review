import React from 'react';
import { Typography, Button, Space, Divider, Breadcrumb } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

interface PageHeaderProps {
  title: React.ReactNode;
  subTitle?: string;
  backPath?: string;
  extra?: React.ReactNode;
  breadcrumb?: { title: string; path?: string }[];
}

const PageHeader: React.FC<PageHeaderProps> = ({ 
  title, 
  subTitle, 
  backPath, 
  extra,
  breadcrumb 
}) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (backPath) {
      navigate(backPath);
    } else {
      navigate(-1);
    }
  };

  return (
    <div className="custom-page-header" style={{ marginBottom: 24 }}>
      {breadcrumb && breadcrumb.length > 0 && (
        <Breadcrumb style={{ marginBottom: 16 }}>
          {breadcrumb.map((item, index) => (
            <Breadcrumb.Item key={index}>
              {item.path ? (
                <a onClick={() => item.path && navigate(item.path)}>{item.title}</a>
              ) : (
                item.title
              )}
            </Breadcrumb.Item>
          ))}
        </Breadcrumb>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          {(backPath || backPath === '') && (
            <Button 
              type="text" 
              icon={<ArrowLeftOutlined />} 
              onClick={handleBack}
              style={{ marginRight: 8 }}
            />
          )}
          {typeof title === 'string' ? (
            <Title level={4} style={{ margin: 0 }}>{title}</Title>
          ) : (
            title
          )}
          {subTitle && (
            <Typography.Text type="secondary">{subTitle}</Typography.Text>
          )}
        </Space>
        {extra && <Space>{extra}</Space>}
      </div>
      <Divider style={{ margin: '0 0 16px 0' }} />
    </div>
  );
};

export default PageHeader; 