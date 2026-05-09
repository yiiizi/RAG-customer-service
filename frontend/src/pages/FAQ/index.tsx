import { useEffect } from 'react';
import { Card, Tabs } from 'antd';
import FAQTable from './FAQTable';
import FAQImport from './FAQImport';
import { useFAQStore } from '@/stores/useFAQStore';

export default function FAQPage() {
  const { fetchList } = useFAQStore();

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ marginBottom: 16 }}>FAQ 高频问答管理</h2>
      <Tabs
        defaultActiveKey="list"
        items={[
          { key: 'list', label: '问答列表', children: <FAQTable /> },
          { key: 'import', label: '批量导入', children: <FAQImport /> },
        ]}
      />
    </div>
  );
}
