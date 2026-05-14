import { useState, useDeferredValue, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Button, Input, List, Modal } from 'antd';
import {
  MessageOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  FileTextOutlined,
  PlusOutlined,
  DeleteOutlined,
  LogoutOutlined,
  CustomerServiceOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { useThemeStore } from '@/stores/useThemeStore';
import { useChatStore } from '@/stores/useChatStore';
import { useAuthStore } from '@/stores/useAuthStore';
import dayjs from 'dayjs';
import SourcePanel from '@/pages/Chat/SourcePanel';
import SettingsPage from '@/pages/Settings';

type ModalKey = 'settings' | null;

const modalConfig: Record<NonNullable<ModalKey>, { title: string; width: number }> = {
  settings: { title: '系统设置', width: 1100 },
};

/** Get initials + gradient color for a conversation avatar */
function getConvAvatar(title: string) {
  const first = (title || 'N')[0].toUpperCase();
  const colors = [
    'linear-gradient(135deg, #6C63FF, #8B7FFF)',
    'linear-gradient(135deg, #FF6584, #FF8FA3)',
    'linear-gradient(135deg, #4ADE80, #86EFAC)',
    'linear-gradient(135deg, #FBBF24, #FDE68A)',
    'linear-gradient(135deg, #A78BFA, #C4B5FD)',
  ];
  const idx = title.charCodeAt(0) % colors.length;
  return { first, bg: colors[idx] };
}

export default function MainLayout() {
  const [activeModal, setActiveModal] = useState<ModalKey>(null);
  const isDark = useThemeStore((s) => s.resolvedMode === 'dark');
  const {
    conversations, activeId, setActive, newConversation, deleteConversation,
    historyVisible, setHistoryVisible, sourceVisible, setSourceVisible,
    sidebarCollapsed, setSidebarCollapsed, loadConversations,
  } = useChatStore();

  const showSidebar = !sidebarCollapsed && historyVisible;
  const [searchText, setSearchText] = useState('');
  const deferredSearch = useDeferredValue(searchText);

  const filteredConversations = deferredSearch.trim()
    ? conversations.filter((c) => {
        const q = deferredSearch.toLowerCase();
        if (c.title.toLowerCase().includes(q)) return true;
        return c.messages.some((m) => m.content.toLowerCase().includes(q));
      })
    : conversations;

  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  const handleLogout = () => {
    logout();
    localStorage.removeItem('rag-chat-store');
    navigate('/login');
  };

  const renderModalContent = () => {
    switch (activeModal) {
      case 'settings': return <SettingsPage />;
      default: return null;
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-deep)' }}>

      {/* ── Left Sidebar ──────────────────────────────────── */}
      {showSidebar && (
        <div
          className="sidebar-container"
          style={{
            width: 260, flexShrink: 0,
            background: 'var(--sidebar-bg)',
            borderRight: '1px solid var(--border-subtle)',
            boxShadow: isDark ? '2px 0 24px rgba(0,0,0,0.4)' : '2px 0 12px rgba(0,0,0,0.06)',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
          }}
        >
          {/* Logo */}
          <div
            style={{
              height: 56, display: 'flex', alignItems: 'center', padding: '0 16px',
              borderBottom: '1px solid var(--border-subtle)', gap: 10,
              cursor: 'pointer', flexShrink: 0,
            }}
          >
            <div className="brand-logo">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H6V22L10 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor" style={{ color: 'var(--text-primary)' }} />
              </svg>
            </div>
            <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: 1, color: 'var(--text-primary)' }}>
              RAG 智能问答
            </span>
          </div>

          {/* New + Search */}
          <div style={{ padding: '10px 12px 6px', flexShrink: 0 }}>
            <Button type="primary" block size="small" icon={<PlusOutlined />}
              onClick={() => { void newConversation(); }}
              style={{ borderRadius: 8, height: 30, fontWeight: 600, fontSize: 12 }}>
              新对话
            </Button>
          </div>
          <div style={{ padding: '0 12px 6px', flexShrink: 0 }}>
            <Input
              prefix={<MessageOutlined style={{ color: 'var(--text-muted)', fontSize: 12 }} />}
              placeholder="搜索对话..." size="small"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
              style={{ borderRadius: 8 }}
            />
          </div>

          {/* Conversation list */}
          <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
            <List
              dataSource={filteredConversations}
              renderItem={(conv) => {
                const isActive = conv.id === activeId;
                const avatar = getConvAvatar(conv.title);
                const lastMsg = conv.messages.length > 0
                  ? conv.messages[conv.messages.length - 1].content.slice(0, 30)
                  : '';
                return (
                  <List.Item
                    onClick={() => setActive(conv.id)}
                    className={`conv-item${isActive ? ' active' : ''}`}
                    actions={[
                      <Button
                        key="del" type="text" size="small" icon={<DeleteOutlined />}
                        className="conv-delete"
                        onClick={(e) => { e.stopPropagation(); void deleteConversation(conv.id); }}
                        title="删除对话"
                        style={{ fontSize: 12, color: 'var(--text-muted)' }}
                      />,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={
                        <div style={{
                          width: 32, height: 32, borderRadius: 10, flexShrink: 0,
                          background: avatar.bg,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: '#fff', fontSize: 13, fontWeight: 700,
                        }}>
                          {avatar.first}
                        </div>
                      }
                      title={<div className="conv-title">{conv.title}</div>}
                      description={
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 140 }}>
                          {lastMsg || dayjs(conv.updatedAt).format('MM-DD HH:mm')}
                        </div>
                      }
                    />
                  </List.Item>
                );
              }}
            />
          </div>

          {/* Status — pinned to bottom */}
          <div style={{
            padding: '10px 12px', margin: '0 12px 12px', borderRadius: 12,
            background: 'var(--bg-hover)', border: '1px solid var(--border-subtle)',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="status-dot" />
              <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 500 }}>系统运行中</span>
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
              Milvus · MySQL · Redis
            </div>
            <Button
              icon={<LogoutOutlined />}
              block
              size="small"
              onClick={handleLogout}
              style={{ marginTop: 10, borderRadius: 8, color: 'var(--text-secondary)', fontSize: 12 }}
            >
              退出登录
            </Button>
          </div>
        </div>
      )}

      {/* ── Center: Top nav + Content ─────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        {/* Top navigation bar */}
        <div style={{
          height: 46, display: 'flex', alignItems: 'center',
          padding: '0 16px', gap: 4, flexShrink: 0,
          borderBottom: '1px solid var(--border-subtle)',
          background: 'var(--bg-panel)',
        }}>
          {/* Left: history toggle */}
          <button
            className={`nav-btn${!sidebarCollapsed && historyVisible ? ' active' : ''}`}
            onClick={() => {
              if (sidebarCollapsed || !historyVisible) {
                setSidebarCollapsed(false);
                setHistoryVisible(true);
              } else {
                setHistoryVisible(false);
              }
            }}
          >
            <HistoryOutlined /> 对话历史
          </button>

          <div style={{ flex: 1 }} />

          {/* Right: modal buttons */}
          {location.pathname !== '/chat' && location.pathname !== '/' && (
            <button className="nav-btn" onClick={() => navigate('/chat')}>
              <MessageOutlined /> 返回聊天
            </button>
          )}

          <button className="nav-btn" onClick={() => navigate('/tickets')}>
            <CustomerServiceOutlined /> {user?.role === 'user' ? '我的工单' : '工单中心'}
          </button>

          {user?.role !== 'user' && (
            <button className="nav-btn" onClick={() => navigate('/unresolved')}>
              <BulbOutlined /> 未解决问题
            </button>
          )}

          {user?.role !== 'user' && (
            <button className="nav-btn" onClick={() => navigate('/dashboard')}>
              <ThunderboltOutlined /> 运营看板
            </button>
          )}

          {isAdmin && (
            <button className="nav-btn" onClick={() => setActiveModal('settings')}>
              <SettingOutlined /> 系统设置
            </button>
          )}

          {isAdmin && (
            <button className="nav-btn" onClick={() => navigate('/admin')}>
              <SettingOutlined /> 管理后台
            </button>
          )}

          <button
            className={`nav-btn${sourceVisible ? ' active' : ''}`}
            onClick={() => setSourceVisible(!sourceVisible)}
            style={{ marginLeft: 4 }}
          >
            <FileTextOutlined /> 产品推荐
          </button>
        </div>

        {/* Content */}
        <div
          className="fade-in"
          style={{
            flex: 1,
            overflowY: location.pathname === '/chat' || location.pathname === '/' ? 'hidden' : 'auto',
            overflowX: 'hidden',
            background: 'var(--content-bg)',
            minHeight: 0,
          }}
        >
          <Outlet />
        </div>
      </div>

      {/* ── Right: Source Panel (full height) ──────────────── */}
      {sourceVisible && <SourcePanel />}

      {/* ── Modals ────────────────────────────────────────── */}
      {activeModal && (
        <Modal
          title={modalConfig[activeModal].title}
          open={!!activeModal}
          onCancel={() => setActiveModal(null)}
          footer={null}
          width={modalConfig[activeModal].width}
          styles={{ body: { padding: 0, maxHeight: '75vh', overflow: 'auto' } }}
          destroyOnClose
        >
          {renderModalContent()}
        </Modal>
      )}
    </div>
  );
}
