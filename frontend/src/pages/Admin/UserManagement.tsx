import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { App, Button, Popconfirm, Select, Space, Table, Tag } from 'antd';
import { CrownOutlined, CustomerServiceOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/useAuthStore';
import type { UserResponse } from '@/types/auth';
import * as userService from '@/services/userService';

const ROLE_META: Record<string, { label: string; color: string; icon: ReactNode }> = {
  user: { label: '普通用户', color: 'blue', icon: <UserOutlined /> },
  staff: { label: '客服', color: 'green', icon: <CustomerServiceOutlined /> },
  admin: { label: '管理员', color: 'red', icon: <CrownOutlined /> },
};

export default function UserManagementPage() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const { user: currentUser } = useAuthStore();
  const { message } = App.useApp();

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await userService.getUsers();
      const items = Array.isArray(data) ? data : (data as any).items || [];
      setUsers(items);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await userService.updateUserRole(userId, newRole);
      message.success('角色已更新');
      void loadUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '角色更新失败');
    }
  };

  const handleActivate = async (userId: number) => {
    try {
      await userService.activateUser(userId);
      message.success('用户已启用');
      void loadUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '启用用户失败');
    }
  };

  const handleDeactivate = async (userId: number) => {
    try {
      await userService.deactivateUser(userId);
      message.success('用户已禁用');
      void loadUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '禁用用户失败');
    }
  };

  const handleDelete = async (userId: number) => {
    try {
      await userService.deleteUser(userId);
      message.success('用户已删除');
      void loadUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除用户失败');
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ marginBottom: 24, color: 'var(--text-primary)' }}>用户管理</h2>
      <Table
        dataSource={users}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 70 },
          { title: '用户名', dataIndex: 'username' },
          { title: '邮箱', dataIndex: 'email' },
          { title: '手机号', dataIndex: 'phone' },
          {
            title: '角色',
            dataIndex: 'role',
            width: 120,
            render: (role: string) => {
              const meta = ROLE_META[role] || ROLE_META.user;
              return <Tag color={meta.color}>{meta.icon} {meta.label}</Tag>;
            },
          },
          {
            title: '状态',
            dataIndex: 'is_active',
            width: 100,
            render: (isActive: boolean) => (
              <Tag color={isActive ? 'green' : 'gray'}>{isActive ? '启用' : '禁用'}</Tag>
            ),
          },
          {
            title: '创建时间',
            dataIndex: 'created_at',
            render: (text: string) => (text ? new Date(text).toLocaleString() : '-'),
          },
          {
            title: '操作',
            key: 'actions',
            width: 320,
            render: (_: unknown, record: UserResponse) => {
              if (record.id === currentUser?.id) return null;
              return (
                <Space>
                  <Select
                    value={record.role}
                    onChange={(value) => handleRoleChange(record.id, value)}
                    style={{ width: 120 }}
                    size="small"
                    options={[
                      { value: 'user', label: '普通用户' },
                      { value: 'staff', label: '客服' },
                      { value: 'admin', label: '管理员' },
                    ]}
                  />

                  {record.is_active ? (
                    <Popconfirm
                      title="确定要禁用该用户吗？"
                      onConfirm={() => handleDeactivate(record.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button danger size="small">禁用</Button>
                    </Popconfirm>
                  ) : (
                    <Button type="primary" size="small" onClick={() => handleActivate(record.id)}>
                      启用
                    </Button>
                  )}

                  <Popconfirm
                    title="确定要删除该用户吗？"
                    onConfirm={() => handleDelete(record.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button danger icon={<DeleteOutlined />} size="small">
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              );
            },
          },
        ]}
      />
    </div>
  );
}
