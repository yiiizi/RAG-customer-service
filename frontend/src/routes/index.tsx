import { RouteObject } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import AdminLayout from '@/layouts/AdminLayout';
import ChatPage from '@/pages/Chat';
import DashboardPage from '@/pages/Dashboard';
import SettingsPage from '@/pages/Settings';
import Login from '@/pages/Auth/Login';
import AdminLogin from '@/pages/Auth/AdminLogin';
import Register from '@/pages/Auth/Register';
import UserManagementPage from '@/pages/Admin/UserManagement';
import AdminDashboardPage from '@/pages/Admin/AdminDashboard';
import AdminKnowledgePage from '@/pages/Admin/AdminKnowledge';
import AdminFAQPage from '@/pages/Admin/AdminFAQ';
import TicketsPage from '@/pages/Tickets';
import UnresolvedPage from '@/pages/Unresolved';
import RequireAuth from '@/components/RequireAuth';

export const routes: RouteObject[] = [
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/admin/login',
    element: <AdminLogin />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    path: '/',
    element: <RequireAuth><MainLayout /></RequireAuth>,
    children: [
      { index: true, element: <ChatPage /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'tickets', element: <TicketsPage /> },
      { path: 'unresolved', element: <RequireAuth allowedRoles={['staff', 'admin']}><UnresolvedPage /></RequireAuth> },
      { path: 'dashboard', element: <RequireAuth allowedRoles={['staff', 'admin']}><DashboardPage /></RequireAuth> },
      { path: 'settings', element: <RequireAuth requireAdmin><SettingsPage /></RequireAuth> },
    ],
  },
  {
    path: '/admin',
    element: <RequireAuth requireAdmin><AdminLayout /></RequireAuth>,
    children: [
      { index: true, element: <AdminDashboardPage /> },
      { path: 'users', element: <UserManagementPage /> },
      { path: 'knowledge', element: <AdminKnowledgePage /> },
      { path: 'faq', element: <AdminFAQPage /> },
    ],
  },
];
