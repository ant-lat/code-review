import React, { useState, useEffect } from 'react';
import { Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { login, getCurrentUser } from '../../api/auth';
import { isLoggedIn } from '../../utils/auth';
import ThemeSwitcher, { LoginTheme } from './ThemeSwitcher';
import './index.less';

/**
 * 登录页面组件
 */
const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [form] = Form.useForm();
  const [theme, setTheme] = useState<LoginTheme>('gradient');
  const [mounted, setMounted] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('loginTheme') as LoginTheme;
    if (savedTheme) {
      setTheme(savedTheme);
    }
    
    // 如果已经登录，跳转到首页
    if (isLoggedIn()) {
      navigate('/dashboard');
    }
    
    // 添加启动动画
    const timer = setTimeout(() => {
      const loginCard = document.querySelector('.login-card');
      if (loginCard) {
        loginCard.classList.add('login-card-visible');
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [navigate]);

  // 主题切换处理
  const handleThemeChange = (newTheme: LoginTheme) => {
    setTheme(newTheme);
    localStorage.setItem('loginTheme', newTheme);
  };

  // 表单提交处理
  const onFinish = async (values: any) => {
    setLoading(true);
    setLoginError('');
    try {
      const result = await login({
        user_id: values.user_id,
        password: values.password,
      });
      
      if (result && result.code === 200) {
        // 显示成功消息和登录动画
        message.success({
          content: '登录成功，欢迎回来！',
          duration: 2
        });
        
        // 存储token
        const tokenData = result.data;
        localStorage.setItem('token', tokenData.access_token);
        localStorage.setItem('token_type', tokenData.token_type);
        localStorage.setItem('expires_in', tokenData.expires_in.toString());
        
        // 如果后端返回了refresh_token，也存储它
        if (tokenData.refresh_token) {
          localStorage.setItem('refresh_token', tokenData.refresh_token);
        }
        
        // 获取用户信息
        const userInfo = await getCurrentUser();
        if (userInfo && userInfo.code === 200) {
          // 存储用户信息
          localStorage.setItem('user', JSON.stringify(userInfo.data));
          
          // 添加登录成功动画
          const loginCard = document.querySelector('.login-card');
          if (loginCard) {
            loginCard.classList.add('login-success');
          }
          
          // 延迟导航以显示动画
          setTimeout(() => {
            // 确保跳转到dashboard
            navigate('/dashboard', { replace: true });
          }, 800);
        } else {
          setLoginError('获取用户信息失败，请重试');
        }
      } else {
        setLoginError(result?.message || '登录失败，请检查用户名和密码');
        form.setFields([
          {
            name: 'password',
            errors: ['密码错误']
          }
        ]);
      }
    } catch (error) {
      console.error('登录失败:', error);
      setLoginError('登录过程中出现错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理忘记密码点击事件
  const handleForgotPassword = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate('/forgot-password');
  };

  return (
    <div className={`login-container ${theme}-theme ${mounted ? 'mounted' : ''}`}>
      <div className="login-content">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">
              <svg viewBox="0 0 24 24" className="logo-icon">
                <defs>
                  <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#1d4ed8" />
                  </linearGradient>
                </defs>
                <rect x="2" y="2" width="20" height="20" rx="4" fill="url(#logoGradient)" />
                <path 
                  d="M16.5 8.5l-4.5 3-4.5-3M16.5 12l-4.5 3-4.5-3M16.5 15.5l-4.5 3-4.5-3" 
                  fill="none" 
                  stroke="white" 
                  strokeWidth="1.5" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h1 className="login-title">代码审查平台</h1>
            <p className="login-subtitle">安全可靠的代码分析与审查工具</p>
          </div>

          <Form
            form={form}
            name="login_form"
            className="login-form"
            initialValues={{ remember: true }}
            onFinish={onFinish}
          >
            <Form.Item
              name="user_id"
              rules={[{ required: true, message: '请输入用户名' }]}
              validateTrigger="onBlur"
            >
              <Input 
                prefix={<UserOutlined className="site-form-item-icon" />} 
                placeholder="用户名" 
                size="large"
                autoComplete="username"
                className="login-input"
              />
            </Form.Item>
            
            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
              validateTrigger="onBlur"
            >
              <Input.Password
                prefix={<LockOutlined className="site-form-item-icon" />}
                type="password"
                placeholder="密码"
                size="large"
                autoComplete="current-password"
                className="login-input"
              />
            </Form.Item>
            
            {loginError && (
              <div className="login-error shake">
                {loginError}
              </div>
            )}
            
            <Form.Item className="login-button-container">
              <Button
                type="primary"
                htmlType="submit"
                className="login-button"
                size="large"
                loading={loading}
                block
              >
                {loading ? '登录中...' : '登录'}
                <span className="login-button-shine"></span>
              </Button>
            </Form.Item>
            
            <div className="login-links">
              <a href="#" className="login-link" onClick={handleForgotPassword}>忘记密码?</a>
            </div>
          </Form>
        </div>
      </div>
      
      <ThemeSwitcher currentTheme={theme} onChange={handleThemeChange} />
    </div>
  );
};

export default Login; 