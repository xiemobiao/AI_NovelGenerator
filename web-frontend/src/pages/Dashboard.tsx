// pages/Dashboard.tsx
// 仪表板页面

import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  List,
  Button,
  Space,
  Tag,
  Empty,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
} from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  PlusOutlined,
  FolderOpenOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';
import type { Project } from '@/types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { currentProject, setCurrentProject, tasks, setTasks, setLoading } = useAppStore();

  const [projects, setProjects] = useState<Project[]>([]);
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadProjects();
    loadTasks();
  }, []);

  const loadProjects = async () => {
    // TODO: 实现项目列表加载
    // 暂时使用模拟数据
    setProjects([
      {
        id: '1',
        name: '修仙传奇',
        filepath: '/path/to/novel1',
        genre: '玄幻',
        num_chapters: 100,
        created_at: '2024-01-01',
        updated_at: '2024-01-15',
        status: 'generating',
      },
      {
        id: '2',
        name: '都市狂少',
        filepath: '/path/to/novel2',
        genre: '都市',
        num_chapters: 50,
        created_at: '2024-01-10',
        updated_at: '2024-01-10',
        status: 'draft',
      },
    ]);
  };

  const loadTasks = async () => {
    try {
      const taskList = await apiClient.listTasks();
      setTasks(taskList);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  };

  const handleCreateProject = async (values: any) => {
    try {
      setLoading(true);
      message.success('项目创建成功！');
      setShowNewProjectModal(false);
      form.resetFields();
      loadProjects();
    } catch (error) {
      message.error('项目创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project);
    message.success(`已切换到项目：${project.name}`);
    navigate('/architecture');
  };

  const getStatusTag = (status: Project['status']) => {
    const statusMap = {
      draft: { color: 'default', text: '草稿' },
      generating: { color: 'processing', text: '生成中' },
      completed: { color: 'success', text: '已完成' },
    };
    const { color, text } = statusMap[status];
    return <Tag color={color}>{text}</Tag>;
  };

  const getTaskStatusTag = (status: string) => {
    const statusMap: any = {
      pending: { color: 'default', text: '待处理' },
      running: { color: 'processing', text: '运行中', icon: <SyncOutlined spin /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', text: '失败' },
    };
    const { color, text, icon } = statusMap[status] || statusMap.pending;
    return <Tag color={color} icon={icon}>{text}</Tag>;
  };

  const totalChapters = projects.reduce((sum, p) => sum + p.num_chapters, 0);
  const completedProjects = projects.filter(p => p.status === 'completed').length;
  const runningTasks = tasks.filter(t => t.status === 'running').length;

  return (
    <div>
      <Row gutter={[16, 16]}>
        {/* 统计卡片 */}
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={projects.length}
              prefix={<FolderOpenOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="章节总数"
              value={totalChapters}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已完成项目"
              value={completedProjects}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="进行中任务"
              value={runningTasks}
              prefix={<SyncOutlined spin={runningTasks > 0} />}
              valueStyle={{ color: runningTasks > 0 ? '#ff9800' : '#666' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* 项目列表 */}
        <Col xs={24} lg={16}>
          <Card
            title="我的项目"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setShowNewProjectModal(true)}
              >
                新建项目
              </Button>
            }
          >
            {projects.length === 0 ? (
              <Empty description="还没有项目，创建一个开始吧！" />
            ) : (
              <List
                dataSource={projects}
                renderItem={(project) => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        onClick={() => handleSelectProject(project)}
                      >
                        打开
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          {project.name}
                          {getStatusTag(project.status)}
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={4}>
                          <div>
                            <Tag>{project.genre}</Tag>
                            <span>共 {project.num_chapters} 章</span>
                          </div>
                          <div style={{ fontSize: 12, color: '#999' }}>
                            更新于 {project.updated_at}
                          </div>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        {/* 最近任务 */}
        <Col xs={24} lg={8}>
          <Card title="最近任务" extra={<Button type="link">查看全部</Button>}>
            {tasks.length === 0 ? (
              <Empty description="暂无任务" />
            ) : (
              <List
                dataSource={tasks.slice(0, 5)}
                renderItem={(task) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <span>{task.task_type}</span>
                          {getTaskStatusTag(task.status)}
                        </Space>
                      }
                      description={
                        <div>
                          {task.status === 'running' && (
                            <Progress
                              percent={task.progress}
                              size="small"
                              status="active"
                            />
                          )}
                          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                            {task.message}
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="快速操作">
            <Space size="large" wrap>
              <Button
                type="primary"
                size="large"
                icon={<PlusOutlined />}
                onClick={() => setShowNewProjectModal(true)}
              >
                创建新项目
              </Button>
              <Button
                size="large"
                icon={<FolderOpenOutlined />}
                onClick={() => {/* TODO: 打开现有项目 */}}
              >
                打开现有项目
              </Button>
              <Button
                size="large"
                icon={<RocketOutlined />}
                onClick={() => navigate('/settings')}
              >
                配置LLM
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 新建项目对话框 */}
      <Modal
        title="创建新项目"
        open={showNewProjectModal}
        onOk={() => form.submit()}
        onCancel={() => {
          setShowNewProjectModal(false);
          form.resetFields();
        }}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateProject}
        >
          <Form.Item
            label="项目名称"
            name="name"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="例如：修仙传奇" />
          </Form.Item>

          <Form.Item
            label="保存路径"
            name="filepath"
            rules={[{ required: true, message: '请选择保存路径' }]}
          >
            <Input placeholder="/path/to/project" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="小说类型"
                name="genre"
                initialValue="玄幻"
                rules={[{ required: true }]}
              >
                <Select>
                  <Select.Option value="玄幻">玄幻</Select.Option>
                  <Select.Option value="都市">都市</Select.Option>
                  <Select.Option value="科幻">科幻</Select.Option>
                  <Select.Option value="武侠">武侠</Select.Option>
                  <Select.Option value="历史">历史</Select.Option>
                  <Select.Option value="言情">言情</Select.Option>
                  <Select.Option value="悬疑">悬疑</Select.Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="计划章节数"
                name="num_chapters"
                initialValue={50}
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="每章字数"
            name="word_number"
            initialValue={3000}
            rules={[{ required: true }]}
          >
            <InputNumber min={500} max={10000} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
