import { useState } from 'react';
import { Upload, Button, App, Table, Card, Typography, Alert } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { FAQBatchImportResponse } from '@/types/faq';
import * as api from '@/services/faqService';
import * as XLSX from 'xlsx';
import Papa from 'papaparse';

export default function FAQImport() {
  const [result, setResult] = useState<FAQBatchImportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const { message } = App.useApp();

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      // Parse CSV/Excel client-side
      const data = await parseFile(file);
      const res = await api.batchImportFAQ({ items: data });
      setResult(res);
      if (res.errors.length === 0) {
        message.success(`成功导入 ${res.imported} 条`);
      } else {
        message.warning(`导入 ${res.imported} 条，${res.skipped} 条失败`);
      }
    } catch (err: any) {
      message.error('导入失败: ' + (err.message || '未知错误'));
    } finally {
      setLoading(false);
    }
    return false; // prevent default upload
  };

  return (
    <Card>
      <Typography.Paragraph>
        支持 CSV 或 Excel 文件，表头需包含: <code>question</code>, <code>answer</code>, <code>category</code> (可选)
      </Typography.Paragraph>

      <Upload
        beforeUpload={handleUpload}
        showUploadList={false}
        accept=".csv,.xlsx"
      >
        <Button icon={<UploadOutlined />} loading={loading}>
          选择文件并导入
        </Button>
      </Upload>

      {result && (
        <div style={{ marginTop: 16 }}>
          <Alert
            type={result.errors.length > 0 ? 'warning' : 'success'}
            message={`导入完成: ${result.imported} 条成功, ${result.skipped} 条跳过`}
            style={{ marginBottom: 12 }}
          />
          {result.errors.length > 0 && (
            <Table
              dataSource={result.errors.map((e, i) => ({ key: i, error: e }))}
              columns={[{ title: '错误信息', dataIndex: 'error' }]}
              size="small"
              pagination={false}
            />
          )}
        </div>
      )}
    </Card>
  );
}

async function parseFile(file: File): Promise<Array<{ question: string; answer: string; category: string }>> {
  const text = await file.text();

  if (file.name.endsWith('.csv')) {
    const parsed = Papa.parse(text, { header: true, skipEmptyLines: true, transformHeader: (h) => h.trim().toLowerCase() });
    return (parsed.data as any[]).map((row) => ({
      question: (row.question || '').trim(),
      answer: (row.answer || '').trim(),
      category: (row.category || 'general').trim(),
    })).filter((r) => r.question && r.answer);
  }

  // Excel
  const wb = XLSX.read(await file.arrayBuffer(), { type: 'array' });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows: any[] = XLSX.utils.sheet_to_json(sheet);

  return rows.map((r) => ({
    question: String(r.question || r['问题'] || ''),
    answer: String(r.answer || r['回答'] || ''),
    category: String(r.category || r['分类'] || 'general'),
  })).filter((r) => r.question && r.answer);
}
