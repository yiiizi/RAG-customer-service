import { useState, useDeferredValue, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Button, Input, List, Modal } from 'antd';
import {
  MessageOutlined,
  DatabaseOutlined,
  QuestionCircleOutlined,
  DashboardOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  FileTextOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useThemeStore } from '@/stores/useThemeStore';
import { useChatStore } from '@/stores/useChatStore';
import dayjs from 'dayjs';
import SourcePanel from '@/pages/Chat/SourcePanel';
import KnowledgeBasePage from '@/pages/KnowledgeBase';
import FAQPage from '@/pages/FAQ';
import DashboardPage from '@/pages/Dashboard';
import SettingsPage from '@/pages/Settings';

type ModalKey = 'knowledge' | 'faq' | 'dashboard' | 'settings' | null;

const modalConfig: Record<NonNullable<ModalKey>, { title: string; width: number }> = {
  knowledge: { title: '知识库管理', width: 900 },
  faq: { title: 'FAQ 高频问答管理', width: 900 },
  dashboard: { title: '数据大盘', width: 1100 },
  settings: { title: '系统设置', width: 720 },
};

export default function MainLayout() {
  const [activeModal, setActiveModal] = useState<ModalKey>(null);
  const isDark = useThemeStore((s) => s.mode === 'dark');
  const {
    conversations, activeId, setActive, newConversation, deleteConversation,
    historyVisible, setHistoryVisible, sourceVisible, setSourceVisible,
    sidebarCollapsed, setSidebarCollapsed,
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

  const renderModalContent = () => {
    switch (activeModal) {
      case 'knowledge': return <KnowledgeBasePage />;
      case 'faq': return <FAQPage />;
      case 'dashboard': return <DashboardPage />;
      case 'settings': return <SettingsPage />;
      default: return null;
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-deep)' }}>

      {/* ── Left Sidebar ──────────────────────────────────── */}
      {showSidebar && (
        <div style={{
          width: 260, flexShrink: 0,
          background: 'var(--sidebar-bg)',
          borderRight: '1px solid var(--border-subtle)',
          boxShadow: isDark ? '2px 0 24px rgba(0,0,0,0.4)' : '2px 0 12px rgba(0,0,0,0.06)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}>
          {/* Logo */}
          <div
            style={{
              height: 56, display: 'flex', alignItems: 'center', padding: '0 16px',
              borderBottom: '1px solid var(--border-subtle)', gap: 10,
              cursor: 'pointer', flexShrink: 0,
            }}
          >
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, var(--accent), var(--accent-dim))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: 'var(--accent-glow)', flexShrink: 0,
            }}>
              <ThunderboltOutlined style={{ color: '#fff', fontSize: 16 }} />
            </div>
            <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: 1, color: 'var(--text-primary)' }}>
              {isDark ? 'NEURAL RAG' : 'RAG 智能问答'}
            </span>
          </div>

          {/* New + Search */}
          <div style={{ padding: '10px 12px 6px', flexShrink: 0 }}>
            <Button type="primary" block size="small" icon={<PlusOutlined />}
              onClick={() => newConversation()}
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
            />
          </div>

          {/* Conversation list */}
          <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
            <List
              dataSource={filteredConversations}
              renderItem={(conv) => {
                const isActive = conv.id === activeId;
                return (
                  <List.Item
                    onClick={() => setActive(conv.id)}
                    className={`conv-item${isActive ? ' active' : ''}`}
                    actions={[
                      <Button
                        key="del" type="text" size="small" icon={<DeleteOutlined />}
                        danger
                        onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                        title="删除对话"
                        className="conv-delete"
                      />,
                    ]}
                  >
                    <List.Item.Meta
                      title={<div className="conv-title">{conv.title}</div>}
                      description={<span className="conv-time">{dayjs(conv.updatedAt).format('MM-DD HH:mm')}</span>}
                    />
                  </List.Item>
                );
              }}
            />
          </div>

          {/* Status — pinned to bottom */}
          <div style={{
            padding: '8px 12px', margin: '0 12px 12px', borderRadius: 8,
            background: 'var(--bg-hover)', border: '1px solid var(--border-subtle)',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%', background: 'var(--green)',
                boxShadow: isDark ? '0 0 6px var(--green)' : 'none',
                animation: 'pulse 2s infinite',
              }} />
              <span style={{ fontSize: 10, color: 'var(--green)', fontWeight: 500 }}>系统运行中</span>
            </div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 3 }}>
              Milvus · MySQL · Redis
            </div>
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
          <button className="nav-btn" onClick={() => setActiveModal('knowledge')}>
            <DatabaseOutlined /> 知识库管理
          </button>
          <button className="nav-btn" onClick={() => setActiveModal('faq')}>
            <QuestionCircleOutlined /> FAQ 管理
          </button>
          <button className="nav-btn" onClick={() => setActiveModal('dashboard')}>
            <DashboardOutlined /> 数据大盘
          </button>
          <button className="nav-btn" onClick={() => setActiveModal('settings')}>
            <SettingOutlined /> 系统设置
          </button>

          <button
            className={`nav-btn${sourceVisible ? ' active' : ''}`}
            onClick={() => setSourceVisible(!sourceVisible)}
            style={{ marginLeft: 4 }}
          >
            <FileTextOutlined /> 引用来源
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'hidden', background: 'var(--content-bg)', minHeight: 0 }}>
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
