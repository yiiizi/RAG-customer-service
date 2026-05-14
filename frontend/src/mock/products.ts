export interface Product {
  id: string;
  productId: string;
  skuId: string;
  name: string;
  description: string;
  grade: string;
  price: string;
  originalPrice: string;
  tags: string[];
  promo: string;
  stock: string;
  service: string;
  specs: string;
  shipping: string;
  returnPolicy: string;
  reason: string;
}

export const mockProducts: Product[] = [
  {
    id: 'p1',
    productId: 'P2001',
    skuId: 'SKU2001-01',
    name: '星澜 X1 Pro 智能手机',
    description: '120Hz AMOLED 屏幕，5000mAh 电池，支持 66W 快充。',
    grade: '推荐 A',
    price: '¥2999',
    originalPrice: '¥3399',
    promo: '直降 400',
    stock: '128 件',
    service: '整机 1 年保修',
    specs: '12GB+256GB / 曜石黑 / 6.7 英寸',
    shipping: '24-48 小时发货',
    returnPolicy: '支持 7 天无理由退货，激活后非质量问题不支持退货',
    reason: '手机咨询频率高，适合展示参数、库存和售后政策。',
    tags: ['5G', '高刷屏', '快充'],
  },
  {
    id: 'p2',
    productId: 'P2003',
    skuId: 'SKU2002-01',
    name: '云听 AirBuds 5 无线耳机',
    description: '支持 42dB 主动降噪，单次续航约 7 小时。',
    grade: '推荐 A',
    price: '¥399',
    originalPrice: '¥499',
    promo: '直降 100',
    stock: '320 件',
    service: '15 天质量换新',
    specs: '蓝牙5.3 / IPX4 / 28 小时总续航',
    shipping: '24 小时内发货',
    returnPolicy: '未拆封支持 7 天无理由，已拆封因卫生原因非质量问题不支持退货',
    reason: '适合测试拆封退货、卫生类商品和售后边界。',
    tags: ['主动降噪', '蓝牙5.3', '轻量'],
  },
  {
    id: 'p3',
    productId: 'P2004',
    skuId: 'SKU2003-01',
    name: '跃动 Watch S3 智能手表',
    description: '支持心率、血氧、睡眠监测，内置 GPS 和 NFC。',
    grade: '推荐 A',
    price: '¥899',
    originalPrice: '¥1099',
    promo: '直降 200',
    stock: '95 件',
    service: '整机 1 年保修',
    specs: '42mm / 10 天续航 / 5ATM 防水',
    shipping: '48 小时内发货',
    returnPolicy: '支持 7 天无理由退货，明显佩戴痕迹可能影响退货',
    reason: '适合商品详情、保修、佩戴痕迹退货问答。',
    tags: ['健康监测', 'GPS', 'NFC'],
  },
  {
    id: 'p4',
    productId: 'P2009',
    skuId: 'SKU2007-01',
    name: '净源桌面空气净化器 A2',
    description: '适合卧室和办公桌面使用，支持滤芯寿命提醒。',
    grade: '推荐 A',
    price: '¥699',
    originalPrice: '¥899',
    promo: '直降 200',
    stock: '64 件',
    service: '整机 1 年保修',
    specs: '15-25㎡ / HEPA 复合滤芯 / 28dB',
    shipping: '48 小时内发货',
    returnPolicy: '支持 7 天无理由退货，滤芯拆封使用后不支持退货',
    reason: '适合测试耗材类售后、滤芯更换和关联追问。',
    tags: ['除醛', '静音', '滤芯提醒'],
  },
  {
    id: 'p5',
    productId: 'P2015',
    skuId: 'SKU2013-01',
    name: '小鹿儿童学习平板 T8',
    description: '内置小学同步课程，支持家长管控和低蓝光护眼。',
    grade: '推荐 A',
    price: '¥1399',
    originalPrice: '¥1699',
    promo: '直降 300',
    stock: '56 件',
    service: '整机 1 年保修',
    specs: '10.4 英寸 / 6GB+128GB / WiFi',
    shipping: '24-48 小时发货',
    returnPolicy: '激活后非质量问题不支持 7 天无理由退货',
    reason: '适合测试激活类商品退货限制和教育电子售后。',
    tags: ['学习资源', '家长管控', '护眼'],
  },
];
