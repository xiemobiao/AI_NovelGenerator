// App.tsx
// 主应用组件

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme, App as AntApp, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAppStore } from '@/store/useAppStore';

// 立即加载的关键组件
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';

// 懒加载页面组件（代码分割）
const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ArchitectureEditor = lazy(() => import('./pages/ArchitectureEditor'));
const BlueprintEditor = lazy(() => import('./pages/BlueprintEditor'));
const ChapterEditor = lazy(() => import('./pages/ChapterEditor'));
const LongNovelManager = lazy(() => import('./pages/LongNovelManager'));
const Visualizations = lazy(() => import('./pages/Visualizations'));
const ExportPage = lazy(() => import('./pages/ExportPage'));
const Settings = lazy(() => import('./pages/Settings'));

import './App.css';

// 加载中组件
const PageLoader: React.FC = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh'
  }}>
    <Spin size="large" tip="加载中..." />
  </div>
);

const App: React.FC = () => {
  const { isDarkMode } = useAppStore();

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <Layout />
                  </PrivateRoute>
                }
              >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="architecture" element={<ArchitectureEditor />} />
                <Route path="blueprint" element={<BlueprintEditor />} />
                <Route path="chapters" element={<ChapterEditor />} />
                <Route path="long-novel" element={<LongNovelManager />} />
                <Route path="visualizations" element={<Visualizations />} />
                <Route path="export" element={<ExportPage />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;
