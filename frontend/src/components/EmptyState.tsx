import { Empty } from 'antd';

interface Props {
  description?: string;
}

export default function EmptyState({ description = '暂无数据' }: Props) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 80 }}>
      <Empty description={description} />
    </div>
  );
}
