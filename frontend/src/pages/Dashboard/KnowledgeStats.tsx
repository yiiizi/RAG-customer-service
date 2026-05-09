import { Card, Descriptions, Tag } from 'antd';

interface Props {
  stats: {
    total_chunks: number;
    collection_name: string;
    dimension: number;
  };
}

export default function KnowledgeStats({ stats }: Props) {
  return (
    <Card title="知识库存储概览">
      <Descriptions column={3} bordered size="small">
        <Descriptions.Item label="Collection">
          <Tag color="blue">{stats.collection_name}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="向量维度">{stats.dimension}</Descriptions.Item>
        <Descriptions.Item label="总分块数">
          <strong>{stats.total_chunks.toLocaleString()}</strong>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
