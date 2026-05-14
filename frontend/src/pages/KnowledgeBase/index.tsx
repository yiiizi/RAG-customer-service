import { useEffect } from 'react';
import { Tabs } from 'antd';
import DocUpload from './DocUpload';
import DocList from './DocList';
import { useKnowledgeStore } from '@/stores/useKnowledgeStore';

export default function KnowledgeBasePage() {
  const { fetchList, fetchStats } = useKnowledgeStore();

  useEffect(() => {
    fetchList();
    fetchStats();
  }, [fetchList, fetchStats]);

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ marginBottom: 16, color: 'var(--text-primary)' }}>知识库管理</h2>
      <Tabs
        defaultActiveKey="list"
        items={[
          {
            key: 'list',
            label: '文档列表',
            children: <DocList />,
          },
          {
            key: 'upload',
            label: '上传文档',
            children: <DocUpload />,
          },
        ]}
      />
    </div>
  );
}
