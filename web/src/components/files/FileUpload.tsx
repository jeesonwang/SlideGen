/**
 * File Upload component with drag-drop support
 */

import { useState } from 'react';
import { Upload, message, Card, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useUploadMultipleFiles } from '../../hooks/useFiles';

const { Dragger } = Upload;
const { Text } = Typography;

interface FileUploadProps {
  sessionId?: string;
  onUploadComplete?: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  sessionId,
  onUploadComplete,
}) => {
  const [fileList, setFileList] = useState<any[]>([]);
  const uploadMutation = useUploadMultipleFiles();

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('Please select files to upload');
      return;
    }

    if (!sessionId) {
      message.error('No session selected. Please create a session first.');
      return;
    }

    try {
      const files = fileList.map((file) => file.originFileObj);
      await uploadMutation.mutateAsync({ files, sessionId });
      setFileList([]);
      onUploadComplete?.();
    } catch (error) {
      // Error is already handled by the mutation
    }
  };

  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    fileList,
    beforeUpload: (file) => {
      // Check file type
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown',
      ];

      if (!allowedTypes.includes(file.type) && !file.name.endsWith('.md')) {
        message.error(`${file.name} is not a supported file type`);
        return false;
      }

      // Check file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        message.error(`${file.name} is larger than 10MB`);
        return false;
      }

      setFileList((prev) => [...prev, file]);
      return false; // Prevent auto upload
    },
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
    },
    onChange: (info) => {
      // Auto-upload when files are added
      if (info.fileList.length > 0 && info.file.status === undefined) {
        // Small delay to ensure fileList is updated
        setTimeout(() => {
          handleUpload();
        }, 100);
      }
    },
  };

  return (
    <Card>
      <Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          Click or drag files to this area to upload
        </p>
        <p className="ant-upload-hint">
          Support for PDF, DOCX, TXT, and Markdown files. Maximum file size:
          10MB.
        </p>
      </Dragger>
      <div style={{ marginTop: 16 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          Uploaded files will be added to your knowledge base and can be used
          for presentation generation.
        </Text>
      </div>
    </Card>
  );
};
