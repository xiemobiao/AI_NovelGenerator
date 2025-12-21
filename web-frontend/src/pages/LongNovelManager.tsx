// pages/LongNovelManager.tsx
import React from 'react';
import { Card, Tabs } from 'antd';

const LongNovelManager: React.FC = () => {
  const items = [
    {
      key: 'volumes',
      label: '卷册管理',
      children: <div style={{ padding: 24 }}>卷册管理功能开发中...</div>,
    },
    {
      key: 'plotlines',
      label: '情节线',
      children: <div style={{ padding: 24 }}>情节线管理功能开发中...</div>,
    },
    {
      key: 'quality',
      label: '质量报告',
      children: <div style={{ padding: 24 }}>质量报告功能开发中...</div>,
    },
  ];

  return (
    <Card title="长篇小说管理">
      <Tabs items={items} />
    </Card>
  );
};

export default LongNovelManager;
