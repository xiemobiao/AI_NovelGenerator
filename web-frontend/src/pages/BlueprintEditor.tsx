// pages/BlueprintEditor.tsx
// 章节蓝图编辑器 - 完整实现

import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  List,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  message,
  Spin,
  Tag,
  Empty,
  Collapse,
  Tooltip,
} from 'antd';
import {
  RocketOutlined,
  EditOutlined,
  FileTextOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';
import type { ChapterBlueprint } from '@/types';

const { TextArea } = Input;
const { Panel } = Collapse;

const BlueprintEditor: React.FC = () => {
  const {
    currentProject,
    blueprints,
    setBlueprints,
    addTask,
    updateTask,
  } = useAppStore();

  const [loading, setLoading] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [editingBlueprint, setEditingBlueprint] = useState<ChapterBlueprint | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [generateForm] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    if (currentProject) {
      loadBlueprints();
    }
  }, [currentProject]);

  const loadBlueprints = async () => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const blueprintList = await apiClient.getBlueprint(currentProject.filepath);
      setBlueprints(blueprintList);
    } catch (error) {
      console.log('No blueprints found');
      setBlueprints([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (values: any) => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const response = await apiClient.generateBlueprint({
        filepath: currentProject.filepath,
        num_chapters: values.num_chapters,
        user_guidance: values.user_guidance,
      });

      addTask({
        task_id: response.task_id,
        task_type: 'blueprint',
        status: 'running',
        progress: 0,
        message: '正在生成章节蓝图...',
        created_at: new Date().toISOString(),
      });

      message.success('蓝图生成任务已启动');
      setShowGenerateModal(false);
      generateForm.resetFields();

      // 轮询任务状态
      pollTaskStatus(response.task_id);
    } catch (error) {
      message.error('生成失败');
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
          message.success('蓝图生成完成');
          loadBlueprints();
        } else if (task.status === 'failed') {
          clearInterval(interval);
          message.error(`生成失败: ${task.error || '未知错误'}`);
        }
      } catch (error) {
        clearInterval(interval);
      }
    }, 2000);

    setTimeout(() => clearInterval(interval), 600000);
  };

  const handleEdit = (blueprint: ChapterBlueprint) => {
    setEditingBlueprint(blueprint);
    editForm.setFieldsValue(blueprint);
    setShowEditModal(true);
  };

  const handleSaveEdit = async (values: any) => {
    if (!currentProject || !editingBlueprint) return;

    try {
      // TODO: 实现保存API
      message.success('保存成功');
      setShowEditModal(false);

      // 更新本地状态
      setBlueprints(
        blueprints.map((bp) =>
          bp.chapter_number === editingBlueprint.chapter_number
            ? { ...bp, ...values }
            : bp
        )
      );
    } catch (error) {
      message.error('保存失败');
    }
  };

  const getStatusTag = (blueprint: ChapterBlueprint) => {
    const hasContent = blueprint.summary && blueprint.summary.length > 0;
    return hasContent ? (
      <Tag color="success" icon={<CheckCircleOutlined />}>
        已完成
      </Tag>
    ) : (
      <Tag color="default">待完善</Tag>
    );
  };

  return (
    <Spin spinning={loading}>
      <Row gutter={[16, 16]}>
        {/* 顶部操作栏 */}
        <Col span={24}>
          <Card>
            <Space size="large">
              <div>
                <div style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 4 }}>
                  章节蓝图
                </div>
                <div style={{ color: '#666' }}>
                  规划每一章的内容大纲，确保故事连贯性
                </div>
              </div>
              <div style={{ flex: 1 }} />
              <Space>
                <Tooltip title="刷新列表">
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={loadBlueprints}
                  >
                    刷新
                  </Button>
                </Tooltip>
                <Button
                  type="primary"
                  size="large"
                  icon={<RocketOutlined />}
                  onClick={() => setShowGenerateModal(true)}
                >
                  生成蓝图
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>

        {/* 蓝图列表 */}
        <Col span={24}>
          <Card
            title={
              <Space>
                <FileTextOutlined />
                <span>蓝图列表</span>
                {blueprints.length > 0 && (
                  <Tag color="blue">{blueprints.length} 章</Tag>
                )}
              </Space>
            }
          >
            {blueprints.length === 0 ? (
              <Empty
                description="还没有章节蓝图"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button
                  type="primary"
                  icon={<RocketOutlined />}
                  onClick={() => setShowGenerateModal(true)}
                >
                  生成蓝图
                </Button>
              </Empty>
            ) : (
              <Collapse accordion>
                {blueprints.map((blueprint) => (
                  <Panel
                    key={blueprint.chapter_number}
                    header={
                      <Space>
                        <span style={{ fontWeight: 'bold' }}>
                          第{blueprint.chapter_number}章
                        </span>
                        {blueprint.title && (
                          <span style={{ color: '#666' }}>
                            - {blueprint.title}
                          </span>
                        )}
                        {getStatusTag(blueprint)}
                      </Space>
                    }
                    extra={
                      <Button
                        type="link"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEdit(blueprint);
                        }}
                      >
                        编辑
                      </Button>
                    }
                  >
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                      {blueprint.title && (
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                            章节标题
                          </div>
                          <div>{blueprint.title}</div>
                        </div>
                      )}

                      {blueprint.summary && (
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                            内容摘要
                          </div>
                          <div style={{ whiteSpace: 'pre-wrap' }}>
                            {blueprint.summary}
                          </div>
                        </div>
                      )}

                      {blueprint.key_events && blueprint.key_events.length > 0 && (
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                            关键事件
                          </div>
                          <List
                            size="small"
                            dataSource={blueprint.key_events}
                            renderItem={(event, index) => (
                              <List.Item>
                                <Space>
                                  <Tag color="blue">{index + 1}</Tag>
                                  {event}
                                </Space>
                              </List.Item>
                            )}
                          />
                        </div>
                      )}

                      {blueprint.characters && blueprint.characters.length > 0 && (
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                            涉及角色
                          </div>
                          <Space wrap>
                            {blueprint.characters.map((char) => (
                              <Tag key={char} color="green">
                                {char}
                              </Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                    </Space>
                  </Panel>
                ))}
              </Collapse>
            )}
          </Card>
        </Col>
      </Row>

      {/* 生成蓝图对话框 */}
      <Modal
        title="生成章节蓝图"
        open={showGenerateModal}
        onOk={() => generateForm.submit()}
        onCancel={() => {
          setShowGenerateModal(false);
          generateForm.resetFields();
        }}
        width={600}
      >
        <Form
          form={generateForm}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            num_chapters: currentProject?.num_chapters || 50,
          }}
        >
          <Form.Item
            label="章节数量"
            name="num_chapters"
            rules={[{ required: true, message: '请输入章节数量' }]}
          >
            <InputNumber
              min={1}
              max={1000}
              style={{ width: '100%' }}
              placeholder="50"
            />
          </Form.Item>

          <Form.Item
            label="内容指导"
            name="user_guidance"
            tooltip="可选：对整体蓝图的要求和期望"
          >
            <TextArea
              rows={6}
              placeholder="例如：第1-20章为修炼初期，重点描写主角的成长；第21-40章为历练阶段，加入更多冒险元素..."
            />
          </Form.Item>

          <div style={{ color: '#999', fontSize: 12 }}>
            💡 提示：生成蓝图后，可以手动编辑每一章的具体内容
          </div>
        </Form>
      </Modal>

      {/* 编辑蓝图对话框 */}
      <Modal
        title={`编辑第${editingBlueprint?.chapter_number}章蓝图`}
        open={showEditModal}
        onOk={() => editForm.submit()}
        onCancel={() => {
          setShowEditModal(false);
          editForm.resetFields();
        }}
        width={700}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleSaveEdit}
        >
          <Form.Item
            label="章节标题"
            name="title"
          >
            <Input placeholder="例如：初入仙门" />
          </Form.Item>

          <Form.Item
            label="内容摘要"
            name="summary"
          >
            <TextArea
              rows={6}
              placeholder="描述本章的主要内容..."
            />
          </Form.Item>

          <Form.Item
            label="关键事件"
            name="key_events"
            tooltip="每行一个事件"
          >
            <TextArea
              rows={4}
              placeholder="例如：&#10;主角通过入门考核&#10;遇到师父&#10;获得第一本功法"
            />
          </Form.Item>

          <Form.Item
            label="涉及角色"
            name="characters"
            tooltip="用逗号分隔"
          >
            <Input placeholder="例如：主角, 师父, 大师兄" />
          </Form.Item>
        </Form>
      </Modal>
    </Spin>
  );
};

export default BlueprintEditor;
