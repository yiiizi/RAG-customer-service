import { useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Slider,
  Button,
  Divider,
  message,
  Radio,
  Spin,
  Typography,
} from 'antd';
import { BulbOutlined } from '@ant-design/icons';
import { useSettingsStore } from '@/stores/useSettingsStore';
import { useThemeStore } from '@/stores/useThemeStore';

export default function SettingsPage() {
  const { settings, loading, saving, fetch, save } = useSettingsStore();
  const { mode, setMode } = useThemeStore();
  const [form] = Form.useForm();

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
    const values = await form.validateFields();
    await save(values);
    message.success('配置已保存（运行时生效，重启后恢复默认值）');
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
    <div style={{ maxWidth: 720, padding: 24 }}>
      <h2 className="page-heading">系统设置</h2>

      <Form form={form} layout="vertical">
        {/* ── Theme ── */}
        <Card
          title={<><BulbOutlined style={{ marginRight: 8, color: 'var(--accent)' }} />界面主题</>}
          style={{ marginBottom: 24 }}
        >
          <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
            切换浅色 / 深色外观，设置会自动保存到本地浏览器
          </Typography.Paragraph>
          <Radio.Group
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            size="large"
          >
            <Radio.Button value="light">
              ☀️ 浅色模式
            </Radio.Button>
            <Radio.Button value="dark">
              🌙 深色模式
            </Radio.Button>
          </Radio.Group>
        </Card>

        {/* ── LLM ── */}
        <Card title="LLM 模型" style={{ marginBottom: 24 }}>
          <Form.Item name="llm_model" label="Model">
            <Input placeholder="gpt-3.5-turbo / deepseek-chat / qwen-turbo" />
          </Form.Item>
          <Form.Item name="llm_temperature" label="Temperature">
            <Slider min={0} max={2} step={0.1} marks={{ 0: '0', 0.5: '.5', 1: '1', 1.5: '1.5', 2: '2' }} />
          </Form.Item>
          <Form.Item name="llm_max_tokens" label="Max Tokens">
            <InputNumber min={256} max={32768} step={256} style={{ width: 200 }} />
          </Form.Item>
          <Typography.Text type="secondary">
            API Base 和 API Key 请在配置文件 .env 中修改，重启后生效
          </Typography.Text>
        </Card>

        {/* ── Retrieval ── */}
        <Card title="检索参数" style={{ marginBottom: 24 }}>
          <Form.Item name="dense_top_k" label="Dense Top-K (Milvus 向量检索)">
            <InputNumber min={1} max={100} step={1} style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="sparse_top_k" label="Sparse Top-K (BM25 检索)">
            <InputNumber min={1} max={100} step={1} style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="reranker_top_n" label="重排序 Top-N">
            <InputNumber min={1} max={50} step={1} style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="bm25_threshold" label="BM25 置信度阈值">
            <Slider min={0} max={1} step={0.05} marks={{ 0: '0', 0.25: '.25', 0.5: '.5', 0.75: '.75', 1: '1' }} />
          </Form.Item>
        </Card>

        {/* ── Cache ── */}
        <Card title="缓存策略">
          <Form.Item name="redis_faq_ttl" label="Redis FAQ 缓存 TTL (小时)">
            <InputNumber min={1} max={720} step={1} style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="redis_hot_threshold" label="高频阈值 (命中次数)">
            <InputNumber min={1} max={10000} step={1} style={{ width: 200 }} />
          </Form.Item>
          <Typography.Text type="secondary">
            命中次数超过阈值的 FAQ 将延长缓存至 7 天
          </Typography.Text>
        </Card>

        <Divider />

        <div style={{ display: 'flex', gap: 12 }}>
          <Button type="primary" onClick={handleSave} loading={saving}>
            保存配置
          </Button>
          <Button onClick={handleReset}>恢复默认</Button>
        </div>
      </Form>
    </div>
  );
}
