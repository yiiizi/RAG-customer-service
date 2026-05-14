import { Card, Col, Row, Statistic } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CustomerServiceOutlined,
  FileTextOutlined,
  LikeOutlined,
  QuestionCircleOutlined,
  SyncOutlined,
  WarningOutlined,
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
      title: '问答总量',
      value: stats.total_queries,
      icon: <QuestionCircleOutlined />,
      color: '#1677ff',
      formatter: (v: number) => <CountUp end={v} duration={1.2} separator="," />,
    },
    {
      title: 'FAQ 命中率',
      value: stats.hit_rate,
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      formatter: () => formatPercent(stats.hit_rate),
    },
    {
      title: '平均响应',
      value: stats.avg_latency_ms,
      icon: <ClockCircleOutlined />,
      color: '#fa8c16',
      formatter: () => formatLatency(stats.avg_latency_ms),
    },
    {
      title: '知识片段',
      value: stats.milvus_stats?.total_chunks ?? 0,
      icon: <FileTextOutlined />,
      color: '#722ed1',
      formatter: (v: number) => <CountUp end={v} duration={1.2} separator="," />,
    },
    {
      title: '有帮助率',
      value: stats.helpful_rate,
      icon: <LikeOutlined />,
      color: '#13c2c2',
      formatter: () => formatPercent(stats.helpful_rate),
    },
    {
      title: '未解决问题',
      value: stats.unresolved_count,
      icon: <WarningOutlined />,
      color: '#f5222d',
      formatter: (v: number) => <CountUp end={v} duration={1.2} separator="," />,
    },
    {
      title: '转人工率',
      value: stats.handoff_rate,
      icon: <CustomerServiceOutlined />,
      color: '#eb2f96',
      formatter: () => formatPercent(stats.handoff_rate),
    },
    {
      title: 'FAQ 转化数',
      value: stats.faq_conversion_count,
      icon: <SyncOutlined />,
      color: '#2f54eb',
      formatter: (v: number) => <CountUp end={v} duration={1.2} separator="," />,
    },
  ];

  return (
    <Row gutter={[16, 16]}>
      {items.map((item) => (
        <Col xs={24} sm={12} lg={6} key={item.title}>
          <Card>
            <Statistic
              title={item.title}
              value={item.value}
              formatter={() => item.formatter(Number(item.value))}
              prefix={<span style={{ color: item.color, fontSize: 22, marginRight: 8 }}>{item.icon}</span>}
            />
          </Card>
        </Col>
      ))}
    </Row>
  );
}
