/**
 * Register page — matching login layout.
 * 颜色跟随系统主题自动适配，左侧装饰区保留深色渐变+白色文字
 */

import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, App, Row, Col } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/useAuthStore';
import Captcha from '@/components/Captcha';

const Register = () => {
  const navigate = useNavigate();
  const { register, loading, error, clearError } = useAuthStore();
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const captchaCodeRef = useRef('');
  const [captchaInput, setCaptchaInput] = useState('');

  const handleRegister = async (values: any) => {
    try {
      await register({
        username: values.username,
        email: values.email,
        phone: values.phone,
        password: values.password,
        confirm_password: values.confirm_password,
      });
      message.success('注册成功！');
      navigate('/');
    } catch (error) {
      // Error is already handled in store
    }
  };

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
              width: 72, height: 72, borderRadius: 20,
              background: 'linear-gradient(135deg, #6C63FF, #FF6584)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
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
            创建账户
          </h1>
          <p style={{ textAlign: 'center', marginBottom: 28, fontSize: 13, color: 'var(--text-secondary)' }}>
            注册以开始使用智能客服
          </p>

          <Form form={form} onFinish={handleRegister} layout="vertical" className="underline-input">
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名！' },
                { min: 3, message: '用户名至少3个字符！' },
                { max: 50, message: '用户名最多50个字符！' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                size="large"
                style={{ height: 44, color: 'var(--text-primary)' }}
              />
            </Form.Item>

            <Form.Item
              name="email"
              rules={[{ type: 'email', message: '请输入有效的邮箱地址！' }]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="邮箱（可选）"
                size="large"
                style={{ height: 44, color: 'var(--text-primary)' }}
              />
            </Form.Item>

            <Form.Item
              name="phone"
              rules={[{ pattern: /^[0-9]+$/, message: '请输入有效的手机号！' }]}
            >
              <Input
                prefix={<PhoneOutlined />}
                placeholder="手机号（可选）"
                size="large"
                style={{ height: 44, color: 'var(--text-primary)' }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码！' },
                { min: 6, message: '密码至少6个字符！' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                size="large"
                style={{ height: 44, color: 'var(--text-primary)' }}
              />
            </Form.Item>

            <Form.Item
              name="confirm_password"
              rules={[
                { required: true, message: '请确认密码！' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的密码不一致！'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="确认密码"
                size="large"
                style={{ height: 44, color: 'var(--text-primary)' }}
              />
            </Form.Item>

            <Form.Item
              name="captcha"
              rules={[{ required: true, message: '请输入验证码！' }]}
            >
              <Row gutter={8}>
                <Col flex="auto">
                  <Input
                    placeholder="验证码"
                    size="large"
                    maxLength={4}
                    value={captchaInput}
                    onChange={(e) => setCaptchaInput(e.target.value)}
                    style={{ height: 44, color: 'var(--text-primary)' }}
                  />
                </Col>
                <Col>
                  <Captcha
                    onChange={(code) => { captchaCodeRef.current = code; }}
                    height={44}
                    width={120}
                  />
                </Col>
              </Row>
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
                注册
              </Button>
            </Form.Item>
          </Form>

          {error && (
            <div style={{ color: 'var(--red)', marginTop: '10px', textAlign: 'center', fontSize: 13 }}>
              {error}
            </div>
          )}

          <div style={{ marginTop: '20px', textAlign: 'center', fontSize: 13 }}>
            <span style={{ color: 'var(--text-secondary)' }}>已有账户？{' '}</span>
            <a href="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 500, transition: 'text-decoration 0.2s' }}
              onMouseEnter={(e) => { e.currentTarget.style.textDecoration = 'underline'; }}
              onMouseLeave={(e) => { e.currentTarget.style.textDecoration = 'none'; }}
            >
              立即登录
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
