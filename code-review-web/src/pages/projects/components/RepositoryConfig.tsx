import React, { useState } from 'react';
import { Form, Input, Select, Button, Space, message } from 'antd';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';

// 创建Repository接口
interface Repository {
  id?: number;
  url: string;
  type: 'git' | 'svn';
  branch: string;
  credentials?: {
    username?: string;
    password?: string;
    key?: string;
  };
}

interface RepositoryConfigProps {
  projectId: number;
  onSubmit: (repositories: Repository[]) => void;
}

const RepositoryConfig: React.FC<RepositoryConfigProps> = ({ projectId, onSubmit }) => {
  const [form] = Form.useForm();

  const handleSubmit = (values: { repositories: Repository[] }) => {
    onSubmit(values.repositories);
  };

  return (
    <Form form={form} onFinish={handleSubmit} layout="vertical">
      <Form.List name="repositories">
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, ...restField }) => (
              <div key={key} style={{ marginBottom: 16 }}>
                <Space align="baseline" style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Form.Item
                    {...restField}
                    name={[name, 'repo_type']}
                    label="仓库类型"
                    rules={[{ required: true, message: '请选择仓库类型' }]}
                    style={{ width: '120px' }}
                  >
                    <Select>
                      <Select.Option value="git">Git</Select.Option>
                      <Select.Option value="svn">SVN</Select.Option>
                    </Select>
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'url']}
                    label="仓库地址"
                    rules={[{ required: true, message: '请输入仓库地址' }]}
                    style={{ width: '300px' }}
                  >
                    <Input placeholder="请输入仓库地址" />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'branch']}
                    label="分支"
                    style={{ width: '120px' }}
                  >
                    <Input placeholder="可选" />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'commit_hash']}
                    label="提交哈希"
                    style={{ width: '120px' }}
                  >
                    <Input placeholder="可选" />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'tag']}
                    label="标签"
                    style={{ width: '120px' }}
                  >
                    <Input placeholder="可选" />
                  </Form.Item>

                  <MinusCircleOutlined onClick={() => remove(name)} style={{ marginTop: 32 }} />
                </Space>
              </div>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                添加仓库
              </Button>
            </Form.Item>
          </>
        )}
      </Form.List>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          保存配置
        </Button>
      </Form.Item>
    </Form>
  );
};

export default RepositoryConfig; 