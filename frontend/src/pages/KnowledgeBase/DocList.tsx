import { useState } from 'react';
import { Table, Tag, Button, Popconfirm, Space, Input, Select } from 'antd';
import { ReloadOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useKnowledgeStore } from '@/stores/useKnowledgeStore';
import { FILE_TYPE_ICONS } from '@/utils/constants';
import DocDetail from './DocDetail';

export default function DocList() {
  const { documents, total, loading, fetchList, deleteFile, reindexFile } = useKnowledgeStore();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [detailDrawer, setDetailDrawer] = useState<string | null>(null);

  const filtered = documents.filter((d) => {
    if (search && !d.file_name.toLowerCase().includes(search.toLowerCase())) return false;
    if (typeFilter && d.file_type !== typeFilter) return false;
    return true;
  });

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索文件名..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 280 }}
          allowClear
        />
        <Select
          value={typeFilter}
          onChange={setTypeFilter}
          placeholder="文件类型"
          style={{ width: 140 }}
          allowClear
          options={[
            { label: 'PDF', value: '.pdf' },
            { label: 'Word', value: '.docx' },
            { label: 'Excel', value: '.xlsx' },
            { label: 'Markdown', value: '.md' },
            { label: 'HTML', value: '.html' },
          ]}
        />
        <Button icon={<ReloadOutlined />} onClick={fetchList}>
          刷新
        </Button>
      </div>

      <Table
        dataSource={filtered}
        rowKey="file_name"
        loading={loading}
        pagination={{ total: filtered.length, pageSize: 20, showSizeChanger: true }}
        columns={[
          {
            title: '文件名',
            dataIndex: 'file_name',
            render: (name: string, record) => (
              <span style={{ cursor: 'pointer', color: '#1677ff' }} onClick={() => setDetailDrawer(name)}>
                {FILE_TYPE_ICONS[record.file_type] || '📄'} {name}
              </span>
            ),
          },
          { title: '类型', dataIndex: 'file_type', width: 80 },
          {
            title: '状态',
            dataIndex: 'status',
            width: 100,
            render: (status: string) => {
              const color = status === 'indexed' ? 'green' : status === 'indexing' ? 'processing' : 'error';
              const label = status === 'indexed' ? '已索引' : status === 'indexing' ? '索引中' : '错误';
              return <Tag color={color}>{label}</Tag>;
            },
          },
          { title: '分块数', dataIndex: 'chunk_count', width: 80 },
          {
            title: '操作',
            width: 160,
            render: (_: unknown, record) => (
              <Space>
                <Button
                  type="link"
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => setDetailDrawer(record.file_name)}
                >
                  详情
                </Button>
                <Popconfirm title="重新索引此文件？" onConfirm={() => reindexFile(record.file_name)}>
                  <Button type="link" size="small" icon={<ReloadOutlined />}>
                    重建
                  </Button>
                </Popconfirm>
                <Popconfirm title="确定删除？" onConfirm={() => deleteFile(record.file_name)}>
                  <Button type="link" size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      {detailDrawer && (
        <DocDetail fileName={detailDrawer} onClose={() => setDetailDrawer(null)} />
      )}
    </div>
  );
}
