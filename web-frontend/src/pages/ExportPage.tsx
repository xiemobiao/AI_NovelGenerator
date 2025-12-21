// pages/ExportPage.tsx
// 导出功能页面

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Space,
  message,
  Row,
  Col,
  Progress,
  Typography,
} from 'antd';
import { DownloadOutlined, FileTextOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const ExportPage: React.FC = () => {
  const { currentProject, addTask, updateTask } = useAppStore();
  const [form] = Form.useForm();
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  const handleExport = async (values: any) => {
    if (!currentProject) {
      message.error('请先选择项目');
      return;
    }

    try {
      setExporting(true);
      setExportProgress(0);

      const response = await apiClient.exportNovel({
        filepath: currentProject.filepath,
        format: values.format,
        metadata: {
          title: values.title,
          author: values.author,
          genre: values.genre,
          description: values.description,
        },
        start_chapter: values.start_chapter,
        end_chapter: values.end_chapter,
      });

      addTask({
        task_id: response.task_id,
        task_type: 'export',
        status: 'running',
        progress: 0,
        message: `正在导出${values.format.toUpperCase()}格式...`,
        created_at: new Date().toISOString(),
      });

      message.success('导出任务已启动');

      // 轮询进度
      pollExportProgress(response.task_id, values.format);
    } catch (error) {
      message.error('导出失败');
      setExporting(false);
    }
  };

  const pollExportProgress = async (taskId: string, format: string) => {
    const interval = setInterval(async () => {
      try {
        const task = await apiClient.getTask(taskId);
        updateTask(taskId, task);
        setExportProgress(task.progress);

        if (task.status === 'completed') {
          clearInterval(interval);
          setExporting(false);
          setExportProgress(100);
          message.success('导出完成！');

          // 自动下载
          if (currentProject) {
            const blob = await apiClient.downloadExport(
              currentProject.filepath,
              format
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${form.getFieldValue('title')}.${format}`;
            a.click();
            URL.revokeObjectURL(url);
          }
        } else if (task.status === 'failed') {
          clearInterval(interval);
          setExporting(false);
          message.error(`导出失败: ${task.error || '未知错误'}`);
        }
      } catch (error) {
        clearInterval(interval);
        setExporting(false);
      }
    }, 2000);

    setTimeout(() => clearInterval(interval), 600000);
  };

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={3}>
            <FileTextOutlined /> 导出小说
          </Title>
          <Paragraph type="secondary">
            将小说导出为多种格式，支持TXT、EPUB、PDF、DOCX
          </Paragraph>
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleExport}
          initialValues={{
            format: 'epub',
            title: currentProject?.name || '',
            author: '匿名作者',
            genre: currentProject?.genre || '',
          }}
        >
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="导出格式"
                name="format"
                rules={[{ required: true }]}
              >
                <Select size="large">
                  <Select.Option value="txt">TXT - 纯文本</Select.Option>
                  <Select.Option value="epub">EPUB - 电子书</Select.Option>
                  <Select.Option value="pdf">PDF - PDF文档</Select.Option>
                  <Select.Option value="docx">DOCX - Word文档</Select.Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="小说标题"
                name="title"
                rules={[{ required: true, message: '请输入标题' }]}
              >
                <Input size="large" placeholder="我的小说" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="作者"
                name="author"
                rules={[{ required: true }]}
              >
                <Input size="large" placeholder="作者名" />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item label="类型" name="genre">
                <Input size="large" placeholder="玄幻、都市等" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="简介" name="description">
            <TextArea rows={4} placeholder="小说简介..." />
          </Form.Item>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item label="起始章节" name="start_chapter">
                <InputNumber
                  min={1}
                  style={{ width: '100%' }}
                  placeholder="留空表示从第一章开始"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item label="结束章节" name="end_chapter">
                <InputNumber
                  min={1}
                  style={{ width: '100%' }}
                  placeholder="留空表示到最后一章"
                />
              </Form.Item>
            </Col>
          </Row>

          {exporting && (
            <div style={{ marginBottom: 16 }}>
              <Progress
                percent={exportProgress}
                status="active"
                strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
              />
            </div>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<DownloadOutlined />}
              size="large"
              loading={exporting}
              block
            >
              {exporting ? '导出中...' : '开始导出'}
            </Button>
          </Form.Item>
        </Form>
      </Space>
    </Card>
  );
};

export default ExportPage;
