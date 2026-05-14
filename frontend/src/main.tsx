import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider, App as AntApp, theme as antTheme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import { useThemeStore, applyThemeToDOM } from './stores/useThemeStore';
import './global.css';

// ★ 关键：在 React 渲染前同步设置 data-theme，避免首帧闪烁/CSS变量不生效
// 这行必须在任何渲染前执行，确保 CSS 变量和 [data-theme] 选择器立即生效
applyThemeToDOM(useThemeStore.getState().resolvedMode);

function Root() {
  const resolvedMode = useThemeStore((s) => s.resolvedMode);
  const isDark = resolvedMode === 'dark';

  // 保持 data-theme 与 store 同步
  React.useEffect(() => {
    applyThemeToDOM(resolvedMode);
  }, [resolvedMode]);

  const sharedToken = {
    colorPrimary: '#6C63FF',
    colorSuccess: '#4ADE80',
    colorWarning: '#FBBF24',
    colorError: '#F87171',
    colorInfo: '#6C63FF',
    borderRadius: 6,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    fontSize: 14,
    lineHeight: 1.6,
  };

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
        token: isDark
          ? {
              ...sharedToken,
              colorBgContainer: '#1A1A2E',
              colorBgElevated: '#1E1E32',
              colorBgLayout: '#0D0D1A',
              colorBorder: '#4A4A6A',
              colorBorderSecondary: '#4A4A6A',
              colorText: '#E8E8F0',
              colorTextSecondary: '#8888A0',
              colorTextTertiary: '#5C5C78',
              colorFillSecondary: 'rgba(108, 99, 255, 0.15)',
            }
          : {
              ...sharedToken,
              colorBgContainer: '#FFFFFF',
              colorBgElevated: '#FFFFFF',
              colorBgLayout: '#F8F9FF',
              colorBorder: '#E0E0F0',
              colorBorderSecondary: '#E0E0F0',
              colorText: '#1A1A2E',
              colorTextSecondary: '#8888A0',
              colorTextTertiary: '#A0A0B8',
              colorFillSecondary: 'rgba(108, 99, 255, 0.08)',
            },
        components: isDark
          ? {
              Layout: { siderBg: '#1A1A2E', triggerBg: '#1A1A2E', triggerColor: '#6C63FF' },
              Menu: { darkItemBg: 'transparent', darkItemSelectedBg: 'rgba(108,99,255,0.15)' },
            }
          : {
              Layout: { siderBg: '#F0F1FF', triggerBg: '#F0F1FF', triggerColor: '#6C63FF' },
            },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
