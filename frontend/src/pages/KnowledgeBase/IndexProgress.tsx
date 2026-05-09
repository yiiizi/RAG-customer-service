import { Progress, Typography } from 'antd';

interface Props {
  totalChunks: number;
  processedChunks: number;
}

export default function IndexProgress({ totalChunks, processedChunks }: Props) {
  const pct = totalChunks > 0 ? Math.round((processedChunks / totalChunks) * 100) : 0;

  return (
    <div style={{ padding: 16 }}>
      <Typography.Text>索引进度</Typography.Text>
      <Progress percent={pct} status={pct === 100 ? 'success' : 'active'} />
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {processedChunks} / {totalChunks} chunks
      </Typography.Text>
    </div>
  );
}
