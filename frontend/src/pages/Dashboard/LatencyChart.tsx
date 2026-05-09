import { Card, Progress, Typography } from 'antd';

interface Props {
  avgLatency: number;
  hitRate: number;
}

export default function LatencyChart({ avgLatency, hitRate }: Props) {
  const latencyScore = Math.max(0, 100 - (avgLatency / 10));
  const hitRatePct = Math.round(hitRate * 100);

  return (
    <Card title="性能指标">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24, padding: '20px 0' }}>
        <div>
          <Typography.Text strong>平均响应延迟</Typography.Text>
          <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
            {avgLatency.toFixed(0)} ms
          </Typography.Text>
          <Progress
            percent={Math.round(latencyScore)}
            status={avgLatency < 500 ? 'success' : avgLatency < 1000 ? 'normal' : 'exception'}
            format={() => `${avgLatency.toFixed(0)}ms`}
            style={{ marginTop: 8 }}
          />
        </div>
        <div>
          <Typography.Text strong>FAQ 缓存命中率</Typography.Text>
          <Progress
            percent={hitRatePct}
            status={hitRatePct > 70 ? 'success' : 'normal'}
            style={{ marginTop: 8 }}
          />
        </div>
      </div>
    </Card>
  );
}
