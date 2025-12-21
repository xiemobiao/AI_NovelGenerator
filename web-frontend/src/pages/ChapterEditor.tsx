// pages/ChapterEditor.tsx
// 章节编辑器页面

import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  List,
  Button,
  Space,
  Tag,
  Input,
  Modal,
  Form,
  InputNumber,
  message,
  Spin,
  Statistic,
  Progress,
  Tooltip,
} from 'antd';
import {
  SaveOutlined,
  CheckOutlined,
  PlusOutlined,
  ReloadOutlined,
  FileTextOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';
import type { Chapter, ChapterVersion } from '@/types';
import VersionHistory from '@/components/VersionHistory';

const { TextArea } = Input;

const ChapterEditor: React.FC = () => {
  const {
    currentProject,
    chapters,
    setChapters,
    currentChapter,
    setCurrentChapter,
    addTask,
    updateTask,
  } = useAppStore();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (currentProject) {
      loadChapters();
    }
  }, [currentProject]);

  useEffect(() => {
    if (currentChapter) {
      setEditorContent(currentChapter.content);
    }
  }, [currentChapter]);

  const loadChapters = async () => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const chapterList = await apiClient.listChapters(currentProject.filepath);
      setChapters(chapterList);

      if (chapterList.length > 0 && !currentChapter) {
        setCurrentChapter(chapterList[0]);
      }
    } catch (error) {
      message.error('加载章节列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectChapter = async (chapter: Chapter) => {
    if (!currentProject) return;

    try {
      const fullChapter = await apiClient.getChapter(
        currentProject.filepath,
        chapter.chapter_number
      );
      setCurrentChapter(fullChapter);
    } catch (error) {
      message.error('加载章节内容失败');
    }
  };

  const handleSaveChapter = async () => {
    if (!currentProject || !currentChapter) return;

    try {
      setSaving(true);
      await apiClient.updateChapter(
        currentProject.filepath,
        currentChapter.chapter_number,
        editorContent
      );
      message.success('保存成功');

      // 更新本地状态
      setChapters(
        chapters.map((ch) =>
          ch.chapter_number === currentChapter.chapter_number
            ? { ...ch, content: editorContent, word_count: editorContent.length }
            : ch
        )
      );
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateChapter = async (values: any) => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const response = await apiClient.generateChapter({
        filepath: currentProject.filepath,
        ...values,
      });

      // 添加任务到任务列表
      addTask({
        task_id: response.task_id,
        task_type: 'chapter',
        status: 'running',
        progress: 0,
        message: `正在生成第${values.chapter_num}章...`,
        created_at: new Date().toISOString(),
      });

      message.success('章节生成任务已启动');
      setShowGenerateModal(false);
      form.resetFields();

      // 轮询任务状态
      pollTaskStatus(response.task_id);
    } catch (error) {
      message.error('生成任务启动失败');
    } finally {
      setLoading(false);
    }
  };

  const pollTaskStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const task = await apiClient.getTask(taskId);
        updateTask(taskId, task);

        if (task.status === 'completed') {
          clearInterval(interval);
          message.success('章节生成完成');
          loadChapters();
        } else if (task.status === 'failed') {
          clearInterval(interval);
          message.error(`生成失败: ${task.error || '未知错误'}`);
        }
      } catch (error) {
        clearInterval(interval);
      }
    }, 2000);

    // 10分钟后停止轮询
    setTimeout(() => clearInterval(interval), 600000);
  };

  const handleFinalizeChapter = async () => {
    if (!currentProject || !currentChapter) return;

    Modal.confirm({
      title: '确认定稿',
      content: '定稿后将更新前文摘要、角色状态和向量库，是否继续？',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true);
          const response = await apiClient.finalizeChapter({
            filepath: currentProject.filepath,
            chapter_num: currentChapter.chapter_number,
            word_number: currentChapter.word_count,
          });

          addTask({
            task_id: response.task_id,
            task_type: 'finalize',
            status: 'running',
            progress: 0,
            message: `正在定稿第${currentChapter.chapter_number}章...`,
            created_at: new Date().toISOString(),
          });

          message.success('定稿任务已启动');
          pollTaskStatus(response.task_id);
        } catch (error) {
          message.error('定稿失败');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleRestoreVersion = (version: ChapterVersion) => {
    if (currentChapter) {
      setEditorContent(version.content);
      message.success('版本已恢复到编辑器，请保存以应用更改');
    }
  };

  const getChapterStatusTag = (status: Chapter['status']) => {
    return status === 'final' ? (
      <Tag color="success" icon={<CheckOutlined />}>
        已定稿
      </Tag>
    ) : (
      <Tag color="default">草稿</Tag>
    );
  };

  const completedChapters = chapters.filter((ch) => ch.status === 'final').length;
  const totalWords = chapters.reduce((sum, ch) => sum + ch.word_count, 0);
  const completionRate = currentProject
    ? (completedChapters / currentProject.num_chapters) * 100
    : 0;

  return (
    <Spin spinning={loading}>
      <Row gutter={[16, 16]}>
        {/* 统计信息 */}
        <Col span={24}>
          <Row gutter={16}>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="已完成章节"
                  value={completedChapters}
                  suffix={`/ ${currentProject?.num_chapters || 0}`}
                />
              </Card>
            </Col>

            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="总字数"
                  value={totalWords}
                  suffix="字"
                />
              </Card>
            </Col>

            <Col xs={24} sm={8}>
              <Card>
                <Statistic title="完成度" value={completionRate.toFixed(1)} suffix="%" />
                <Progress
                  percent={completionRate}
                  status="active"
                  strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                />
              </Card>
            </Col>
          </Row>
        </Col>

        {/* 章节列表 */}
        <Col xs={24} md={6}>
          <Card
            title="章节列表"
            extra={
              <Space>
                <Tooltip title="刷新">
                  <Button
                    type="text"
                    icon={<ReloadOutlined />}
                    onClick={loadChapters}
                    size="small"
                  />
                </Tooltip>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setShowGenerateModal(true)}
                  size="small"
                >
                  生成
                </Button>
              </Space>
            }
            bodyStyle={{ padding: 0, maxHeight: 'calc(100vh - 300px)', overflow: 'auto' }}
          >
            <List
              dataSource={chapters}
              renderItem={(chapter) => (
                <List.Item
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    backgroundColor:
                      currentChapter?.chapter_number === chapter.chapter_number
                        ? '#e6f7ff'
                        : 'transparent',
                  }}
                  onClick={() => handleSelectChapter(chapter)}
                >
                  <List.Item.Meta
                    avatar={<FileTextOutlined />}
                    title={
                      <Space>
                        <span>第{chapter.chapter_number}章</span>
                        {getChapterStatusTag(chapter.status)}
                      </Space>
                    }
                    description={
                      <div style={{ fontSize: 12 }}>
                        {chapter.title || '未命名'}
                        <br />
                        <span style={{ color: '#999' }}>
                          {chapter.word_count} 字
                        </span>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* 编辑器 */}
        <Col xs={24} md={18}>
          <Card
            title={
              currentChapter ? (
                <Space>
                  <span>第{currentChapter.chapter_number}章</span>
                  {getChapterStatusTag(currentChapter.status)}
                  <Tag>{editorContent.length} 字</Tag>
                </Space>
              ) : (
                '选择一个章节开始编辑'
              )
            }
            extra={
              currentChapter && (
                <Space>
                  <Tooltip title="版本历史">
                    <Button
                      icon={<HistoryOutlined />}
                      onClick={() => setShowVersionHistory(true)}
                    />
                  </Tooltip>
                  <Button
                    icon={<SaveOutlined />}
                    onClick={handleSaveChapter}
                    loading={saving}
                  >
                    保存
                  </Button>
                  <Button
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={handleFinalizeChapter}
                    disabled={currentChapter.status === 'final'}
                  >
                    定稿
                  </Button>
                </Space>
              )
            }
            bodyStyle={{ padding: 0 }}
          >
            {currentChapter ? (
              <Editor
                height="calc(100vh - 320px)"
                language="markdown"
                value={editorContent}
                onChange={(value) => setEditorContent(value || '')}
                theme="vs-light"
                options={{
                  fontSize: 14,
                  lineHeight: 24,
                  wordWrap: 'on',
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                }}
              />
            ) : (
              <div
                style={{
                  height: 'calc(100vh - 320px)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#999',
                }}
              >
                <Space direction="vertical" align="center">
                  <FileTextOutlined style={{ fontSize: 48 }} />
                  <div>请从左侧选择一个章节开始编辑</div>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setShowGenerateModal(true)}
                  >
                    生成新章节
                  </Button>
                </Space>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 生成章节对话框 */}
      <Modal
        title="生成章节"
        open={showGenerateModal}
        onOk={() => form.submit()}
        onCancel={() => {
          setShowGenerateModal(false);
          form.resetFields();
        }}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleGenerateChapter}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="章节号"
                name="chapter_num"
                rules={[{ required: true, message: '请输入章节号' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} placeholder="1" />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="字数"
                name="word_number"
                initialValue={3000}
                rules={[{ required: true }]}
              >
                <InputNumber min={500} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="涉及角色" name="characters_involved">
            <Input placeholder="例如：主角, 师父, 敌人" />
          </Form.Item>

          <Form.Item label="关键物品" name="key_items">
            <Input placeholder="例如：神器, 灵药" />
          </Form.Item>

          <Form.Item label="场景地点" name="scene_location">
            <Input placeholder="例如：仙府, 密林" />
          </Form.Item>

          <Form.Item label="时间限制" name="time_constraint">
            <Input placeholder="例如：三天后, 黄昏时分" />
          </Form.Item>

          <Form.Item label="剧情指导" name="user_guidance">
            <TextArea
              rows={4}
              placeholder="对本章内容的要求和期望..."
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 版本历史 */}
      {currentChapter && (
        <VersionHistory
          visible={showVersionHistory}
          chapterNumber={currentChapter.chapter_number}
          onClose={() => setShowVersionHistory(false)}
          onRestore={handleRestoreVersion}
        />
      )}
    </Spin>
  );
};

export default ChapterEditor;
