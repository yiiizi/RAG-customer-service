import { useEffect, useRef } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Slider,
  Button,
  Divider,
  App,
  Radio,
  Spin,
  Typography,
  Row,
  Col,
} from 'antd';
import { BulbOutlined, RobotOutlined, SearchOutlined, ThunderboltOutlined, DatabaseOutlined, CloudOutlined } from '@ant-design/icons';
import { useSettingsStore } from '@/stores/useSettingsStore';
import { useThemeStore } from '@/stores/useThemeStore';
import ModelConfigPage from '@/pages/ModelConfig';

export default function SettingsPage() {
  const { settings, loading, saving, fetch, save } = useSettingsStore();
  const { mode, setMode } = useThemeStore();
  const [form] = Form.useForm();
  const bottomRef = useRef<HTMLDivElement>(null);
  const { message } = App.useApp();

  useEffect(() => {
    fetch();
  }, [fetch]);

  useEffect(() => {
    if (settings) {
      form.setFieldsValue({
        llm_model: settings.llm.model,
        llm_temperature: settings.llm.temperature,
        llm_max_tokens: settings.llm.max_tokens,
        dense_top_k: settings.retrieval.dense_top_k,
        sparse_top_k: settings.retrieval.sparse_top_k,
        reranker_top_n: settings.retrieval.reranker_top_n,
        bm25_threshold: settings.retrieval.bm25_threshold,
        redis_faq_ttl: settings.cache.redis_faq_ttl_hours,
        redis_hot_threshold: settings.cache.redis_hot_threshold,
      });
    }
  }, [settings, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await save(values);
      message.success('配置已保存（运行时生效，重启后恢复默认值）');
      await fetch();
    } catch (error: any) {
      console.error('[Settings] Save failed:', error);
      if (error?.errorFields) {
        message.warning('请检查表单中的错误项');
      } else if (error?.response) {
        message.error(error.response.data?.detail || '保存失败，服务器错误');
      } else {
        message.error('保存失败，请稍后重试');
      }
    }
  };

  const handleReset = () => {
    form.resetFields();
    if (settings) {
      form.setFieldsValue({
        llm_model: settings.llm.model,
        llm_temperature: settings.llm.temperature,
        llm_max_tokens: settings.llm.max_tokens,
        dense_top_k: settings.retrieval.dense_top_k,
        sparse_top_k: settings.retrieval.sparse_top_k,
        reranker_top_n: settings.retrieval.reranker_top_n,
        bm25_threshold: settings.retrieval.bm25_threshold,
        redis_faq_ttl: settings.cache.redis_faq_ttl_hours,
        redis_hot_threshold: settings.cache.redis_hot_threshold,
      });
    }
    message.success('已恢复默认值');
  };

  if (loading && !settings) {
    return (
      <div style={{ textAlign: 'center', padding: 120 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1100, padding: 24 }}>
      <h2 className="page-heading">系统设置</h2>

      <Form form={form} layout="vertical">
        {/* ── Theme ── */}
        <Card
          title={<><BulbOutlined style={{ marginRight: 8, color: 'var(--accent)' }} />界面主题</>}
          style={{ marginBottom: 20, borderRadius: 12 }}
        >
          <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
            切换浅色 / 深色外观
          </Typography.Paragraph>
          <Radio.Group
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            size="large"
          >
            <Radio.Button value="light">☀️ 浅色</Radio.Button>
            <Radio.Button value="dark">🌙 深色</Radio.Button>
            <Radio.Button value="system">💻 跟随系统</Radio.Button>
          </Radio.Group>
        </Card>

        {/* ── LLM ── */}
        <Card
          title={<><ThunderboltOutlined style={{ marginRight: 8, color: 'var(--accent)' }} />LLM 模型</>}
          style={{ marginBottom: 20, borderRadius: 12 }}
        >
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item name="llm_model" label="模型名称">
                <Input placeholder="gpt-3.5-turbo / deepseek-chat / qwen-turbo" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="llm_max_tokens" label="最大 Token 数">
                <InputNumber min={256} max={32768} step={256} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="llm_temperature" label="温度 (Temperature)">
            <Slider min={0} max={2} step={0.1} marks={{ 0: '0', 0.5: '.5', 1: '1', 1.5: '1.5', 2: '2' }} />
          </Form.Item>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            API Base 和 API Key 请在配置文件 .env 中修改
          </Typography.Text>
        </Card>

        {/* ── Retrieval ── */}
        <Card
          title={<><DatabaseOutlined style={{ marginRight: 8, color: 'var(--accent)' }} />检索参数</>}
          style={{ marginBottom: 20, borderRadius: 12 }}
        >
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="dense_top_k" label="稠密检索 Top-K">
                <InputNumber min={1} max={100} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sparse_top_k" label="稀疏检索 Top-K">
                <InputNumber min={1} max={100} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="reranker_top_n" label="重排序 Top-N">
                <InputNumber min={1} max={50} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="bm25_threshold" label="BM25 置信度阈值">
            <Slider min={0} max={1} step={0.05} marks={{ 0: '0', 0.25: '.25', 0.5: '.5', 0.75: '.75', 1: '1' }} />
          </Form.Item>
        </Card>

        {/* ── Cache ── */}
        <Card
          title={<><CloudOutlined style={{ marginRight: 8, color: 'var(--accent)' }} />缓存策略</>}
          style={{ marginBottom: 20, borderRadius: 12 }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="redis_faq_ttl" label="FAQ 缓存 TTL (小时)">
                <InputNumber min={1} max={720} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="redis_hot_threshold" label="高频阈值 (命中次数)">
                <InputNumber min={1} max={10000} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            命中次数超过阈值的 FAQ 将延长缓存至 7 天
          </Typography.Text>
        </Card>
      </Form>

      {/* ── 模型配置 ── */}
      <Card
        title={<><RobotOutlined style={{ marginRight: 8, color: 'var(--accent)' }} />模型配置</>}
        style={{ marginTop: 8, borderRadius: 12 }}
        styles={{ body: { padding: 0 } }}
      >
        <ModelConfigPage />
      </Card>

      <Divider />

      {/* Fixed action buttons */}
      <div ref={bottomRef} style={{ display: 'flex', gap: 12, paddingTop: 8 }}>
        <Button type="primary" onClick={handleSave} loading={saving} style={{ borderRadius: 8 }}>
          保存配置
        </Button>
        <Button onClick={handleReset} style={{ borderRadius: 8 }}>恢复默认</Button>
      </div>
    </div>
  );
}
