// types/index.ts
// 核心类型定义

export interface Project {
  id: string;
  name: string;
  filepath: string;
  genre: string;
  num_chapters: number;
  created_at: string;
  updated_at: string;
  status: 'draft' | 'generating' | 'completed';
}

export interface NovelArchitecture {
  topic: string;
  genre: string;
  main_characters: string;
  story_background: string;
  plot_outline: string;
  core_conflicts: string;
  writing_style: string;
}

export interface ChapterBlueprint {
  chapter_number: number;
  title: string;
  summary: string;
  key_events: string[];
  characters: string[];
}

export interface Chapter {
  chapter_number: number;
  title: string;
  content: string;
  word_count: number;
  status: 'draft' | 'final';
  created_at: string;
  updated_at: string;
}

export interface GenerationTask {
  task_id: string;
  task_type: 'architecture' | 'blueprint' | 'chapter' | 'finalize' | 'export';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  result?: any;
  error?: string;
}

export interface ExportRequest {
  filepath: string;
  format: 'txt' | 'epub' | 'pdf' | 'docx';
  metadata: {
    title: string;
    author: string;
    genre?: string;
    description?: string;
  };
  start_chapter?: number;
  end_chapter?: number;
}

export interface Plotline {
  plot_id: string;
  title: string;
  importance: 'main' | 'major' | 'minor' | 'background';
  start_chapter: number;
  expected_end_chapter: number;
  actual_end_chapter?: number;
  status: 'planned' | 'active' | 'suspended' | 'resolved' | 'abandoned';
  description: string;
  milestones: Milestone[];
  conflicts: Conflict[];
}

export interface Milestone {
  chapter: number;
  description: string;
  achieved: boolean;
}

export interface Conflict {
  conflict_id: string;
  description: string;
  chapter: number;
  resolved: boolean;
}

export interface QualityReport {
  total_chapters: number;
  total_characters: number;
  total_locations: number;
  total_items: number;
  unresolved_foreshadowing: number;
  character_issues: string[];
  location_issues: string[];
  missing_information: string[];
  main_characters: Array<{
    name: string;
    appearances: number;
    first_chapter: number;
    last_chapter: number;
  }>;
}

export interface VisualizationData {
  plotlines: Plotline[];
  characters: Map<string, any>;
  quality_metrics: number[][];
}

export interface LLMConfig {
  interface_format: string;
  api_key: string;
  base_url: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
}

export interface EmbeddingConfig {
  interface_format: string;
  api_key: string;
  base_url: string;
  model_name: string;
  retrieval_k: number;
}

export interface AppConfig {
  llm: LLMConfig;
  embedding: EmbeddingConfig;
  other_params: {
    topic: string;
    genre: string;
    num_chapters: number;
    word_number: number;
    filepath: string;
  };
}
