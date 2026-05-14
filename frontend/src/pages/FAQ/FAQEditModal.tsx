import { useState, cloneElement, type ReactElement } from 'react';
import { Modal, Form, Input, Select, App } from 'antd';
import { useFAQStore } from '@/stores/useFAQStore';

interface Props {
  mode: 'create' | 'edit';
  record?: {
    id: string;
    question: string;
    answer: string;
    category: string;
    status?: string;
    priority?: number;
    similar_questions?: string[];
  };
  children: ReactElement;
}

export default function FAQEditModal({ mode, record, children }: Props) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const { create, update } = useFAQStore();
  const [loading, setLoading] = useState(false);
  const { message } = App.useApp();

  const handleOk = async () => {
    const values = await form.validateFields();
    setLoading(true);
    try {
      if (mode === 'create') {
        await create(values);
        message.success('创建成功');
      } else if (record) {
        await update(record.id, values);
        message.success('更新成功');
      }
      setOpen(false);
      form.resetFields();
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {cloneElement(children, {
        onClick: () => {
          if (mode === 'edit' && record) {
            form.setFieldsValue(record);
          }
          setOpen(true);
        },
      })}
      <Modal
        title={mode === 'create' ? '新增 FAQ' : '编辑 FAQ'}
        open={open}
        onOk={handleOk}
        onCancel={() => {
          setOpen(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="question" label="问题" rules={[{ required: true, message: '请输入问题' }]}>
            <Input placeholder="常见问题..." />
          </Form.Item>
          <Form.Item name="answer" label="回答" rules={[{ required: true, message: '请输入回答' }]}>
            <Input.TextArea rows={4} placeholder="标准回答..." />
          </Form.Item>
          <Form.Item name="category" label="分类" initialValue="general">
            <Select
              options={[
                { label: '通用', value: 'general' },
                { label: '账户', value: 'account' },
                { label: '售后', value: 'aftersale' },
                { label: '技术', value: 'tech' },
              ]}
            />
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select
              options={[
                { label: '草稿', value: 'draft' },
                { label: '已发布', value: 'active' },
                { label: '已停用', value: 'inactive' },
                { label: '已驳回', value: 'rejected' },
              ]}
            />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={0}>
            <Input type="number" min={0} max={100} />
          </Form.Item>
          <Form.Item name="similar_questions" label="相似问">
            <Select mode="tags" tokenSeparators={['\n']} placeholder="输入相似问后回车" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
