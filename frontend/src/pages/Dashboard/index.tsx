import { useEffect } from 'react';
import { Card, Col, Progress, Row, Segmented, Spin, Table, Tag, Typography } from 'antd';
import { useDashboardStore } from '@/stores/useDashboardStore';
import type { DashboardRange } from '@/services/dashboardService';
import StatCards from './StatCards';
import QAChart from './QAChart';
import IntentPie from './IntentPie';
import FAQRanking from './FAQRanking';
import LatencyChart from './LatencyChart';
import KnowledgeStats from './KnowledgeStats';

export default function DashboardPage() {
  const { stats, loading, range, setRange, fetch } = useDashboardStore();

  useEffect(() => {
    void fetch();
  }, [fetch]);

  const handleRangeChange = (value: string | number) => {
    const next = value as DashboardRange;
    setRange(next);
    void fetch(next);
  };

  if (loading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: 120 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, marginBottom: 24 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          运营看板
        </Typography.Title>
        <Segmented
          value={range}
          onChange={handleRangeChange}
          options={[
            { label: '今日', value: 'today' },
            { label: '近 7 天', value: '7d' },
            { label: '近 30 天', value: '30d' },
          ]}
        />
      </div>

      <StatCards stats={stats} />

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={14}>
          <QAChart data={stats.daily_trend} />
        </Col>
        <Col xs={24} lg={10}>
          <IntentPie data={stats.intent_distribution} />
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={14}>
          <FAQRanking data={stats.top_faqs} />
        </Col>
        <Col xs={24} lg={10}>
          <LatencyChart avgLatency={stats.avg_latency_ms} hitRate={stats.hit_rate} />
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={14}>
          <Card title="高频未解决问题">
            <Table
              rowKey="id"
              size="small"
              pagination={false}
              dataSource={stats.top_unresolved}
              columns={[
                { title: '问题', dataIndex: 'question', ellipsis: true },
                {
                  title: '频次',
                  dataIndex: 'frequency',
                  width: 80,
                  render: (value: number) => <Tag color="orange">{value}</Tag>,
                },
                {
                  title: '状态',
                  dataIndex: 'status',
                  width: 120,
                  render: (value: string) => <Tag>{value}</Tag>,
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="服务闭环">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18, padding: '8px 0' }}>
              <div>
                <Typography.Text strong>工单解决率</Typography.Text>
                <Progress percent={Math.round(stats.ticket_resolution_rate * 100)} style={{ marginTop: 8 }} />
              </div>
              <div>
                <Typography.Text strong>没帮助率</Typography.Text>
                <Progress
                  percent={Math.round(stats.unhelpful_rate * 100)}
                  status={stats.unhelpful_rate > 0.3 ? 'exception' : 'normal'}
                  style={{ marginTop: 8 }}
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row style={{ marginTop: 24 }}>
        <Col span={24}>
          <KnowledgeStats stats={stats.milvus_stats} />
        </Col>
      </Row>
    </div>
  );
}
