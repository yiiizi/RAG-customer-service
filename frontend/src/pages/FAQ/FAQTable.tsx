import { useEffect } from 'react';
import {
  Button,
  Input,
  message,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { useDebounceFn } from 'ahooks';
import FAQEditModal from './FAQEditModal';
import { useFAQStore } from '@/stores/useFAQStore';
import { formatDate } from '@/utils/format';

const STATUS_META: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'gold' },
  active: { label: '已发布', color: 'green' },
  inactive: { label: '已停用', color: 'default' },
  rejected: { label: '已驳回', color: 'red' },
};

export default function FAQTable() {
  const {
    items,
    total,
    loading,
    keyword,
    category,
    page,
    pageSize,
    fetchList,
    setKeyword,
    setCategory,
    setPage,
    remove,
  } = useFAQStore();

  const { run: debouncedSearch } = useDebounceFn(
    () => { void fetchList(); },
    { wait: 300 }
  );

  useEffect(() => {
    debouncedSearch();
  }, [keyword, category, page, pageSize, debouncedSearch]);

  const handleDelete = async (id: string) => {
    await remove(id);
    message.success('已删除');
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索问题..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ width: 280 }}
          allowClear
        />
        <Select
          value={category}
          onChange={setCategory}
          placeholder="全部分类"
          style={{ width: 140 }}
          allowClear
          options={[
            { label: '通用', value: 'general' },
            { label: '账户', value: 'account' },
            { label: '售后', value: 'aftersale' },
            { label: '技术', value: 'tech' },
          ]}
        />
        <FAQEditModal mode="create">
          <Button type="primary" icon={<PlusOutlined />}>
            新增 FAQ
          </Button>
        </FAQEditModal>
      </div>

      <Table
        dataSource={items}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p, ps) => {
            setPage(p);
            useFAQStore.getState().setPageSize(ps);
          },
          showTotal: (t) => `共 ${t} 条`,
        }}
        columns={[
          {
            title: '问题',
            dataIndex: 'question',
            ellipsis: true,
            render: (text: string) => <span title={text}>{text}</span>,
          },
          {
            title: '分类',
            dataIndex: 'category',
            width: 100,
            render: (cat: string) => <Tag>{cat}</Tag>,
          },
          {
            title: '状态',
            dataIndex: 'status',
            width: 100,
            render: (status: string) => {
              const meta = STATUS_META[status] || STATUS_META.inactive;
              return <Tag color={meta.color}>{meta.label}</Tag>;
            },
          },
          {
            title: '优先级',
            dataIndex: 'priority',
            width: 90,
            render: (priority: number) => <Tag>{priority ?? 0}</Tag>,
          },
          {
            title: '命中次数',
            dataIndex: 'frequency',
            width: 100,
            sorter: (a: any, b: any) => a.frequency - b.frequency,
            render: (freq: number) => (
              <Tag color={freq > 500 ? 'red' : freq > 100 ? 'orange' : 'default'}>
                {freq}
              </Tag>
            ),
          },
          {
            title: '更新时间',
            dataIndex: 'updated_at',
            width: 160,
            render: (v: string) => formatDate(v),
          },
          {
            title: '操作',
            width: 120,
            render: (_: unknown, record) => (
              <Space>
                <FAQEditModal mode="edit" record={record}>
                  <Button type="link" size="small" icon={<EditOutlined />} />
                </FAQEditModal>
                <Popconfirm title="确定删除？" onConfirm={() => void handleDelete(record.id)}>
                  <Button type="link" size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
    </div>
  );
}
