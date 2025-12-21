// store/useAppStore.ts
// 全局状态管理

import { create } from 'zustand';
import type {
  User,
  Project,
  NovelArchitecture,
  ChapterBlueprint,
  Chapter,
  GenerationTask,
  AppConfig,
  Plotline,
  QualityReport,
} from '@/types';

interface AppState {
  // ==================== 用户认证 ====================
  currentUser: User | null;
  token: string | null;
  setUser: (user: User | null, token?: string | null) => void;
  logout: () => void;
  isAuthenticated: () => boolean;

  // ==================== 当前项目 ====================
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;

  // ==================== 小说架构 ====================
  architecture: NovelArchitecture | null;
  setArchitecture: (architecture: NovelArchitecture | null) => void;

  // ==================== 章节蓝图 ====================
  blueprints: ChapterBlueprint[];
  setBlueprints: (blueprints: ChapterBlueprint[]) => void;

  // ==================== 章节列表 ====================
  chapters: Chapter[];
  setChapters: (chapters: Chapter[]) => void;
  updateChapter: (chapterNum: number, content: string) => void;

  // ==================== 当前编辑的章节 ====================
  currentChapter: Chapter | null;
  setCurrentChapter: (chapter: Chapter | null) => void;

  // ==================== 任务列表 ====================
  tasks: GenerationTask[];
  setTasks: (tasks: GenerationTask[]) => void;
  addTask: (task: GenerationTask) => void;
  updateTask: (taskId: string, updates: Partial<GenerationTask>) => void;

  // ==================== 情节线 ====================
  plotlines: Plotline[];
  setPlotlines: (plotlines: Plotline[]) => void;
  addPlotline: (plotline: Plotline) => void;
  updatePlotline: (plotId: string, updates: Partial<Plotline>) => void;

  // ==================== 质量报告 ====================
  qualityReport: QualityReport | null;
  setQualityReport: (report: QualityReport | null) => void;

  // ==================== 应用配置 ====================
  config: AppConfig | null;
  setConfig: (config: AppConfig | null) => void;

  // ==================== UI状态 ====================
  loading: boolean;
  setLoading: (loading: boolean) => void;

  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;

  isDarkMode: boolean;
  setIsDarkMode: (isDark: boolean) => void;
  toggleTheme: () => void;

  // ==================== 通知 ====================
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    description?: string;
  }>;
  addNotification: (notification: {
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    description?: string;
  }) => void;
  removeNotification: (id: string) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // ==================== 初始状态 ====================
  currentUser: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!) : null,
  token: localStorage.getItem('token'),
  currentProject: null,
  architecture: null,
  blueprints: [],
  chapters: [],
  currentChapter: null,
  tasks: [],
  plotlines: [],
  qualityReport: null,
  config: null,
  loading: false,
  sidebarCollapsed: false,
  isDarkMode: localStorage.getItem('theme') === 'dark',
  notifications: [],

  // ==================== Actions ====================
  setUser: (user, token) => {
    if (user && token) {
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('token', token);
      set({ currentUser: user, token });
    } else {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      set({ currentUser: null, token: null });
    }
  },

  logout: () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    set({
      currentUser: null,
      token: null,
      currentProject: null,
      architecture: null,
      blueprints: [],
      chapters: [],
      currentChapter: null,
      tasks: [],
      plotlines: [],
      qualityReport: null,
    });
  },

  isAuthenticated: () => {
    const state = get();
    return !!(state.currentUser && state.token);
  },

  setCurrentProject: (project) => set({ currentProject: project }),

  setArchitecture: (architecture) => set({ architecture }),

  setBlueprints: (blueprints) => set({ blueprints }),

  setChapters: (chapters) => set({ chapters }),

  updateChapter: (chapterNum, content) =>
    set((state) => ({
      chapters: state.chapters.map((ch) =>
        ch.chapter_number === chapterNum
          ? { ...ch, content, word_count: content.length }
          : ch
      ),
    })),

  setCurrentChapter: (chapter) => set({ currentChapter: chapter }),

  setTasks: (tasks) => set({ tasks }),

  addTask: (task) =>
    set((state) => ({
      tasks: [task, ...state.tasks],
    })),

  updateTask: (taskId, updates) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.task_id === taskId ? { ...task, ...updates } : task
      ),
    })),

  setPlotlines: (plotlines) => set({ plotlines }),

  addPlotline: (plotline) =>
    set((state) => ({
      plotlines: [...state.plotlines, plotline],
    })),

  updatePlotline: (plotId, updates) =>
    set((state) => ({
      plotlines: state.plotlines.map((plot) =>
        plot.plot_id === plotId ? { ...plot, ...updates } : plot
      ),
    })),

  setQualityReport: (report) => set({ qualityReport: report }),

  setConfig: (config) => set({ config }),

  setLoading: (loading) => set({ loading }),

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  setIsDarkMode: (isDark) => {
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    set({ isDarkMode: isDark });
  },

  toggleTheme: () =>
    set((state) => {
      const newTheme = !state.isDarkMode;
      localStorage.setItem('theme', newTheme ? 'dark' : 'light');
      return { isDarkMode: newTheme };
    }),

  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          ...notification,
          id: `notification-${Date.now()}-${Math.random()}`,
        },
      ],
    })),

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));

export default useAppStore;
