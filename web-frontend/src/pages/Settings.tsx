// pages/Settings.tsx
import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Button,
  Space,
  message,
  Tabs,
  Select,
} from 'antd';
import { SaveOutlined, CheckOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/useAppStore';
import apiClient from '@/services/api';

const Settings: React.FC = () => {
  const { setConfig } = useAppStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const cfg = await apiClient.getConfig();
      setConfig(cfg);
      form.setFieldsValue(cfg);
    } catch (error) {
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values: any) => {
    try {
      setLoading(true);
      await apiClient.updateConfig(values);
      setConfig(values);
      message.success('保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTestLLM = async () => {
    try {
      setTesting(true);
      const llmConfig = form.getFieldValue('llm');
      const result = await apiClient.testLLMConfig(llmConfig);

      if (result.success) {
        message.success('LLM配置测试成功');
      } else {
        message.error(`测试失败: ${result.message}`);
      }
    } catch (error) {
      message.error('测试失败');
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card title="设置">
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
      >
        <Tabs
          items={[
            {
              key: 'llm',
              label: 'LLM配置',
              children: (
                <>
                  <Form.Item
                    label="接口类型"
                    name={['llm', 'interface_format']}
                  >
                    <Select>
                      <Select.Option value="OpenAI">OpenAI</Select.Option>
                      <Select.Option value="Gemini">Google Gemini</Select.Option>
                      <Select.Option value="Azure">Azure OpenAI</Select.Option>
                      <Select.Option value="Claude">Anthropic Claude</Select.Option>
                    </Select>
                  </Form.Item>

                  <Form.Item label="API Key" name={['llm', 'api_key']}>
                    <Input.Password placeholder="sk-..." />
                  </Form.Item>

                  <Form.Item label="Base URL" name={['llm', 'base_url']}>
                    <Input placeholder="https://api.openai.com/v1" />
                  </Form.Item>

                  <Form.Item label="模型名称" name={['llm', 'model_name']}>
                    <Input placeholder="gpt-4" />
                  </Form.Item>

                  <Form.Item label="Temperature" name={['llm', 'temperature']}>
                    <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>

                  <Form.Item label="Max Tokens" name={['llm', 'max_tokens']}>
                    <InputNumber min={1} max={100000} style={{ width: '100%' }} />
                  </Form.Item>

                  <Form.Item label="Timeout (秒)" name={['llm', 'timeout']}>
                    <InputNumber min={1} max={3600} style={{ width: '100%' }} />
                  </Form.Item>

                  <Space>
                    <Button
                      icon={<CheckOutlined />}
                      onClick={handleTestLLM}
                      loading={testing}
                    >
                      测试连接
                    </Button>
                  </Space>
                </>
              ),
            },
            {
              key: 'embedding',
              label: 'Embedding配置',
              children: <div>Embedding配置开发中...</div>,
            },
          ]}
        />

        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={loading}
          >
            保存配置
          </Button>
        </div>
      </Form>
    </Card>
  );
};

export default Settings;
