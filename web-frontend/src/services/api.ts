// services/api.ts
// API客户端封装

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  NovelArchitecture,
  ChapterBlueprint,
  Chapter,
  GenerationTask,
  ExportRequest,
  QualityReport,
  AppConfig,
  Plotline,
} from '@/types';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      timeout: 600000, // 10分钟超时
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // ==================== 健康检查 ====================
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // ==================== 小说架构 ====================
  async generateArchitecture(params: {
    topic: string;
    genre: string;
    num_chapters: number;
    word_number: number;
    filepath: string;
    user_guidance?: string;
  }): Promise<{ task_id: string }> {
    const response = await this.client.post('/novel/architecture', params);
    return response.data;
  }

  async getArchitecture(filepath: string): Promise<NovelArchitecture> {
    const response = await this.client.get('/novel/architecture', {
      params: { filepath },
    });
    return response.data;
  }

  // ==================== 章节蓝图 ====================
  async generateBlueprint(params: {
    filepath: string;
    num_chapters: number;
    user_guidance?: string;
  }): Promise<{ task_id: string }> {
    const response = await this.client.post('/novel/blueprint', params);
    return response.data;
  }

  async getBlueprint(filepath: string): Promise<ChapterBlueprint[]> {
    const response = await this.client.get('/novel/blueprint', {
      params: { filepath },
    });
    return response.data;
  }

  // ==================== 章节生成 ====================
  async generateChapter(params: {
    filepath: string;
    chapter_num: number;
    word_number: number;
    characters_involved?: string;
    key_items?: string;
    scene_location?: string;
    time_constraint?: string;
    user_guidance?: string;
  }): Promise<{ task_id: string }> {
    const response = await this.client.post('/novel/chapter/draft', params);
    return response.data;
  }

  async getChapter(
    filepath: string,
    chapter_num: number
  ): Promise<Chapter> {
    const response = await this.client.get('/novel/chapter', {
      params: { filepath, chapter_num },
    });
    return response.data;
  }

  async listChapters(filepath: string): Promise<Chapter[]> {
    const response = await this.client.get('/novel/chapters', {
      params: { filepath },
    });
    return response.data;
  }

  async updateChapter(
    filepath: string,
    chapter_num: number,
    content: string
  ): Promise<void> {
    await this.client.put('/novel/chapter', {
      filepath,
      chapter_num,
      content,
    });
  }

  async finalizeChapter(params: {
    filepath: string;
    chapter_num: number;
    word_number: number;
  }): Promise<{ task_id: string }> {
    const response = await this.client.post('/novel/chapter/finalize', params);
    return response.data;
  }

  // ==================== 导出 ====================
  async exportNovel(request: ExportRequest): Promise<{ task_id: string }> {
    const response = await this.client.post('/novel/export', request);
    return response.data;
  }

  async downloadExport(filepath: string, format: string): Promise<Blob> {
    const response = await this.client.get('/novel/export/download', {
      params: { filepath, format },
      responseType: 'blob',
    });
    return response.data;
  }

  // ==================== 任务管理 ====================
  async getTask(taskId: string): Promise<GenerationTask> {
    const response = await this.client.get(`/task/${taskId}`);
    return response.data;
  }

  async listTasks(): Promise<GenerationTask[]> {
    const response = await this.client.get('/tasks');
    return response.data.tasks || [];
  }

  // ==================== 质量检查 ====================
  async checkConsistency(params: {
    filepath: string;
    chapter_num: number;
  }): Promise<{ report: string }> {
    const response = await this.client.post('/novel/consistency', params);
    return response.data;
  }

  async getQualityReport(filepath: string): Promise<QualityReport> {
    const response = await this.client.get('/novel/quality', {
      params: { filepath },
    });
    return response.data;
  }

  // ==================== 长篇小说系统 ====================
  async getPlotlines(filepath: string): Promise<Plotline[]> {
    const response = await this.client.get('/longnovel/plotlines', {
      params: { filepath },
    });
    return response.data;
  }

  async createPlotline(filepath: string, plotline: Partial<Plotline>): Promise<Plotline> {
    const response = await this.client.post('/longnovel/plotlines', {
      filepath,
      ...plotline,
    });
    return response.data;
  }

  async updatePlotline(
    filepath: string,
    plotId: string,
    updates: Partial<Plotline>
  ): Promise<Plotline> {
    const response = await this.client.put(`/longnovel/plotlines/${plotId}`, {
      filepath,
      ...updates,
    });
    return response.data;
  }

  async getContextReport(filepath: string): Promise<any> {
    const response = await this.client.get('/longnovel/context', {
      params: { filepath },
    });
    return response.data;
  }

  // ==================== 可视化 ====================
  async generateVisualization(
    filepath: string,
    type: 'timeline' | 'relationship' | 'heatmap' | 'all'
  ): Promise<{ files: string[] }> {
    const response = await this.client.post('/visualizations/generate', {
      filepath,
      type,
    });
    return response.data;
  }

  async getVisualizationImage(filepath: string, filename: string): Promise<Blob> {
    const response = await this.client.get('/visualizations/image', {
      params: { filepath, filename },
      responseType: 'blob',
    });
    return response.data;
  }

  // ==================== 配置管理 ====================
  async getConfig(): Promise<AppConfig> {
    const response = await this.client.get('/config');
    return response.data;
  }

  async updateConfig(config: Partial<AppConfig>): Promise<void> {
    await this.client.put('/config', config);
  }

  async testLLMConfig(llmConfig: any): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/config/test-llm', llmConfig);
    return response.data;
  }

  async testEmbeddingConfig(embeddingConfig: any): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/config/test-embedding', embeddingConfig);
    return response.data;
  }

  // ==================== 知识库 ====================
  async importKnowledge(filepath: string, file: File): Promise<{ success: boolean }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filepath', filepath);

    const response = await this.client.post('/knowledge/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async clearVectorStore(filepath: string): Promise<{ success: boolean }> {
    const response = await this.client.post('/knowledge/clear', { filepath });
    return response.data;
  }
}

// 导出单例
export const apiClient = new APIClient();
export default apiClient;
