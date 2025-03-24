import React, { useState } from 'react';
import { Card, Form, Input, Button, Alert, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { changePassword } from '../../api/users';

const PasswordChange: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const handleSubmit = async (values: {
    old_password: string;
    new_password: string;
    confirm_password: string;
  }) => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    try {
      const result = await changePassword({
        current_password: values.old_password,
        new_password: values.new_password,
        confirm_password: values.confirm_password
      });
      
      if (result.code === 200) {
        setSuccess(true);
        form.resetFields();
        message.success('密码修改成功');
      } else {
        setError(result.message || '密码修改失败，请稍后重试');
      }
    } catch (err: any) {
      // 处理响应中的详细错误信息
      if (err.response && err.response.data) {
        setError(err.response.data.message || err.response.data.detail || '密码修改失败，请稍后重试');
      } else {
        setError(err.message || '密码修改失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };
  
  // 密码强度校验
  const validatePasswordStrength = (_: any, value: string) => {
    if (!value) {
      return Promise.reject(new Error('请输入新密码'));
    }
    
    const hasUpper = /[A-Z]/.test(value);
    const hasLower = /[a-z]/.test(value);
    const hasNumber = /\d/.test(value);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(value);
    const isLongEnough = value.length >= 8;
    
    if (!isLongEnough) {
      return Promise.reject(new Error('密码长度需要至少8位'));
    }
    
    if (!hasUpper) {
      return Promise.reject(new Error('密码必须包含大写字母'));
    }
    
    if (!hasLower) {
      return Promise.reject(new Error('密码必须包含小写字母'));
    }
    
    if (!hasNumber) {
      return Promise.reject(new Error('密码必须包含数字'));
    }
    
    if (!hasSpecial) {
      return Promise.reject(new Error('密码必须包含至少一个特殊字符'));
    }
    
    return Promise.resolve();
  };
  
  return (
    <Card title="修改密码" style={{ maxWidth: 600, margin: '0 auto' }}>
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setError(null)}
        />
      )}
      
      {success && (
        <Alert
          message="密码修改成功"
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setSuccess(false)}
        />
      )}
      
      <Alert
        message="密码规则"
        description="密码必须满足以下条件：
          • 长度至少8位
          • 至少包含一个大写字母
          • 至少包含一个小写字母
          • 至少包含一个数字
          • 至少包含一个特殊字符（如!@#$%^&*）"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          name="old_password"
          label="当前密码"
          rules={[{ required: true, message: '请输入当前密码' }]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入当前密码"
          />
        </Form.Item>
        
        <Form.Item
          name="new_password"
          label="新密码"
          rules={[
            { required: true, message: '请输入新密码' },
            { validator: validatePasswordStrength }
          ]}
          extra="请确保密码包含大写字母、小写字母、数字和特殊字符，长度至少8位"
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请输入新密码"
          />
        </Form.Item>
        
        <Form.Item
          name="confirm_password"
          label="确认新密码"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请确认新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="请确认新密码"
          />
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            修改密码
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default PasswordChange; 