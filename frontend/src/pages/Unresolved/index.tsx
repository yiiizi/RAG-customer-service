import { useCallback, useEffect, useMemo, useState } from 'react';
import { App, Button, Card, Descriptions, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import * as unresolvedService from '@/services/unresolvedService';
import type { UnresolvedQuestion, UnresolvedStatus } from '@/types/unresolved';

const STATUS_LABELS: Record<UnresolvedStatus, string> = {
  pending: '待处理',
  converted_to_faq: '已生成 FAQ',
  ignored: '已忽略',
  resolved: '已解决',
};

const STATUS_COLORS: Record<UnresolvedStatus, string> = {
  pending: 'gold',
  converted_to_faq: 'blue',
  ignored: 'default',
  resolved: 'green',
};

export default function UnresolvedPage() {
  const { message } = App.useApp();
  const [items, setItems] = useState<UnresolvedQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<UnresolvedStatus | ''>('pending');
  const [activeItem, setActiveItem] = useState<UnresolvedQuestion | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [form] = Form.useForm();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await unresolvedService.getUnresolvedQuestions({
        status: statusFilter,
        page,
        page_size: pageSize,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message || '加载失败';
      message.error(`加载未解决问题失败：${detail}`);
    } finally {
      setLoading(false);
    }
  }, [message, page, pageSize, statusFilter]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const updateStatus = async (item: UnresolvedQuestion, status: UnresolvedStatus) => {
    try {
      await unresolvedService.updateUnresolvedStatus(item.id, status);
      message.success('状态已更新');
      await loadData();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message || '更新失败';
      message.error(`状态更新失败：${detail}`);
    }
  };

  const openConvertModal = (item: UnresolvedQuestion) => {
    setActiveItem(item);
    form.setFieldsValue({
      question: item.question,
      answer: item.ai_answer || '',
      category: 'general',
      similar_questions: [],
    });
  };

  const handleConvert = async () => {
    if (!activeItem) return;
    setConfirmLoading(true);
    try {
      const values = await form.validateFields();
      const similarQuestions = Array.isArray(values.similar_questions)
        ? values.similar_questions.map((item: string) => item.trim()).filter(Boolean)
        : [];
      await unresolvedService.convertToFAQ(activeItem.id, {
        question: values.question?.trim(),
        answer: values.answer?.trim(),
        category: values.category || 'general',
        similar_questions: similarQuestions,
      });
      message.success('已生成 FAQ，并已写入 Redis 缓存');
      setActiveItem(null);
      form.resetFields();
      await loadData();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message || '请检查问题、答案和登录权限';
      message.error(`生成 FAQ 失败：${detail}`);
    } finally {
      setConfirmLoading(false);
    }
  };

  const columns = useMemo<ColumnsType<UnresolvedQuestion>>(() => [
    {
      title: '问题',
      dataIndex: 'question',
      ellipsis: true,
      render: (value: string) => <Typography.Text title={value}>{value}</Typography.Text>,
    },
    {
      title: '原因',
      dataIndex: 'reason',
      width: 130,
      render: (value: string) => <Tag>{value || '-'}</Tag>,
    },
    {
      title: '次数',
      dataIndex: 'frequency',
      width: 90,
      sorter: (a, b) => a.frequency - b.frequency,
      render: (value: number) => <Tag color={value > 3 ? 'red' : 'orange'}>{value}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      render: (value: UnresolvedStatus) => <Tag color={STATUS_COLORS[value]}>{STATUS_LABELS[value]}</Tag>,
    },
    {
      title: '最后出现',
      dataIndex: 'last_seen_at',
      width: 180,
      render: (value: string) => new Date(value).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 230,
      render: (_: unknown, record) => (
        <Space>
          <Button size="small" type="primary" onClick={() => openConvertModal(record)}>
            生成 FAQ
          </Button>
          <Button size="small" onClick={() => void updateStatus(record, 'resolved')}>
            解决
          </Button>
          <Button size="small" onClick={() => void updateStatus(record, 'ignored')}>
            忽略
          </Button>
        </Space>
      ),
    },
  ], [loadData]);

  return (
    <Space direction="vertical" size={16} style={{ display: 'flex' }}>
      <Card bodyStyle={{ padding: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} align="start">
          <div>
            <Typography.Title level={4} style={{ margin: 0 }}>未解决问题管理</Typography.Title>
            <Typography.Text type="secondary">
              将低置信度回答或用户负反馈直接沉淀为可命中的 FAQ，并同步写入 Redis 缓存。
            </Typography.Text>
          </div>
          <Select
            value={statusFilter}
            onChange={(value) => {
              setStatusFilter(value);
              setPage(1);
            }}
            style={{ width: 160 }}
            options={[
              { label: '待处理', value: 'pending' },
              { label: '已生成 FAQ', value: 'converted_to_faq' },
              { label: '已解决', value: 'resolved' },
              { label: '已忽略', value: 'ignored' },
              { label: '全部', value: '' },
            ]}
          />
        </Space>
      </Card>

      <Table<UnresolvedQuestion>
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={items}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (nextPage, nextPageSize) => {
            setPage(nextPage);
            setPageSize(nextPageSize);
          },
        }}
        expandable={{
          expandedRowRender: (record) => (
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="AI 回答">{record.ai_answer || '-'}</Descriptions.Item>
              <Descriptions.Item label="意图">{record.intent || '-'}</Descriptions.Item>
              <Descriptions.Item label="置信度">{record.confidence}</Descriptions.Item>
              <Descriptions.Item label="会话 ID">{record.conversation_id || '-'}</Descriptions.Item>
            </Descriptions>
          ),
        }}
      />

      <Modal
        open={!!activeItem}
        title="生成 FAQ"
        onCancel={() => setActiveItem(null)}
        onOk={() => void handleConvert()}
        confirmLoading={confirmLoading}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="question" label="问题" rules={[{ required: true, message: '请输入问题' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="answer" label="标准答案" rules={[{ required: true, message: '请输入标准答案' }]}>
            <Input.TextArea rows={5} />
          </Form.Item>
          <Form.Item name="category" label="分类" initialValue="general">
            <Select
              options={[
                { label: '通用', value: 'general' },
                { label: '账号', value: 'account' },
                { label: '售后', value: 'aftersale' },
                { label: '技术', value: 'tech' },
                { label: '商品', value: 'product' },
                { label: '订单物流', value: 'order' },
              ]}
            />
          </Form.Item>
          <Form.Item name="similar_questions" label="相似问法">
            <Select mode="tags" tokenSeparators={['\n']} placeholder="输入相似问法后按回车" />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
