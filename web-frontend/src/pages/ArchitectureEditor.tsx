// pages/ArchitectureEditor.tsx
// 小说架构编辑器

import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Button, Space, message, Spin } from 'antd';
import { SaveOutlined, RocketOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';

const { TextArea } = Input;

const ArchitectureEditor: React.FC = () => {
  const { currentProject, architecture, setArchitecture, addTask } = useAppStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (currentProject) {
      loadArchitecture();
    }
  }, [currentProject]);

  useEffect(() => {
    if (architecture) {
      form.setFieldsValue(architecture);
    }
  }, [architecture, form]);

  const loadArchitecture = async () => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const arch = await apiClient.getArchitecture(currentProject.filepath);
      setArchitecture(arch);
    } catch (error) {
      // 架构可能还不存在
      console.log('No architecture found');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (values: any) => {
    if (!currentProject) return;

    try {
      setLoading(true);
      const response = await apiClient.generateArchitecture({
        ...values,
        filepath: currentProject.filepath,
        num_chapters: currentProject.num_chapters,
        word_number: 3000,
      });

      addTask({
        task_id: response.task_id,
        task_type: 'architecture',
        status: 'running',
        progress: 0,
        message: '正在生成小说架构...',
        created_at: new Date().toISOString(),
      });

      message.success('架构生成任务已启动');
    } catch (error) {
      message.error('生成失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!currentProject) return;

    try {
      setSaving(true);
      const values = form.getFieldsValue();
      // TODO: 调用保存接口
      setArchitecture(values);
      message.success('保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Spin spinning={loading}>
      <Card
        title="小说架构"
        extra={
          <Space>
            <Button icon={<SaveOutlined />} onClick={handleSave} loading={saving}>
              保存
            </Button>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={() => form.submit()}
            >
              AI生成
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
        >
          <Form.Item
            label="小说主题"
            name="topic"
            rules={[{ required: true, message: '请输入小说主题' }]}
          >
            <TextArea
              rows={3}
              placeholder="请描述小说的核心主题和设定..."
            />
          </Form.Item>

          <Form.Item label="类型" name="genre">
            <Input placeholder="玄幻、都市、科幻等" />
          </Form.Item>

          <Form.Item label="主要角色" name="main_characters">
            <TextArea
              rows={4}
              placeholder="描述主要角色的性格、背景、能力等..."
            />
          </Form.Item>

          <Form.Item label="故事背景" name="story_background">
            <TextArea
              rows={4}
              placeholder="世界观设定、时代背景等..."
            />
          </Form.Item>

          <Form.Item label="情节大纲" name="plot_outline">
            <TextArea
              rows={6}
              placeholder="整体故事发展脉络..."
            />
          </Form.Item>

          <Form.Item label="核心冲突" name="core_conflicts">
            <TextArea
              rows={4}
              placeholder="故事的主要矛盾和冲突..."
            />
          </Form.Item>

          <Form.Item label="写作风格" name="writing_style">
            <TextArea
              rows={3}
              placeholder="期望的叙事风格、语言特色等..."
            />
          </Form.Item>
        </Form>
      </Card>
    </Spin>
  );
};

export default ArchitectureEditor;
