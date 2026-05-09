import { useEffect } from 'react';
import { Row, Col, Spin } from 'antd';
import { useDashboardStore } from '@/stores/useDashboardStore';
import StatCards from './StatCards';
import QAChart from './QAChart';
import IntentPie from './IntentPie';
import FAQRanking from './FAQRanking';
import LatencyChart from './LatencyChart';
import KnowledgeStats from './KnowledgeStats';

export default function DashboardPage() {
  const { stats, loading, fetch } = useDashboardStore();

  useEffect(() => {
    fetch();
  }, [fetch]);

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
      <h2 style={{ marginBottom: 24 }}>数据大盘</h2>

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

      <Row style={{ marginTop: 24 }}>
        <Col span={24}>
          <KnowledgeStats stats={stats.milvus_stats} />
        </Col>
      </Row>
    </div>
  );
}
