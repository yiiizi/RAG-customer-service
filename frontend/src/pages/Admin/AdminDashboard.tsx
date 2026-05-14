import { useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin } from 'antd';
import {
  TeamOutlined,
  DatabaseOutlined,
  QuestionCircleOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import { useDashboardStore } from '@/stores/useDashboardStore';

export default function AdminDashboardPage() {
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

  return (
    <div>
      <h2 style={{ marginBottom: 24, color: 'var(--text-primary)' }}>管理后台首页</h2>

      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总查询量"
              value={stats?.total_queries || 0}
              prefix={<MessageOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="知识库文档"
              value={stats?.milvus_stats?.total_chunks || 0}
              prefix={<DatabaseOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="FAQ 数量"
              value={stats?.top_faqs?.length || 0}
              prefix={<QuestionCircleOutlined style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均响应"
              value={stats?.avg_latency_ms || 0}
              suffix="ms"
              prefix={<TeamOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="系统说明">
            <p style={{ color: 'var(--text-primary)' }}>管理后台提供以下功能：</p>
            <ul>
              <li style={{ color: 'var(--text-secondary)' }}>用户管理：查看、编辑用户角色、启用/禁用账号</li>
              <li style={{ color: 'var(--text-secondary)' }}>知识库管理：上传文档、管理知识库内容</li>
              <li style={{ color: 'var(--text-secondary)' }}>FAQ 管理：维护高频问答对、批量导入</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
