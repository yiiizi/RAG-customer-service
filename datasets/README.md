# 智能客服演示数据集

本目录用于给项目补充演示数据，不直接替代系统的上传、切块和向量化流程。

## 目录说明

- `knowledge_docs/`：知识库原始文档。通过管理端知识库上传入口上传，让系统自动完成解析、父子分块、embedding、BM25 索引和来源追踪。
- `faq_import.json`：FAQ 高频问答批量导入数据。可通过后端 `/api/faq/batch-import` 或前端 FAQ 导入功能导入。
- `structured_business_data.json`：商品、订单、物流结构化样例。适合后续替换 Mock 服务或初始化业务表，不建议上传到知识库。

## 推荐导入顺序

1. 先上传 `knowledge_docs/` 下的文档。
2. 再导入 `faq_import.json`。
3. 最后根据需要把 `structured_business_data.json` 接入业务服务。

## 验收问题示例

- 退货政策是什么？
- 手机拆封后还能退货吗？
- 发票怎么开？
- 会员积分怎么用？
- 订单 00010002 到哪里了？
- 第一个商品什么时候发货？
- 我的快递多久能到？
