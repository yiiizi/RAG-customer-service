import { Card } from 'antd';
import ReactECharts from 'echarts-for-react';
import { INTENT_LABELS, INTENT_COLORS } from '@/utils/constants';

interface Props {
  data: Record<string, number>;
}

export default function IntentPie({ data }: Props) {
  const chartData = Object.entries(data).map(([intent, count]) => ({
    name: INTENT_LABELS[intent] || intent,
    value: count,
    itemStyle: { color: INTENT_COLORS[intent] || '#999' },
  }));

  const option = {
    tooltip: { trigger: 'item' as const },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '45%'],
        data: chartData,
        label: {
          formatter: '{b}\n{d}%',
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.15)' },
        },
      },
    ],
  };

  return (
    <Card title="意图分布">
      {chartData.length > 0 ? (
        <ReactECharts option={option} style={{ height: 280 }} />
      ) : (
        <div style={{ textAlign: 'center', padding: 80, color: '#999' }}>暂无数据</div>
      )}
    </Card>
  );
}
