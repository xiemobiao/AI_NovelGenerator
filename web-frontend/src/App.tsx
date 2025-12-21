// App.tsx
// 主应用组件

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// 页面组件
import Dashboard from './pages/Dashboard';
import ArchitectureEditor from './pages/ArchitectureEditor';
import BlueprintEditor from './pages/BlueprintEditor';
import ChapterEditor from './pages/ChapterEditor';
import LongNovelManager from './pages/LongNovelManager';
import Visualizations from './pages/Visualizations';
import Settings from './pages/Settings';
import Layout from './components/Layout';

import './App.css';

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="architecture" element={<ArchitectureEditor />} />
              <Route path="blueprint" element={<BlueprintEditor />} />
              <Route path="chapters" element={<ChapterEditor />} />
              <Route path="long-novel" element={<LongNovelManager />} />
              <Route path="visualizations" element={<Visualizations />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;
