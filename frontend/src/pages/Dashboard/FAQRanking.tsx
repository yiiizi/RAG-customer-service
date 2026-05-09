import { Card, Table, Tag } from 'antd';

interface Props {
  data: Array<{
    id: string;
    question: string;
    frequency: number;
    category: string;
  }>;
}

export default function FAQRanking({ data }: Props) {
  return (
    <Card title="高频问答 TOP 10">
      <Table
        dataSource={data}
        rowKey="id"
        pagination={false}
        size="small"
        columns={[
          {
            title: '排名',
            width: 50,
            render: (_: unknown, __: unknown, idx: number) => idx + 1,
          },
          {
            title: '问题',
            dataIndex: 'question',
            ellipsis: true,
          },
          {
            title: '分类',
            dataIndex: 'category',
            width: 80,
            render: (cat: string) => <Tag>{cat}</Tag>,
          },
          {
            title: '命中',
            dataIndex: 'frequency',
            width: 80,
            render: (freq: number) => (
              <Tag color={freq > 500 ? 'red' : 'orange'}>{freq}</Tag>
            ),
          },
        ]}
      />
    </Card>
  );
}
