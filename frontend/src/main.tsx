import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider, App as AntApp, theme as antTheme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import { useThemeStore } from './stores/useThemeStore';
import './global.css';

function Root() {
  const mode = useThemeStore((s) => s.mode);
  const isDark = mode === 'dark';

  // Apply data-theme to <html> so CSS can respond
  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
  }, [mode]);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
        token: isDark
          ? {
              colorPrimary: '#00d4ff',
              colorSuccess: '#00ff88',
              colorWarning: '#ffb300',
              colorError: '#ff4472',
              colorInfo: '#00d4ff',
              borderRadius: 8,
              fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
              fontSize: 14,
              lineHeight: 1.6,
            }
          : {
              colorPrimary: '#1677ff',
              borderRadius: 8,
              fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
              fontSize: 14,
              lineHeight: 1.6,
            },
        components: isDark
          ? {
              Layout: { siderBg: '#0d1321', triggerBg: '#0d1321', triggerColor: '#00d4ff' },
            }
          : {},
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
