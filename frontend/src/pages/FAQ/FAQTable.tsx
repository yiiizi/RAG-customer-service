import { useEffect } from 'react';
import {
  Table,
  Tag,
  Button,
  Space,
  Input,
  Select,
  Popconfirm,
  message,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useFAQStore } from '@/stores/useFAQStore';
import { useDebounceFn } from 'ahooks';
import { formatDate } from '@/utils/format';
import FAQEditModal from './FAQEditModal';

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
    () => fetchList(),
    { wait: 300 }
  );

  useEffect(() => {
    debouncedSearch();
  }, [keyword, category, page, debouncedSearch]);

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
            render: (text: string) => (
              <span title={text}>{text}</span>
            ),
          },
          {
            title: '分类',
            dataIndex: 'category',
            width: 100,
            render: (cat: string) => <Tag>{cat}</Tag>,
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
                <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
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
