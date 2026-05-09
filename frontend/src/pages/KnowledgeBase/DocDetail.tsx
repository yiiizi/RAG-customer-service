import { useState, useEffect } from 'react';
import { Modal, Tree, Descriptions, Tag, Spin, Typography } from 'antd';
import { FolderOutlined, FileTextOutlined } from '@ant-design/icons';
import { useKnowledgeStore } from '@/stores/useKnowledgeStore';
import * as api from '@/services/knowledgeService';
import { formatDate, formatUnixTime } from '@/utils/format';

interface Props {
  fileName: string;
  onClose: () => void;
}

export default function DocDetail({ fileName, onClose }: Props) {
  const { documents } = useKnowledgeStore();
  const doc = documents.find((d) => d.file_name === fileName);
  const [chunkData, setChunkData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getFileChunks(fileName).then(setChunkData).finally(() => setLoading(false));
  }, [fileName]);

  const treeData = chunkData?.parents?.map((p: any, pi: number) => ({
    title: (
      <Typography.Text strong style={{ fontSize: 12 }}>
        父块 #{pi + 1}（{p.parent_text.length > 80 ? p.parent_text.slice(0, 80) + '...' : p.parent_text}）
      </Typography.Text>
    ),
    key: p.parent_id,
    icon: <FolderOutlined />,
    children: p.children?.map((c: any, ci: number) => ({
      title: (
        <div style={{ fontSize: 11, lineHeight: 1.6 }}>
          <Typography.Text type="secondary">
            子块 #{c.chunk_index}
            {c.created_at ? ` · ${formatUnixTime(c.created_at)}` : ''}
          </Typography.Text>
          <div style={{ color: 'var(--text-secondary)', marginTop: 2, maxHeight: 120, overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', border: '1px solid var(--border-subtle)', borderRadius: 4, padding: '4px 8px', background: 'var(--surface-raised)' }}>
            {c.text}
          </div>
        </div>
      ),
      key: c.id,
      icon: <FileTextOutlined />,
    })),
  })) || [];

  return (
    <Modal
      title={`文档详情 - ${fileName}`}
      open
      onCancel={onClose}
      width={800}
      footer={null}
    >
      <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
        <Descriptions.Item label="文件名">{doc?.file_name || fileName}</Descriptions.Item>
        <Descriptions.Item label="类型">{doc?.file_type || '-'}</Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={doc?.status === 'indexed' ? 'green' : doc?.status === 'indexing' ? 'processing' : 'error'}>
            {doc?.status === 'indexed' ? '已索引' : doc?.status || '-'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="分块数">{chunkData?.chunk_count ?? doc?.chunk_count ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="创建时间">{doc?.created_at ? formatDate(doc.created_at) : '-'}</Descriptions.Item>
        <Descriptions.Item label="父块数">{chunkData?.parent_count ?? '-'}</Descriptions.Item>
      </Descriptions>

      <Typography.Title level={5} style={{ marginTop: 16 }}>
        <FileTextOutlined /> 父子分块结构
      </Typography.Title>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
      ) : treeData.length > 0 ? (
        <div style={{ maxHeight: 400, overflow: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12 }}>
          <Tree treeData={treeData} defaultExpandAll showLine={{ showLeafIcon: false }} />
        </div>
      ) : (
        <Typography.Text type="secondary">暂无法加载分块详情</Typography.Text>
      )}
    </Modal>
  );
}
