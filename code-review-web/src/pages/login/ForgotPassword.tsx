import React, { useState } from 'react';
import { Form, Input, Button, message, Card, Steps, Alert } from 'antd';
import { UserOutlined, LockOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { requestPasswordReset, verifyInfo, resetPassword } from '../../api/auth';
import './index.less';

const { Step } = Steps;

const ForgotPassword: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');
  const [verificationType, setVerificationType] = useState('');
  const [verificationQuestion, setVerificationQuestion] = useState('');
  const [verificationAnswer, setVerificationAnswer] = useState('');
  const [form] = Form.useForm();
  const navigate = useNavigate();

  // 步骤1: 获取验证问题
  const handleGetQuestion = async (values: { user_id: string }) => {
    setLoading(true);
    setError('');
    try {
      const response = await requestPasswordReset({
        user_id: values.user_id
      });

      if (response.code === 200) {
        message.success('已获取验证问题');
        setUserId(values.user_id);
        setVerificationType(response.data.verification_type);
        setVerificationQuestion(response.data.question);
        setCurrentStep(1);
      } else {
        setError(response.message || '获取验证问题失败');
      }
    } catch (err: any) {
      setError(err.message || '获取验证问题失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 步骤2: 验证用户信息
  const handleVerifyInfo = async (values: { answer: string }) => {
    setLoading(true);
    setError('');
    try {
      const response = await verifyInfo({
        user_id: userId,
        verification_type: verificationType,
        answer: values.answer
      });

      if (response.code === 200) {
        message.success('验证信息正确');
        setVerificationAnswer(values.answer);
        setCurrentStep(2);
      } else {
        setError(response.message || '验证失败');
      }
    } catch (err: any) {
      setError(err.message || '验证失败，请检查您的答案');
    } finally {
      setLoading(false);
    }
  };

  // 步骤3: 重置密码
  const handleResetPassword = async (values: { new_password: string, confirm_password: string }) => {
    setLoading(true);
    setError('');
    try {
      const response = await resetPassword({
        user_id: userId,
        verification_type: verificationType,
        answer: verificationAnswer,
        new_password: values.new_password,
        confirm_password: values.confirm_password
      });

      if (response.code === 200) {
        message.success('密码重置成功，请使用新密码登录');
        navigate('/login');
      } else {
        setError(response.message || '密码重置失败');
      }
    } catch (err: any) {
      if (err.response && err.response.data) {
        setError(err.response.data.message || err.response.data.detail || '密码重置失败，请稍后重试');
      } else {
        setError(err.message || '密码重置失败，请稍后重试');
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

  const steps = [
    {
      title: '输入用户ID',
      content: (
        <Form form={form} onFinish={handleGetQuestion} layout="vertical">
          <Form.Item
            name="user_id"
            rules={[
              { required: true, message: '请输入用户ID' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户ID"
              size="large"
              autoComplete="username"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              下一步
            </Button>
          </Form.Item>
        </Form>
      )
    },
    {
      title: '验证身份',
      content: (
        <Form form={form} onFinish={handleVerifyInfo} layout="vertical">
          <div className="verification-question">
            <QuestionCircleOutlined /> {verificationQuestion}
          </div>
          <Form.Item
            name="answer"
            rules={[
              { required: true, message: '请输入您的答案' }
            ]}
          >
            <Input
              placeholder="请输入您的答案"
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              验证
            </Button>
          </Form.Item>
        </Form>
      )
    },
    {
      title: '重置密码',
      content: (
        <Form form={form} onFinish={handleResetPassword} layout="vertical">
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
              placeholder="新密码"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="confirm_password"
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
              placeholder="确认新密码"
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              重置密码
            </Button>
          </Form.Item>
        </Form>
      )
    }
  ];

  return (
    <div className="forgot-password-container">
      <Card className="forgot-password-card">
        <h2 className="card-title">忘记密码</h2>
        
        <Steps current={currentStep} className="steps-container">
          {steps.map(item => (
            <Step key={item.title} title={item.title} />
          ))}
        </Steps>
        
        {error && (
          <Alert 
            message="错误" 
            description={error} 
            type="error" 
            showIcon 
            closable 
            onClose={() => setError('')}
            style={{ marginBottom: 16, marginTop: 16 }}
          />
        )}
        
        <div className="steps-content">
          {steps[currentStep].content}
        </div>
        
        <div className="login-link-container">
          <Link to="/login">返回登录</Link>
        </div>
      </Card>
    </div>
  );
};

export default ForgotPassword; 