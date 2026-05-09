import { Card } from 'antd';
import ReactECharts from 'echarts-for-react';

interface Props {
  data: Array<{ date: string; count: number }>;
}

export default function QAChart({ data }: Props) {
  const option = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category' as const,
      data: data.map((d) => d.date.slice(5)),
      axisLabel: { fontSize: 11, rotate: 45 },
    },
    yAxis: { type: 'value' as const, minInterval: 1 },
    series: [
      {
        data: data.map((d) => d.count),
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(22,119,255,0.15)' },
        lineStyle: { color: '#1677ff', width: 2 },
        itemStyle: { color: '#1677ff' },
      },
    ],
  };

  return (
    <Card title="问答趋势（近30天）">
      {data.length > 0 ? (
        <ReactECharts option={option} style={{ height: 240 }} />
      ) : (
        <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>暂无数据</div>
      )}
    </Card>
  );
}
