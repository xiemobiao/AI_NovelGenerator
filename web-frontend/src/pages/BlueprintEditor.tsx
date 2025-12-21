// pages/BlueprintEditor.tsx
import React from 'react';
import { Card, Empty, Button } from 'antd';
import { RocketOutlined } from '@ant-design/icons';

const BlueprintEditor: React.FC = () => {
  return (
    <Card title="章节蓝图">
      <Empty description="功能开发中..." />
      <div style={{ textAlign: 'center', marginTop: 16 }}>
        <Button type="primary" icon={<RocketOutlined />}>
          生成章节蓝图
        </Button>
      </div>
    </Card>
  );
};

export default BlueprintEditor;
