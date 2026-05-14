import { useCallback, useEffect, useMemo, useState } from 'react';
import { App, Button, Card, Descriptions, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import * as ticketService from '@/services/ticketService';
import { useAuthStore } from '@/stores/useAuthStore';
import type { Ticket, TicketStatus } from '@/types/ticket';

const STATUS_COLORS: Record<TicketStatus, string> = {
  open: 'gold',
  processing: 'blue',
  resolved: 'green',
  closed: 'default',
};

const STATUS_LABELS: Record<TicketStatus, string> = {
  open: '待处理',
  processing: '处理中',
  resolved: '已解决',
  closed: '已关闭',
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'default',
};

export default function TicketsPage() {
  const { message } = App.useApp();
  const user = useAuthStore((s) => s.user);
  const isStaffView = user?.role === 'staff' || user?.role === 'admin';

  const [items, setItems] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('');
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);
  const [staffNote, setStaffNote] = useState('');
  const [nextStatus, setNextStatus] = useState<TicketStatus>('processing');
  const [saving, setSaving] = useState(false);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      const data = isStaffView
        ? await ticketService.getQueueTickets(statusFilter)
        : await ticketService.getMyTickets();
      setItems(data.items);
    } finally {
      setLoading(false);
    }
  }, [isStaffView, statusFilter]);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  const openEdit = (ticket: Ticket) => {
    setEditingTicket(ticket);
    setStaffNote(ticket.staff_note || '');
    setNextStatus(ticket.status === 'open' ? 'processing' : ticket.status);
  };

  const handleClaim = async (ticketId: number) => {
    await ticketService.claimTicket(ticketId);
    message.success('工单已领取');
    await loadTickets();
  };

  const handleSave = async () => {
    if (!editingTicket) return;
    setSaving(true);
    try {
      await ticketService.updateTicket(editingTicket.id, {
        status: nextStatus,
        staff_note: staffNote,
      });
      message.success('工单已更新');
      setEditingTicket(null);
      await loadTickets();
    } finally {
      setSaving(false);
    }
  };

  const columns = useMemo<ColumnsType<Ticket>>(() => {
    const common: ColumnsType<Ticket> = [
      {
        title: '工单号',
        dataIndex: 'ticket_no',
        width: 180,
        render: (value: string) => <Typography.Text code>{value}</Typography.Text>,
      },
      {
        title: '摘要',
        dataIndex: 'summary',
        ellipsis: true,
      },
      {
        title: '状态',
        dataIndex: 'status',
        width: 110,
        render: (value: TicketStatus) => <Tag color={STATUS_COLORS[value]}>{STATUS_LABELS[value]}</Tag>,
      },
      {
        title: '优先级',
        dataIndex: 'priority',
        width: 100,
        render: (value: string) => <Tag color={PRIORITY_COLORS[value] || 'default'}>{value}</Tag>,
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        width: 180,
        render: (value: string) => new Date(value).toLocaleString(),
      },
    ];

    if (!isStaffView) return common;

    return [
      common[0],
      {
        title: '用户',
        dataIndex: 'username',
        width: 120,
        render: (value: string | null | undefined, record) => value || `用户 ${record.user_id}`,
      },
      common[1],
      common[2],
      common[3],
      {
        title: '处理人',
        dataIndex: 'assigned_username',
        width: 120,
        render: (value: string | null | undefined) => value || '未领取',
      },
      common[4],
      {
        title: '操作',
        key: 'actions',
        width: 180,
        render: (_: unknown, record) => (
          <Space>
            {!record.assigned_to && (
              <Button size="small" type="primary" onClick={() => void handleClaim(record.id)}>
                领取
              </Button>
            )}
            {(user?.role === 'admin' || record.assigned_to === user?.id) && (
              <Button size="small" onClick={() => openEdit(record)}>
                处理
              </Button>
            )}
          </Space>
        ),
      },
    ];
  }, [isStaffView, user?.id, user?.role]);

  return (
    <Space direction="vertical" size={16} style={{ display: 'flex' }}>
      <Card bodyStyle={{ padding: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <div>
            <Typography.Title level={4} style={{ margin: 0 }}>
              {isStaffView ? '工单中心' : '我的工单'}
            </Typography.Title>
            <Typography.Text type="secondary">
              {isStaffView ? '处理转人工、高风险和异常问题工单。' : '查看转人工后的处理进度。'}
            </Typography.Text>
          </div>
          {isStaffView && (
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 160 }}
              options={[
                { label: '全部状态', value: '' },
                { label: '待处理', value: 'open' },
                { label: '处理中', value: 'processing' },
                { label: '已解决', value: 'resolved' },
                { label: '已关闭', value: 'closed' },
              ]}
            />
          )}
        </Space>
      </Card>

      <Table<Ticket>
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={items}
        pagination={false}
        expandable={{
          expandedRowRender: (record) => (
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="用户问题">{record.user_question}</Descriptions.Item>
              <Descriptions.Item label="AI 回复">{record.ai_answer}</Descriptions.Item>
              <Descriptions.Item label="分类">{record.category}</Descriptions.Item>
              <Descriptions.Item label="备注">{record.staff_note || '-'}</Descriptions.Item>
            </Descriptions>
          ),
        }}
      />

      <Modal
        open={!!editingTicket}
        title={editingTicket ? `处理工单 ${editingTicket.ticket_no}` : '处理工单'}
        onCancel={() => setEditingTicket(null)}
        onOk={() => void handleSave()}
        confirmLoading={saving}
        destroyOnClose
      >
        <Space direction="vertical" size={12} style={{ display: 'flex' }}>
          <Select<TicketStatus>
            value={nextStatus}
            onChange={setNextStatus}
            options={[
              { label: '处理中', value: 'processing' },
              { label: '已解决', value: 'resolved' },
              { label: '已关闭', value: 'closed' },
              { label: '待处理', value: 'open' },
            ]}
          />
          <Input.TextArea
            value={staffNote}
            onChange={(e) => setStaffNote(e.target.value)}
            rows={5}
            placeholder="填写处理备注"
          />
        </Space>
      </Modal>
    </Space>
  );
}
