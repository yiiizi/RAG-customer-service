import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Avatar, Button, Dropdown, Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  QuestionCircleOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/useAuthStore';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/admin', icon: <DashboardOutlined />, label: '管理概览' },
  { key: '/admin/users', icon: <TeamOutlined />, label: '用户管理' },
  { key: '/admin/knowledge', icon: <DatabaseOutlined />, label: '知识库管理' },
  { key: '/admin/faq', icon: <QuestionCircleOutlined />, label: 'FAQ 管理' },
];

export default function AdminLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/admin/login', { replace: true });
  };

  return (
    <Layout style={{ minHeight: '100vh', height: '100vh', overflow: 'hidden' }}>
      <Sider trigger={null} collapsible collapsed={collapsed} theme="dark" style={{ height: '100vh', overflow: 'auto' }}>
        <div
          className="admin-sider-logo"
          style={{
            height: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-primary)',
            fontSize: collapsed ? 14 : 16,
            fontWeight: 700,
            borderBottom: '1px solid rgba(108, 99, 255, 0.15)',
          }}
        >
          {collapsed ? '管理' : '后台管理'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <Layout style={{ height: '100vh', minHeight: 0, overflow: 'hidden' }}>
        <Header
          style={{
            padding: '0 24px',
            background: 'var(--bg-panel)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            <Button icon={<MessageOutlined />} onClick={() => navigate('/chat')}>
              返回聊天
            </Button>
          </div>

          <Dropdown
            menu={{
              items: [
                { key: 'chat', icon: <MessageOutlined />, label: '返回聊天', onClick: () => navigate('/chat') },
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout },
              ],
            }}
            placement="bottomRight"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <Avatar size="small" icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #6C63FF, #FF6584)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-primary)' }}>{user?.username || '管理员'}</span>
            </div>
          </Dropdown>
        </Header>

        <Content
          className="fade-in"
          style={{
            margin: 24,
            padding: 24,
            background: 'var(--bg-card)',
            borderRadius: 12,
            minHeight: 0,
            height: 'calc(100vh - 112px)',
            overflowY: 'auto',
            overflowX: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
