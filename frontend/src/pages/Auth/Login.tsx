/**
 * Login page — left decoration + right form layout.
 * 颜色跟随系统主题自动适配，左侧装饰区保留深色渐变+白色文字
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, Form, Input, Button, App, TabsProps } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/useAuthStore';

type LoginType = 'username' | 'email' | 'phone';

const Login = () => {
  const navigate = useNavigate();
  const { login, loading, error, clearError } = useAuthStore();
  const [loginType, setLoginType] = useState<LoginType>('username');
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const handleLogin = async (values: any) => {
    try {
      const loginData: any = {
        login_type: loginType,
        password: values.password,
      };

      if (loginType === 'username') {
        loginData.username = values.username;
      } else if (loginType === 'email') {
        loginData.email = values.email;
      } else if (loginType === 'phone') {
        loginData.phone = values.phone;
      }

      await login(loginData);
      message.success('登录成功！');
      const loggedUser = useAuthStore.getState().user;
      if (loggedUser?.role === 'admin') {
        navigate('/admin');
      } else if (loggedUser?.role === 'staff') {
        navigate('/tickets');
      } else {
        navigate('/chat');
      }
    } catch (error) {
      // Error is already handled in store
    }
  };

  const inputStyle = {
    height: 44,
    color: 'var(--text-primary)',
  };

  const tabItems: TabsProps['items'] = [
    {
      key: 'username',
      label: '用户名',
      children: (
        <Form form={form} onFinish={handleLogin} layout="vertical" className="underline-input">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名！' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" size="large" style={inputStyle} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码！' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" style={inputStyle} />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{ height: 44, borderRadius: 8, fontWeight: 600 }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'email',
      label: '邮箱',
      children: (
        <Form form={form} onFinish={handleLogin} layout="vertical" className="underline-input">
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱！' },
              { type: 'email', message: '请输入有效的邮箱地址！' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" size="large" style={inputStyle} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码！' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" style={inputStyle} />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{ height: 44, borderRadius: 8, fontWeight: 600 }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'phone',
      label: '手机号',
      children: (
        <Form form={form} onFinish={handleLogin} layout="vertical" className="underline-input">
          <Form.Item name="phone" rules={[{ required: true, message: '请输入手机号！' }]}>
            <Input prefix={<PhoneOutlined />} placeholder="手机号" size="large" style={inputStyle} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码！' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" style={inputStyle} />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{ height: 44, borderRadius: 8, fontWeight: 600 }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg-deep)' }}>
      {/* Left: Decoration area — 始终使用深色渐变+白色文字 */}
      <div
        className="login-deco-left"
        style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          background: 'linear-gradient(135deg, #0D0D1A 0%, #1A1A2E 50%, #2A1A3E 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div className="login-deco-grid" />
        <div className="login-deco-circle" style={{ width: 400, height: 400, top: '-10%', left: '-10%', background: '#6C63FF' }} />
        <div className="login-deco-circle" style={{ width: 300, height: 300, bottom: '5%', right: '-5%', background: '#FF6584' }} />
        <div className="login-deco-circle" style={{ width: 200, height: 200, top: '40%', left: '30%', background: '#6C63FF', opacity: 0.3 }} />

        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center', padding: 40 }}>
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 20,
              background: 'linear-gradient(135deg, #6C63FF, #FF6584)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 24,
              boxShadow: '0 8px 32px rgba(108, 99, 255, 0.4)',
              animation: 'float 6s ease-in-out infinite',
            }}
          >
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
              <path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H6V22L10 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white" />
              <circle cx="8" cy="9" r="1.5" fill="#6C63FF" />
              <circle cx="12" cy="9" r="1.5" fill="#6C63FF" />
              <circle cx="16" cy="9" r="1.5" fill="#6C63FF" />
            </svg>
          </div>
          <h1 style={{ color: '#fff', fontSize: 32, fontWeight: 700, letterSpacing: 2, marginBottom: 8, textShadow: '0 2px 8px rgba(108,99,255,0.3)' }}>
            RAG 智能客服
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.65)', fontSize: 15, letterSpacing: 1 }}>
            基于 AI 的智能问答助手
          </p>
        </div>
      </div>

      {/* Right: Form area — 跟随主题颜色 */}
      <div
        className="login-layout"
        style={{
          width: 480,
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 48,
          background: 'var(--bg-panel)',
        }}
      >
        <div style={{ width: '100%', maxWidth: 360 }}>
          <h1 style={{ textAlign: 'center', marginBottom: 4, fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
            欢迎回来
          </h1>
          <p style={{ textAlign: 'center', marginBottom: 28, fontSize: 13, color: 'var(--text-secondary)' }}>
            登录您的账户以继续
          </p>

          <Tabs
            activeKey={loginType}
            onChange={(key) => {
              setLoginType(key as LoginType);
              form.resetFields();
              clearError();
            }}
            items={tabItems}
            centered
          />

          {error && (
            <div style={{ color: 'var(--red)', marginTop: '10px', textAlign: 'center', fontSize: 13 }}>
              {error}
            </div>
          )}

          <div style={{ marginTop: '20px', textAlign: 'center', fontSize: 13 }}>
            <span style={{ color: 'var(--text-secondary)' }}>还没有账户？{' '}</span>
            <a href="/register" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 500, transition: 'text-decoration 0.2s' }}
              onMouseEnter={(e) => { e.currentTarget.style.textDecoration = 'underline'; }}
              onMouseLeave={(e) => { e.currentTarget.style.textDecoration = 'none'; }}
            >
              立即注册
            </a>
          </div>

          <div style={{ marginTop: 12, textAlign: 'center' }}>
            <a href="/admin/login" style={{ fontSize: 13, color: 'var(--text-secondary)', textDecoration: 'none', transition: 'color 0.2s' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              管理后台入口 →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
