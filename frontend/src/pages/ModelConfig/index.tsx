/**
 * 模型配置页面。
 */

import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, App, Space, Switch, InputNumber, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, StarOutlined, StarFilled } from '@ant-design/icons';
import { useModelConfigStore } from '@/stores/useModelConfigStore';

const ModelConfigPage = () => {
  const { configs, loading, loadConfigs, addConfig, updateConfig, deleteConfig, setDefaultConfig } = useModelConfigStore();
  const { message } = App.useApp();

  const [modalVisible, setModalVisible] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadConfigs().catch(() => { /* ignore */ });
  }, [loadConfigs]);

  useEffect(() => {
    if (modalVisible && editingRecord) {
      form.setFieldsValue({
        provider: editingRecord.provider,
        model_name: editingRecord.model_name,
        base_url: editingRecord.base_url,
        temperature: editingRecord.temperature,
        max_tokens: editingRecord.max_tokens,
        is_default: editingRecord.is_default,
      });
    }
  }, [modalVisible, editingRecord, form]);

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: any) => {
    setEditingRecord(record);
    form.resetFields();
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteConfig(id);
      message.success('删除成功');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleSetDefault = async (id: number) => {
    try {
      await setDefaultConfig(id);
      message.success('设置默认成功');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '设置默认失败');
    }
  };

  const handleModalOk = async () => {
    const values = await form.validateFields();
    setModalLoading(true);
    try {
      if (editingRecord) {
        const payload = { ...values };
        if (!payload.api_key) {
          delete payload.api_key;
        }
        await updateConfig(editingRecord.id, payload);
        message.success('更新成功');
      } else {
        await addConfig(values);
        message.success('添加成功');
      }

      setModalVisible(false);
      form.resetFields();
      setEditingRecord(null);
    } catch (error: any) {
      const msg = error?.response?.data?.detail;
      if (Array.isArray(msg)) {
        message.error(msg.map((m: any) => m.msg || String(m)).join('; ') || '操作失败');
      } else {
        message.error(msg || '操作失败');
      }
    } finally {
      setModalLoading(false);
    }
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    form.resetFields();
    setEditingRecord(null);
  };

  const columns = [
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (text: string) => <span style={{ textTransform: 'capitalize' }}>{text}</span>,
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
    },
    {
      title: 'API 密钥',
      dataIndex: 'api_key_masked',
      key: 'api_key_masked',
    },
    {
      title: '基础 URL',
      dataIndex: 'base_url',
      key: 'base_url',
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
    },
    {
      title: '最大 Token',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
    },
    {
      title: '默认',
      dataIndex: 'is_default',
      key: 'is_default',
      render: (isDefault: boolean, record: any) => (
        <span>
          {isDefault ? <StarFilled style={{ color: '#FBBF24' }} /> : <StarOutlined style={{ color: 'var(--text-muted)' }} />}
          {!isDefault && (
            <a onClick={() => handleSetDefault(record.id)} style={{ marginLeft: 8, color: 'var(--accent)' }}>
              设为默认
            </a>
          )}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => text ? new Date(text).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: any) => (
        <Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
            style={{ borderRadius: 6 }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此配置吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="primary"
              danger
              icon={<DeleteOutlined />}
              size="small"
              style={{ borderRadius: 6 }}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  
  return (
    <div style={{ padding: '16px 20px' }}>
      {/* Add button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: 12 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
          style={{ borderRadius: 8 }}
        >
          添加配置
        </Button>
      </div>
      
      <Table
        dataSource={configs}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={false}
        size="middle"
      />
      
      <Modal
        title={editingRecord ? '编辑配置' : '添加配置'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={modalLoading}
        width={560}
        style={{ top: 40 }}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            provider: 'openai',
            temperature: 0.7,
            max_tokens: 4096,
            is_default: false,
          }}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true, message: '请选择提供商！' }]}
          >
            <Select>
              <Select.Option value="openai">OpenAI</Select.Option>
              <Select.Option value="deepseek">DeepSeek</Select.Option>
              <Select.Option value="claude">Claude</Select.Option>
              <Select.Option value="gemini">Gemini</Select.Option>
              <Select.Option value="qwen">Qwen</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称！' }]}
          >
            <Input placeholder="例如：gpt-3.5-turbo" />
          </Form.Item>
          
          <Form.Item
            name="api_key"
            label="API 密钥"
            rules={[{ required: !editingRecord, message: '请输入 API 密钥！' }]}
          >
            <Input.Password placeholder={editingRecord ? '留空则保留原密钥' : '请输入 API 密钥'} />
          </Form.Item>
          
          <Form.Item
            name="base_url"
            label="基础 URL（可选）"
          >
            <Input placeholder="例如：https://api.openai.com/v1" />
          </Form.Item>
          
          <Form.Item
            name="temperature"
            label="温度"
            rules={[{ required: true, message: '请输入温度！' }]}
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="max_tokens"
            label="最大 Token"
            rules={[{ required: true, message: '请输入最大 Token 数！' }]}
          >
            <InputNumber min={1} max={32768} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="is_default"
            label="设为默认"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ModelConfigPage;
