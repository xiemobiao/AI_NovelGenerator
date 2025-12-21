# AI Novel Generator - Web Frontend

AI驱动的小说生成器Web前端界面

## 🚀 技术栈

- **React 18** - 现代化UI库
- **TypeScript** - 类型安全
- **Vite** - 极速构建工具
- **Ant Design 5** - 企业级UI组件库
- **Zustand** - 轻量级状态管理
- **React Router 6** - 路由管理
- **Axios** - HTTP客户端
- **Monaco Editor** - 代码编辑器
- **ECharts** - 数据可视化

## 📦 功能模块

### ✅ 已实现
- ✅ 仪表板（项目管理、统计信息）
- ✅ 小说架构编辑器
- ✅ 章节编辑器（Monaco Editor集成）
- ✅ 长篇小说管理
- ✅ 数据可视化
- ✅ 设置页面（LLM配置）
- ✅ 布局和路由
- ✅ API客户端封装
- ✅ 状态管理
- ✅ 任务进度跟踪

### 🔨 开发中
- 🔨 章节蓝图编辑器（完善）
- 🔨 长篇小说管理（完善）
- 🔨 实时协作
- 🔨 用户认证

## 🛠️ 开发

### 安装依赖
```bash
cd web-frontend
npm install
```

### 开发模式
```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本
```bash
npm run build
```

构建产物在 `dist/` 目录

### 预览生产版本
```bash
npm run preview
```

## 📁 项目结构

```
web-frontend/
├── src/
│   ├── components/       # 通用组件
│   │   └── Layout.tsx    # 主布局
│   ├── pages/            # 页面组件
│   │   ├── Dashboard.tsx           # 仪表板
│   │   ├── ArchitectureEditor.tsx  # 架构编辑器
│   │   ├── BlueprintEditor.tsx     # 蓝图编辑器
│   │   ├── ChapterEditor.tsx       # 章节编辑器
│   │   ├── LongNovelManager.tsx    # 长篇管理
│   │   ├── Visualizations.tsx      # 可视化
│   │   └── Settings.tsx            # 设置
│   ├── services/         # 服务层
│   │   └── api.ts        # API客户端
│   ├── store/            # 状态管理
│   │   └── useAppStore.ts
│   ├── types/            # TypeScript类型
│   │   └── index.ts
│   ├── utils/            # 工具函数
│   ├── App.tsx           # 应用主组件
│   ├── App.css           # 应用样式
│   ├── main.tsx          # 入口文件
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── index.html            # HTML模板
├── vite.config.ts        # Vite配置
├── tsconfig.json         # TypeScript配置
└── package.json          # 项目配置
```

## 🔌 API集成

前端通过Axios与后端FastAPI通信，所有API请求通过 `/api/v1` 代理：

```typescript
// 配置在 vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 🎨 主要功能说明

### 1. 仪表板
- 项目列表和管理
- 实时任务进度
- 统计信息
- 快速操作

### 2. 小说架构编辑器
- 架构设计和编辑
- AI生成架构
- 保存和加载

### 3. 章节编辑器
- Monaco Editor集成
- 章节列表
- 生成章节
- 定稿功能
- 实时字数统计

### 4. 长篇小说管理
- 卷册管理
- 情节线追踪
- 质量报告

### 5. 数据可视化
- 情节线时间轴
- 角色关系图
- 质量热力图

### 6. 设置
- LLM配置
- Embedding配置
- 测试连接

## 📝 开发指南

### 添加新页面

1. 在 `src/pages/` 创建新组件
2. 在 `src/App.tsx` 添加路由
3. 在 `src/components/Layout.tsx` 添加菜单项

### 调用API

```typescript
import apiClient from '@/services/api';

// 示例：生成章节
const response = await apiClient.generateChapter({
  filepath: '/path/to/novel',
  chapter_num: 1,
  word_number: 3000,
});
```

### 使用状态管理

```typescript
import { useAppStore } from '@/store/useAppStore';

const MyComponent = () => {
  const { currentProject, setCurrentProject } = useAppStore();

  // 使用状态
  console.log(currentProject);

  // 更新状态
  setCurrentProject(newProject);
};
```

## 🚢 部署

### 使用Nginx

1. 构建项目
```bash
npm run build
```

2. 配置Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/web-frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📖 相关文档

- [React文档](https://react.dev/)
- [Ant Design文档](https://ant.design/)
- [Vite文档](https://vitejs.dev/)
- [TypeScript文档](https://www.typescriptlang.org/)
- [Zustand文档](https://github.com/pmndrs/zustand)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
