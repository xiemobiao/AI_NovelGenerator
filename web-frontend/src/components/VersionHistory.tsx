// components/VersionHistory.tsx
// 版本历史组件

import React, { useState, useEffect } from 'react';
import { Modal, Timeline, Button, Space, Typography, Tag, Empty, Spin, message } from 'antd';
import { ClockCircleOutlined, RollbackOutlined, EyeOutlined } from '@ant-design/icons';
import type { ChapterVersion } from '@/types';
import { useAppStore } from '@/store/useAppStore';

const { Text, Paragraph } = Typography;

interface VersionHistoryProps {
  visible: boolean;
  chapterNumber: number;
  onClose: () => void;
  onRestore: (version: ChapterVersion) => void;
}

const VersionHistory: React.FC<VersionHistoryProps> = ({
  visible,
  chapterNumber,
  onClose,
  onRestore,
}) => {
  const { currentUser } = useAppStore();
  const [versions, setVersions] = useState<ChapterVersion[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewVersion, setPreviewVersion] = useState<ChapterVersion | null>(null);

  useEffect(() => {
    if (visible) {
      loadVersions();
    }
  }, [visible, chapterNumber]);

  const loadVersions = async () => {
    setLoading(true);
    try {
      // 模拟API调用 - 实际应该调用后端API
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟版本数据
      const mockVersions: ChapterVersion[] = [
        {
          version_id: '1',
          chapter_number: chapterNumber,
          content: '这是第一版的内容...',
          word_count: 1000,
          created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
          created_by: currentUser?.username || 'user',
          change_description: '初始版本',
        },
        {
          version_id: '2',
          chapter_number: chapterNumber,
          content: '这是第二版的内容，进行了修改...',
          word_count: 1200,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          created_by: currentUser?.username || 'user',
          change_description: '修正了部分情节矛盾',
        },
        {
          version_id: '3',
          chapter_number: chapterNumber,
          content: '这是最新版本的内容...',
          word_count: 1500,
          created_at: new Date().toISOString(),
          created_by: currentUser?.username || 'user',
          change_description: '添加了角色对话',
        },
      ];

      setVersions(mockVersions);
    } catch (error) {
      message.error('加载版本历史失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = (version: ChapterVersion) => {
    Modal.confirm({
      title: '确认恢复版本？',
      content: `确定要恢复到 ${new Date(version.created_at).toLocaleString()} 的版本吗？当前内容将被保存为新版本。`,
      onOk: () => {
        onRestore(version);
        message.success('版本已恢复');
        onClose();
      },
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} 天前`;
    } else if (hours > 0) {
      return `${hours} 小时前`;
    } else {
      return '刚刚';
    }
  };

  return (
    <>
      <Modal
        title={`第${chapterNumber}章 - 版本历史`}
        open={visible}
        onCancel={onClose}
        width={800}
        footer={null}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin tip="加载中..." />
          </div>
        ) : versions.length === 0 ? (
          <Empty description="暂无版本历史" />
        ) : (
          <Timeline
            items={versions.map((version, index) => ({
              dot: index === 0 ? <ClockCircleOutlined style={{ fontSize: '16px' }} /> : undefined,
              color: index === 0 ? 'green' : 'gray',
              children: (
                <div>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Space>
                      <Text strong>{formatDate(version.created_at)}</Text>
                      {index === 0 && <Tag color="green">当前版本</Tag>}
                      <Text type="secondary">{new Date(version.created_at).toLocaleString()}</Text>
                    </Space>

                    <Space>
                      <Text type="secondary">作者:</Text>
                      <Text>{version.created_by}</Text>
                      <Text type="secondary">字数:</Text>
                      <Text>{version.word_count}</Text>
                    </Space>

                    {version.change_description && (
                      <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                        {version.change_description}
                      </Paragraph>
                    )}

                    <Space>
                      <Button
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => setPreviewVersion(version)}
                      >
                        预览
                      </Button>
                      {index !== 0 && (
                        <Button
                          size="small"
                          type="primary"
                          icon={<RollbackOutlined />}
                          onClick={() => handleRestore(version)}
                        >
                          恢复此版本
                        </Button>
                      )}
                    </Space>
                  </Space>
                </div>
              ),
            }))}
          />
        )}
      </Modal>

      {/* 预览模态框 */}
      <Modal
        title={`版本预览 - ${previewVersion ? new Date(previewVersion.created_at).toLocaleString() : ''}`}
        open={!!previewVersion}
        onCancel={() => setPreviewVersion(null)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setPreviewVersion(null)}>
            关闭
          </Button>,
          previewVersion && (
            <Button
              key="restore"
              type="primary"
              icon={<RollbackOutlined />}
              onClick={() => {
                if (previewVersion) {
                  handleRestore(previewVersion);
                  setPreviewVersion(null);
                }
              }}
            >
              恢复此版本
            </Button>
          ),
        ]}
      >
        {previewVersion && (
          <div
            style={{
              maxHeight: '500px',
              overflow: 'auto',
              padding: '16px',
              background: '#f5f5f5',
              borderRadius: '4px',
            }}
          >
            <Paragraph>{previewVersion.content}</Paragraph>
          </div>
        )}
      </Modal>
    </>
  );
};

export default VersionHistory;
