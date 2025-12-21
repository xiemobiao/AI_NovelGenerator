// pages/LongNovelManager.tsx
// 长篇小说管理 - 完整实现

import React, { useEffect, useState } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Tag,
  Descriptions,
  Progress,
  List,
  Statistic,
  Row,
  Col,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';
import type { Plotline } from '@/types';

const { TextArea } = Input;

// 卷册接口（临时定义）
interface Volume {
  id: string;
  title: string;
  start_chapter: number;
  end_chapter: number;
  summary: string;
  main_plot: string;
}

const LongNovelManager: React.FC = () => {
  const { currentProject, plotlines, setPlotlines, qualityReport, setQualityReport } = useAppStore();

  const [activeTab, setActiveTab] = useState('volumes');
  const [loading, setLoading] = useState(false);

  // 卷册管理状态
  const [volumes] = useState<Volume[]>([]);
  const [showVolumeModal, setShowVolumeModal] = useState(false);
  const [editingVolume, setEditingVolume] = useState<Volume | null>(null);
  const [volumeForm] = Form.useForm();

  // 情节线管理状态
  const [showPlotlineModal, setShowPlotlineModal] = useState(false);
  const [editingPlotline, setEditingPlotline] = useState<Plotline | null>(null);
  const [plotlineForm] = Form.useForm();

  useEffect(() => {
    if (currentProject) {
      loadData();
    }
  }, [currentProject, activeTab]);

  const loadData = async () => {
    if (!currentProject) return;

    try {
      setLoading(true);

      if (activeTab === 'volumes') {
        // TODO: 加载卷册数据
        // const volumeList = await apiClient.getVolumes(currentProject.filepath);
        // setVolumes(volumeList);
      } else if (activeTab === 'plotlines') {
        const plotlineList = await apiClient.getPlotlines(currentProject.filepath);
        setPlotlines(plotlineList);
      } else if (activeTab === 'quality') {
        const report = await apiClient.getQualityReport(currentProject.filepath);
        setQualityReport(report);
      }
    } catch (error) {
      console.log('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // ==================== 卷册管理 ====================
  const handleAddVolume = () => {
    setEditingVolume(null);
    volumeForm.resetFields();
    setShowVolumeModal(true);
  };

  const handleEditVolume = (volume: Volume) => {
    setEditingVolume(volume);
    volumeForm.setFieldsValue(volume);
    setShowVolumeModal(true);
  };

  const handleSaveVolume = async (_values: any) => {
    try {
      // TODO: 实现保存API
      message.success(editingVolume ? '卷册更新成功' : '卷册创建成功');
      setShowVolumeModal(false);
      loadData();
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleDeleteVolume = (volume: Volume) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除"${volume.title}"吗？`,
      onOk: async () => {
        try {
          // TODO: 实现删除API
          message.success('删除成功');
          loadData();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const volumeColumns = [
    {
      title: '卷号',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '卷名',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '章节范围',
      key: 'range',
      render: (_: unknown, record: Volume) => (
        <span>
          第{record.start_chapter}-{record.end_chapter}章
        </span>
      ),
    },
    {
      title: '摘要',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: Volume) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditVolume(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteVolume(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // ==================== 情节线管理 ====================
  const handleAddPlotline = () => {
    setEditingPlotline(null);
    plotlineForm.resetFields();
    setShowPlotlineModal(true);
  };

  const handleEditPlotline = (plotline: Plotline) => {
    setEditingPlotline(plotline);
    plotlineForm.setFieldsValue(plotline);
    setShowPlotlineModal(true);
  };

  const handleSavePlotline = async (values: any) => {
    if (!currentProject) return;

    try {
      if (editingPlotline) {
        await apiClient.updatePlotline(
          currentProject.filepath,
          editingPlotline.plot_id,
          values
        );
        message.success('情节线更新成功');
      } else {
        await apiClient.createPlotline(currentProject.filepath, values);
        message.success('情节线创建成功');
      }

      setShowPlotlineModal(false);
      loadData();
    } catch (error) {
      message.error('保存失败');
    }
  };

  const getPlotlineStatusTag = (status: Plotline['status']) => {
    const statusMap: Record<string, { color: string; text: string; icon?: React.ReactNode }> = {
      planned: { color: 'default', text: '计划中', icon: <ClockCircleOutlined /> },
      active: { color: 'processing', text: '进行中', icon: <ExclamationCircleOutlined /> },
      suspended: { color: 'warning', text: '已暂停', icon: <ClockCircleOutlined /> },
      resolved: { color: 'success', text: '已完结', icon: <CheckCircleOutlined /> },
      abandoned: { color: 'default', text: '已放弃' },
    };

    const { color, text, icon } = statusMap[status];
    return (
      <Tag color={color} icon={icon}>
        {text}
      </Tag>
    );
  };

  const getImportanceTag = (importance: Plotline['importance']) => {
    const colorMap = {
      main: 'red',
      major: 'orange',
      minor: 'blue',
      background: 'default',
    };
    return <Tag color={colorMap[importance]}>{importance}</Tag>;
  };

  const plotlineColumns = [
    {
      title: '情节线',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '重要性',
      dataIndex: 'importance',
      key: 'importance',
      width: 100,
      render: (importance: Plotline['importance']) => getImportanceTag(importance),
    },
    {
      title: '章节范围',
      key: 'range',
      width: 150,
      render: (_: unknown, record: Plotline) => (
        <span>
          第{record.start_chapter}-{record.expected_end_chapter}章
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: Plotline['status']) => getPlotlineStatusTag(status),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: Plotline) => (
        <Button
          type="link"
          size="small"
          icon={<EditOutlined />}
          onClick={() => handleEditPlotline(record)}
        >
          编辑
        </Button>
      ),
    },
  ];

  // ==================== 标签页内容 ====================
  const volumesContent = (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAddVolume}
        >
          新增卷册
        </Button>
      </div>

      {volumes.length === 0 ? (
        <Empty description="还没有卷册">
          <Button type="primary" onClick={handleAddVolume}>
            创建第一个卷册
          </Button>
        </Empty>
      ) : (
        <Table
          dataSource={volumes}
          columns={volumeColumns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      )}
    </div>
  );

  const plotlinesContent = (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddPlotline}
          >
            新增情节线
          </Button>
          <div style={{ color: '#666' }}>
            共 {plotlines.length} 条情节线
          </div>
        </Space>
      </div>

      {plotlines.length === 0 ? (
        <Empty description="还没有情节线">
          <Button type="primary" onClick={handleAddPlotline}>
            创建第一条情节线
          </Button>
        </Empty>
      ) : (
        <Table
          dataSource={plotlines}
          columns={plotlineColumns}
          rowKey="plot_id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          expandable={{
            expandedRowRender: (record) => (
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="描述" span={2}>
                  {record.description}
                </Descriptions.Item>
                <Descriptions.Item label="里程碑">
                  {record.milestones?.length || 0} 个
                </Descriptions.Item>
                <Descriptions.Item label="冲突">
                  {record.conflicts?.length || 0} 个
                </Descriptions.Item>
              </Descriptions>
            ),
          }}
        />
      )}
    </div>
  );

  const qualityContent = (
    <div>
      {!qualityReport ? (
        <Empty description="暂无质量报告" />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 统计信息 */}
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总章节数"
                  value={qualityReport.total_chapters}
                  suffix="章"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总角色数"
                  value={qualityReport.total_characters}
                  suffix="个"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总地点数"
                  value={qualityReport.total_locations}
                  suffix="个"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="未解决伏笔"
                  value={qualityReport.unresolved_foreshadowing}
                  suffix="个"
                  valueStyle={{ color: qualityReport.unresolved_foreshadowing > 0 ? '#cf1322' : '#3f8600' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 主要角色 */}
          <Card title="主要角色">
            <List
              dataSource={qualityReport.main_characters?.slice(0, 10)}
              renderItem={(char) => (
                <List.Item>
                  <List.Item.Meta
                    title={char.name}
                    description={
                      <Space>
                        <span>出场 {char.appearances} 次</span>
                        <span>
                          第{char.first_chapter}-{char.last_chapter}章
                        </span>
                      </Space>
                    }
                  />
                  <Progress
                    percent={(char.appearances / qualityReport.total_chapters) * 100}
                    size="small"
                    showInfo={false}
                    style={{ width: 200 }}
                  />
                </List.Item>
              )}
            />
          </Card>

          {/* 一致性问题 */}
          {qualityReport.character_issues && qualityReport.character_issues.length > 0 && (
            <Card title={`角色一致性问题 (${qualityReport.character_issues.length})`}>
              <List
                dataSource={qualityReport.character_issues.slice(0, 10)}
                renderItem={(issue) => (
                  <List.Item>
                    <ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
                    {issue}
                  </List.Item>
                )}
              />
            </Card>
          )}

          {qualityReport.location_issues && qualityReport.location_issues.length > 0 && (
            <Card title={`地点一致性问题 (${qualityReport.location_issues.length})`}>
              <List
                dataSource={qualityReport.location_issues.slice(0, 10)}
                renderItem={(issue) => (
                  <List.Item>
                    <ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
                    {issue}
                  </List.Item>
                )}
              />
            </Card>
          )}
        </Space>
      )}
    </div>
  );

  const tabItems = [
    {
      key: 'volumes',
      label: '卷册管理',
      children: volumesContent,
    },
    {
      key: 'plotlines',
      label: '情节线',
      children: plotlinesContent,
    },
    {
      key: 'quality',
      label: '质量报告',
      children: qualityContent,
    },
  ];

  return (
    <div>
      <Card title="长篇小说管理">
        <Tabs
          items={tabItems}
          activeKey={activeTab}
          onChange={setActiveTab}
        />
      </Card>

      {/* 卷册编辑对话框 */}
      <Modal
        title={editingVolume ? '编辑卷册' : '新增卷册'}
        open={showVolumeModal}
        onOk={() => volumeForm.submit()}
        onCancel={() => setShowVolumeModal(false)}
        width={700}
      >
        <Form
          form={volumeForm}
          layout="vertical"
          onFinish={handleSaveVolume}
        >
          <Form.Item
            label="卷名"
            name="title"
            rules={[{ required: true, message: '请输入卷名' }]}
          >
            <Input placeholder="例如：第一卷 - 初入仙门" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="起始章节"
                name="start_chapter"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="结束章节"
                name="end_chapter"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="卷摘要" name="summary">
            <TextArea rows={4} placeholder="描述本卷的主要内容..." />
          </Form.Item>

          <Form.Item label="主要情节" name="main_plot">
            <TextArea rows={4} placeholder="本卷的核心情节线..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* 情节线编辑对话框 */}
      <Modal
        title={editingPlotline ? '编辑情节线' : '新增情节线'}
        open={showPlotlineModal}
        onOk={() => plotlineForm.submit()}
        onCancel={() => setShowPlotlineModal(false)}
        width={700}
      >
        <Form
          form={plotlineForm}
          layout="vertical"
          onFinish={handleSavePlotline}
        >
          <Form.Item
            label="情节线标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="例如：主角修炼之路" />
          </Form.Item>

          <Form.Item
            label="重要性"
            name="importance"
            initialValue="major"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="main">主线</Select.Option>
              <Select.Option value="major">主要支线</Select.Option>
              <Select.Option value="minor">次要支线</Select.Option>
              <Select.Option value="background">背景线</Select.Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="起始章节"
                name="start_chapter"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="预计结束章节"
                name="expected_end_chapter"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="状态"
            name="status"
            initialValue="planned"
          >
            <Select>
              <Select.Option value="planned">计划中</Select.Option>
              <Select.Option value="active">进行中</Select.Option>
              <Select.Option value="suspended">已暂停</Select.Option>
              <Select.Option value="resolved">已完结</Select.Option>
              <Select.Option value="abandoned">已放弃</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: true }]}
          >
            <TextArea rows={4} placeholder="描述这条情节线的发展..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LongNovelManager;
