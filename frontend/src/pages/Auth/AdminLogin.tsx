/**
 * Admin login page with dark/admin theme.
 * 颜色跟随系统主题自动适配
 */

import { Form, Input, Button, App } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/useAuthStore';

const AdminLogin = () => {
  const navigate = useNavigate();
  const { login, loading, error, clearError } = useAuthStore();
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const handleLogin = async (values: any) => {
    try {
      const loginData = {
        login_type: 'username',
        username: values.username,
        password: values.password,
      };
      await login(loginData);
      const user = useAuthStore.getState().user;
      if (user?.role !== 'admin') {
        message.warning('该账号不是管理员');
        return;
      }
      message.success('管理员登录成功！');
      navigate('/admin');
    } catch (error) {
      // Error is already handled in store
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0D0D1A 0%, #1A1A2E 50%, #2A1A3E 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative elements */}
      <div className="login-deco-grid" />
      <div className="login-deco-circle" style={{ width: 400, height: 400, top: '-15%', right: '-10%', background: '#6C63FF' }} />
      <div className="login-deco-circle" style={{ width: 250, height: 250, bottom: '-5%', left: '-5%', background: '#FF6584' }} />

      <div
        className="glass-card"
        style={{
          width: 400,
          padding: '40px 32px',
          position: 'relative',
          zIndex: 2,
        }}
      >
        {/* Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #6C63FF, #FF6584)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 16,
              boxShadow: '0 4px 20px rgba(108, 99, 255, 0.4)',
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1Z" fill="white" opacity="0.9" />
              <path d="M10 12L11.5 13.5L14.5 10.5" stroke="#6C63FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h1 style={{
            color: 'var(--text-primary)',
            fontSize: 22,
            fontWeight: 700,
            marginBottom: 4,
            letterSpacing: 2,
          }}>
            管理后台登录
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
            RAG 智能客服系统 · 管理员专用
          </p>
        </div>

        <Form form={form} onFinish={handleLogin} layout="vertical" className="underline-input">
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入管理员账号' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="管理员账号"
              size="large"
              style={{ height: 44, color: 'var(--text-primary)' }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
              style={{ height: 44, color: 'var(--text-primary)' }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{
                height: 44,
                borderRadius: 8,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #6C63FF, #FF6584)',
                border: 'none',
                boxShadow: '0 4px 16px rgba(108, 99, 255, 0.3)',
              }}
            >
              登录管理后台
            </Button>
          </Form.Item>
        </Form>

        {error && (
          <div style={{ color: 'var(--red)', marginTop: 8, textAlign: 'center', fontSize: 13 }}>
            {error}
          </div>
        )}

        <div
          style={{
            marginTop: 20,
            textAlign: 'center',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: 16,
          }}
        >
          <a
            href="/login"
            style={{
              color: 'var(--text-secondary)',
              fontSize: 13,
              textDecoration: 'none',
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
          >
            ← 返回普通用户登录
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
