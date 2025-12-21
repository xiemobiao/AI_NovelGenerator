// components/Layout.tsx
// 主布局组件

import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout as AntLayout, Menu, Button, Typography, Space, Badge } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  UnorderedListOutlined,
  EditOutlined,
  BarChartOutlined,
  LineChartOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';

const { Header, Sider, Content } = AntLayout;
const { Title } = Typography;

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const { sidebarCollapsed, setSidebarCollapsed, tasks, notifications } = useAppStore();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/architecture',
      icon: <FileTextOutlined />,
      label: '小说架构',
    },
    {
      key: '/blueprint',
      icon: <UnorderedListOutlined />,
      label: '章节蓝图',
    },
    {
      key: '/chapters',
      icon: <EditOutlined />,
      label: '章节编辑',
    },
    {
      key: '/long-novel',
      icon: <BarChartOutlined />,
      label: '长篇管理',
    },
    {
      key: '/visualizations',
      icon: <LineChartOutlined />,
      label: '数据可视化',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ];

  const runningTasks = tasks.filter(t => t.status === 'running').length;

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
        width={250}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: sidebarCollapsed ? '16px' : '20px',
            fontWeight: 'bold',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          {sidebarCollapsed ? '📚' : '📚 AI小说生成器'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: '16px' }}
        />
      </Sider>

      <AntLayout style={{ marginLeft: sidebarCollapsed ? 80 : 250, transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Space>
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            />
            <Title level={4} style={{ margin: 0 }}>
              AI Novel Generator - Web
            </Title>
          </Space>

          <Space>
            <Badge count={runningTasks} offset={[-5, 5]}>
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => {/* TODO: 打开任务面板 */}}
              >
                {runningTasks > 0 && `${runningTasks} 个任务进行中`}
              </Button>
            </Badge>
          </Space>
        </Header>

        <Content style={{ margin: '24px', minHeight: 'calc(100vh - 112px)' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default AppLayout;
