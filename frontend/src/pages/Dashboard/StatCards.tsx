import { Card, Row, Col, Statistic } from 'antd';
import {
  QuestionCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import CountUp from 'react-countup';
import type { DashboardStats } from '@/types/dashboard';
import { formatLatency, formatPercent } from '@/utils/format';

interface Props {
  stats: DashboardStats;
}

export default function StatCards({ stats }: Props) {
  const items = [
    {
      title: '总问答数',
      value: stats.total_queries,
      icon: <QuestionCircleOutlined />,
      color: '#1677ff',
      formatter: (v: number) => <CountUp end={v} duration={2} separator="," />,
    },
    {
      title: '命中率',
      value: stats.hit_rate,
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      formatter: (_: number) => formatPercent(stats.hit_rate),
    },
    {
      title: '平均延迟',
      value: stats.avg_latency_ms,
      icon: <ClockCircleOutlined />,
      color: '#fa8c16',
      formatter: (_: number) => formatLatency(stats.avg_latency_ms),
    },
    {
      title: '知识库分块',
      value: stats.milvus_stats?.total_chunks ?? 0,
      icon: <FileTextOutlined />,
      color: '#722ed1',
      formatter: (v: number) => <CountUp end={v} duration={2} separator="," />,
    },
  ];

  return (
    <Row gutter={[24, 16]}>
      {items.map((item) => (
        <Col xs={24} sm={12} lg={6} key={item.title}>
          <Card>
            <Statistic
              title={item.title}
              value={item.value}
              formatter={() => item.formatter(item.value)}
              prefix={
                <span style={{ color: item.color, fontSize: 24, marginRight: 8 }}>
                  {item.icon}
                </span>
              }
            />
          </Card>
        </Col>
      ))}
    </Row>
  );
}
