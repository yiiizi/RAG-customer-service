import { RouteObject } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import ChatPage from '@/pages/Chat';
import KnowledgeBasePage from '@/pages/KnowledgeBase';
import FAQPage from '@/pages/FAQ';
import DashboardPage from '@/pages/Dashboard';
import SettingsPage from '@/pages/Settings';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <ChatPage /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'knowledge', element: <KnowledgeBasePage /> },
      { path: 'faq', element: <FAQPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
];
