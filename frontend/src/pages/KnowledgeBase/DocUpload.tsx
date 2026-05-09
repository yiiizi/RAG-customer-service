import { useState } from 'react';
import { Upload, message, Card, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useKnowledgeStore } from '@/stores/useKnowledgeStore';
import { SUPPORTED_FILE_TYPES } from '@/utils/constants';

const { Dragger } = Upload;

export default function DocUpload() {
  const { uploadFile, uploading } = useKnowledgeStore();
  const [fileList, setFileList] = useState<any[]>([]);

  const handleUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    try {
      await uploadFile(file);
      message.success(`${file.name} 上传并索引成功`);
      onSuccess?.({}, file);
    } catch (err: any) {
      onError?.(err);
    }
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <Card>
        <Dragger
          multiple
          fileList={fileList}
          onChange={({ fileList: fl }) => setFileList(fl)}
          customRequest={handleUpload}
          showUploadList={{ showRemoveIcon: true }}
          accept={SUPPORTED_FILE_TYPES.join(',')}
          disabled={uploading}
          beforeUpload={(file) => {
            if (file.size > 50 * 1024 * 1024) {
              message.error(`${file.name} 超过 50MB 限制`);
              return Upload.LIST_IGNORE;
            }
            return true;
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint" style={{ fontSize: 12 }}>
            支持 PDF / Word / Markdown / HTML / CSV / Excel / PPT / JSON / EPUB / 图片(OCR) / 代码文件
          </p>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            单个文件最大 50MB
          </Typography.Text>
        </Dragger>
      </Card>
    </div>
  );
}
