// pages/Visualizations.tsx
import React, { useState } from 'react';
import { Card, Row, Col, Button, Space, message, Image } from 'antd';
import {
  LineChartOutlined,
  DeploymentUnitOutlined,
  HeatMapOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';

const Visualizations: React.FC = () => {
  const { currentProject } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [images, setImages] = useState<{ [key: string]: string }>({});

  const generateVisualization = async (type: 'timeline' | 'relationship' | 'heatmap') => {
    if (!currentProject) {
      message.warning('请先选择项目');
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.generateVisualization(
        currentProject.filepath,
        type
      );
      message.success('可视化生成成功');

      // TODO: 加载图片
      setImages({ ...images, [type]: '/api/visualizations/...' });
    } catch (error) {
      message.error('生成失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="数据可视化">
            <Space size="large" wrap>
              <Button
                type="primary"
                size="large"
                icon={<LineChartOutlined />}
                onClick={() => generateVisualization('timeline')}
                loading={loading}
              >
                生成情节线时间轴
              </Button>

              <Button
                type="primary"
                size="large"
                icon={<DeploymentUnitOutlined />}
                onClick={() => generateVisualization('relationship')}
                loading={loading}
              >
                生成角色关系图
              </Button>

              <Button
                type="primary"
                size="large"
                icon={<HeatMapOutlined />}
                onClick={() => generateVisualization('heatmap')}
                loading={loading}
              >
                生成质量热力图
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 显示生成的图表 */}
        {Object.entries(images).map(([type, url]) => (
          <Col xs={24} lg={12} key={type}>
            <Card
              title={type}
              extra={
                <Button icon={<DownloadOutlined />} type="link">
                  下载
                </Button>
              }
            >
              <Image src={url} alt={type} />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default Visualizations;
