# FuzzTest 前端 (Vite + Vue 3)

本前端使用 Vite + Vue 3 + Tailwind CSS 构建。

## 项目结构

```
frontend/
├── index.html              # HTML 入口文件
├── package.json            # 项目依赖
├── vite.config.js          # Vite 配置
├── tailwind.config.js      # Tailwind CSS 配置
├── postcss.config.js       # PostCSS 配置
├── src/
│   ├── main.js             # 应用入口点
│   ├── App.vue             # 根组件
│   ├── style.css           # 全局样式
│   ├── api/
│   │   └── index.js        # API 服务
│   ├── stores/
│   │   └── testStore.js    # 状态管理
│   ├── components/
│   │   ├── Sidebar.vue     # 侧边栏组件
│   │   ├── Header.vue      # 顶部导航组件
│   │   └── HelpModal.vue   # 帮助模态框
│   └── views/
│       ├── Dashboard.vue   # 仪表盘页面
│       ├── Analysis.vue    # 批次分析报告页面
│       ├── Config.vue      # 系统配置页面
│       └── Logs.vue        # 运行日志页面
└── public/
    └── vite.svg            # 静态资源
```

## 开发模式

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动，并自动代理 API 请求到后端服务器（默认 `http://localhost:5000`）。

### 3. 启动后端服务器

在另一个终端中运行：

```bash
python start.py
```

## 生产构建

### 1. 构建前端

```bash
cd frontend
npm run build
```

构建产物将输出到 `frontend/dist/` 目录。

### 2. 运行后端

后端会自动检测并服务 `frontend/dist/` 目录中的静态文件：

```bash
python start.py
```

访问 `http://localhost:5000` 即可使用。

## API 接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/control/start` | POST | 启动测试 |
| `/control/stop` | POST | 停止测试 |
| `/control/status` | GET | 获取运行状态 |
| `/logs/tail` | GET | 获取最新日志 |
| `/export` | GET | 导出测试数据 |
| `/config` | GET | 获取配置 |
| `/config` | POST | 保存配置 |

## 技术栈

- **Vue 3** - 前端框架
- **Vue Router** - 路由管理
- **Vite** - 构建工具
- **Tailwind CSS** - CSS 框架
- **Axios** - HTTP 客户端
- **Font Awesome** - 图标库
