import { Tree } from 'antd';

interface ChunkNode {
  title: string;
  key: string;
  children?: ChunkNode[];
}

interface Props {
  chunks: ChunkNode[];
}

export default function ChunkViewer({ chunks }: Props) {
  return <Tree treeData={chunks} defaultExpandAll showLine />;
}
