import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Descriptions, Modal, Space, Tag, Typography } from 'antd';
import { EyeOutlined, MessageOutlined, ShoppingOutlined } from '@ant-design/icons';
import { mockProducts, type Product } from '@/mock/products';

export default function SourcePanel() {
  const [detailProduct, setDetailProduct] = useState<Product | null>(null);

  return (
    <div style={{
      width: 330,
      flexShrink: 0,
      borderLeft: '1px solid var(--border-subtle)',
      background: 'var(--sidebar-panel-bg)',
      padding: 14,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      gap: 12,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        paddingBottom: 8,
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <ShoppingOutlined style={{ fontSize: 15, color: 'var(--accent)' }} />
        <Typography.Text strong style={{ fontSize: 14, color: 'var(--text-primary)' }}>
          推荐产品
        </Typography.Text>
      </div>

      <div style={{
        flex: 1,
        minHeight: 0,
        display: 'grid',
        gridTemplateRows: `repeat(${mockProducts.length}, minmax(0, 1fr))`,
        gap: 10,
      }}>
        {mockProducts.map((product) => (
          <ProductCard key={product.id} product={product} onViewDetail={setDetailProduct} />
        ))}
      </div>

      <ProductDetailModal product={detailProduct} onClose={() => setDetailProduct(null)} />
    </div>
  );
}

function ProductCard({
  product,
  onViewDetail,
}: {
  product: Product;
  onViewDetail: (product: Product) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const navigate = useNavigate();

  const askProduct = () => {
    navigate('/chat');
    window.setTimeout(() => {
      window.dispatchEvent(new CustomEvent('rag:quick-send', {
        detail: `我想了解${product.name}，商品ID：${product.productId}，请介绍一下价格、优惠、库存、规格和售后政策。`,
      }));
    }, 80);
  };

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        minHeight: 0,
        border: '1px solid var(--border-subtle)',
        borderRadius: 8,
        padding: '10px 12px',
        background: hovered ? 'var(--bg-hover)' : 'var(--surface-raised)',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ minWidth: 0 }}>
          <Typography.Text strong style={{ fontSize: 13, color: 'var(--text-primary)' }} ellipsis>
            {product.name}
          </Typography.Text>
          <div style={{ marginTop: 3 }}>
            <Tag color="blue" style={{ fontSize: 10 }}>{product.grade}</Tag>
            <Tag color="red" style={{ fontSize: 10 }}>{product.price}</Tag>
          </div>
        </div>
        <Space size={4} style={{ flexShrink: 0 }}>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => onViewDetail(product)}
            style={{ height: 24, width: 28, padding: 0 }}
          />
          <Button
            type="primary"
            size="small"
            icon={<MessageOutlined />}
            onClick={askProduct}
            style={{ height: 24, padding: '0 8px' }}
          >
            咨询
          </Button>
        </Space>
      </div>

      <Typography.Paragraph
        style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.45, margin: 0 }}
        ellipsis={{ rows: 2 }}
      >
        {product.description}
      </Typography.Paragraph>

      <div style={{ display: 'grid', gridTemplateColumns: '52px 1fr', gap: '3px 6px', fontSize: 11, color: 'var(--text-muted)' }}>
        <span>库存</span><span>{product.stock}</span>
        <span>规格</span><span>{product.specs}</span>
        <span>发货</span><span>{product.shipping}</span>
        <span>售后</span><span>{product.service}</span>
      </div>
    </div>
  );
}

function ProductDetailModal({ product, onClose }: { product: Product | null; onClose: () => void }) {
  const navigate = useNavigate();

  const askProduct = () => {
    if (!product) return;
    onClose();
    navigate('/chat');
    window.setTimeout(() => {
      window.dispatchEvent(new CustomEvent('rag:quick-send', {
        detail: `我想了解${product.name}，商品ID：${product.productId}，请介绍一下价格、优惠、库存、规格和售后政策。`,
      }));
    }, 80);
  };

  return (
    <Modal
      open={!!product}
      title={product?.name}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>关闭</Button>,
        <Button key="ask" type="primary" icon={<MessageOutlined />} onClick={askProduct}>咨询该商品</Button>,
      ]}
      width={620}
      destroyOnClose
    >
      {product && (
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="商品ID">{product.productId}</Descriptions.Item>
          <Descriptions.Item label="SKU">{product.skuId}</Descriptions.Item>
          <Descriptions.Item label="价格">{product.price} <Typography.Text type="secondary">原价 {product.originalPrice}</Typography.Text></Descriptions.Item>
          <Descriptions.Item label="优惠">{product.promo}</Descriptions.Item>
          <Descriptions.Item label="库存">{product.stock}</Descriptions.Item>
          <Descriptions.Item label="规格">{product.specs}</Descriptions.Item>
          <Descriptions.Item label="配送">{product.shipping}</Descriptions.Item>
          <Descriptions.Item label="保修">{product.service}</Descriptions.Item>
          <Descriptions.Item label="退换货">{product.returnPolicy}</Descriptions.Item>
          <Descriptions.Item label="标签">{product.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)}</Descriptions.Item>
          <Descriptions.Item label="推荐理由">{product.reason}</Descriptions.Item>
        </Descriptions>
      )}
    </Modal>
  );
}
