// components/Layout.tsx
// 主布局组件

import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout as AntLayout, Menu, Button, Typography, Space, Badge, Drawer, Grid, Modal, Table, Dropdown, Avatar } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  UnorderedListOutlined,
  EditOutlined,
  BarChartOutlined,
  LineChartOutlined,
  DownloadOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  BulbOutlined,
  BulbFilled,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import { useHotkeys } from '@/hooks/useHotkeys';
import { useWebSocket } from '@/hooks/useWebSocket';

const { Header, Sider, Content } = AntLayout;
const { Title } = Typography;
const { useBreakpoint } = Grid;

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();

  const { sidebarCollapsed, setSidebarCollapsed, tasks, notifications, isDarkMode, toggleTheme, currentUser, logout } = useAppStore();
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const [hotkeyHelpVisible, setHotkeyHelpVisible] = useState(false);

  // 判断是否为移动端
  const isMobile = !screens.md;

  // 移动端自动折叠侧边栏
  useEffect(() => {
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  }, [isMobile, setSidebarCollapsed]);

  // WebSocket实时通知
  useWebSocket();

  // 全局快捷键配置
  useHotkeys([
    {
      key: 'b',
      ctrl: true,
      handler: () => {
        if (!isMobile) {
          setSidebarCollapsed(!sidebarCollapsed);
        }
      },
      description: '切换侧边栏',
    },
    {
      key: 'd',
      ctrl: true,
      handler: toggleTheme,
      description: '切换深色模式',
    },
    {
      key: '/',
      ctrl: true,
      handler: () => setHotkeyHelpVisible(true),
      description: '显示快捷键帮助',
    },
  ]);

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
      key: '/export',
      icon: <DownloadOutlined />,
      label: '导出小说',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ];

  const runningTasks = tasks.filter(t => t.status === 'running').length;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    if (isMobile) {
      setMobileMenuVisible(false);
    }
  };

  const sidebarContent = (
    <>
      <div
        style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: sidebarCollapsed && !isMobile ? '16px' : '20px',
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        {sidebarCollapsed && !isMobile ? '📚' : '📚 AI小说生成器'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ marginTop: '16px' }}
      />
    </>
  );

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
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
          {sidebarContent}
        </Sider>
      )}

      {/* 移动端抽屉菜单 */}
      {isMobile && (
        <Drawer
          placement="left"
          onClose={() => setMobileMenuVisible(false)}
          open={mobileMenuVisible}
          bodyStyle={{ padding: 0, background: '#001529' }}
          width={250}
        >
          {sidebarContent}
        </Drawer>
      )}

      <AntLayout style={{ marginLeft: isMobile ? 0 : (sidebarCollapsed ? 80 : 250), transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: isMobile ? '0 12px' : '0 24px',
            background: isDarkMode ? '#141414' : '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: `1px solid ${isDarkMode ? '#303030' : '#f0f0f0'}`,
          }}
        >
          <Space>
            <Button
              type="text"
              icon={isMobile ? <MenuUnfoldOutlined /> : (sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />)}
              onClick={() => isMobile ? setMobileMenuVisible(true) : setSidebarCollapsed(!sidebarCollapsed)}
            />
            {!isMobile && (
              <Title level={4} style={{ margin: 0 }}>
                AI Novel Generator - Web
              </Title>
            )}
          </Space>

          <Space size={isMobile ? 'small' : 'middle'}>
            <Button
              type="text"
              icon={isDarkMode ? <BulbFilled /> : <BulbOutlined />}
              onClick={toggleTheme}
              title={isDarkMode ? '切换到浅色模式' : '切换到深色模式'}
            />
            <Badge count={runningTasks} offset={[-5, 5]}>
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => {/* TODO: 打开任务面板 */}}
              >
                {!isMobile && runningTasks > 0 && `${runningTasks} 个任务进行中`}
              </Button>
            </Badge>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  size={isMobile ? 'small' : 'default'}
                  icon={<UserOutlined />}
                  style={{ backgroundColor: '#1890ff' }}
                />
                {!isMobile && <span>{currentUser?.username}</span>}
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ margin: isMobile ? '12px' : '24px', minHeight: 'calc(100vh - 112px)' }}>
          <Outlet />
        </Content>
      </AntLayout>

      {/* 快捷键帮助模态框 */}
      <Modal
        title="快捷键帮助"
        open={hotkeyHelpVisible}
        onCancel={() => setHotkeyHelpVisible(false)}
        footer={null}
        width={600}
      >
        <Table
          dataSource={[
            { key: '1', shortcut: 'Ctrl/Cmd + B', description: '切换侧边栏' },
            { key: '2', shortcut: 'Ctrl/Cmd + D', description: '切换深色模式' },
            { key: '3', shortcut: 'Ctrl/Cmd + S', description: '保存当前内容（在编辑器中）' },
            { key: '4', shortcut: 'Ctrl/Cmd + /', description: '显示此帮助' },
          ]}
          columns={[
            {
              title: '快捷键',
              dataIndex: 'shortcut',
              key: 'shortcut',
              width: '40%',
              render: (text) => <code style={{ padding: '2px 6px', background: isDarkMode ? '#333' : '#f5f5f5', borderRadius: '4px' }}>{text}</code>,
            },
            {
              title: '功能说明',
              dataIndex: 'description',
              key: 'description',
            },
          ]}
          pagination={false}
        />
      </Modal>
    </AntLayout>
  );
};

export default AppLayout;
