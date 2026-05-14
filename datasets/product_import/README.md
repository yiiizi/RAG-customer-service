# 商品导入数据说明

这个目录用于管理端商品数据导入或后续商品管理模块开发。

## 文件

- `product_import.csv`：扁平表格格式，适合管理端上传 CSV 或转成 Excel 后导入。
- `product_import.json`：结构化 JSON 格式，适合后端接口、初始化脚本或 Mock 服务读取。

## 推荐字段

- `product_id`：商品 ID，业务唯一标识。
- `spu_id`：标准商品单元，用于把同款不同规格聚合在一起。
- `sku_id`：具体销售规格 ID。
- `name`：商品名称。
- `category`：商品分类。
- `brand`：品牌。
- `model`：型号或规格名。
- `price`：当前售价。
- `original_price`：划线价。
- `stock`：库存。
- `status`：商品状态，当前样例使用 `on_sale`。
- `tags`：商品标签。
- `selling_points`：卖点。
- `specs`：规格参数。
- `warranty`：保修政策。
- `return_policy`：退换货政策。
- `shipping_policy`：发货和配送政策。
- `after_sales`：售后处理方式。
- `recommend_level`：推荐等级，A/B/C。
- `recommend_reason`：推荐理由。

## 导入建议

如果管理端支持 CSV 导入，优先使用 `product_import.csv`。

如果后续要做商品详情接口、推荐商品接口或订单商品关联，建议使用 `product_import.json`，因为 JSON 能保留 `tags`、`selling_points`、`specs` 这些结构化字段。

## 可测试的问题

- 星澜 X1 Pro 有哪些版本？
- 云听 AirBuds 5 拆封后还能退吗？
- 净源 A2 的滤芯多久换一次？
- K870T 青轴和茶轴有什么区别？
- 小鹿儿童学习平板激活后还能无理由退货吗？
