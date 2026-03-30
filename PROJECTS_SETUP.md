# Notion Projects Table View 设置指南

## 🎯 总体思路

使用 Notion 的 Table View 来统一管理项目，通过数据库关联自动生成项目展示页面。

## 📋 步骤 1: 在 Notion 中创建项目数据库

1. **创建新数据库**
   - 在 Notion 中创建新的 Database
   - 选择 "Table" 视图

2. **设置数据库属性**

| 属性名称 | 类型 | 说明 | 示例 |
|---------|------|------|------|
| Title | Title | 项目名称 | "我的博客系统" |
| Description | Rich text | 项目描述 | "基于 Hugo 的个人博客系统" |
| Status | Select | 项目状态 | Active, Completed, Development, Archived |
| Technologies | Multi-select | 技术栈 | React, Node.js, TypeScript |
| GitHub | URL | GitHub 链接 | https://github.com/... |
| Demo | URL | 在线演示 | https://demo.example.com |
| Period | Rich text | 项目时间 | "2023.01 - 2023.06" |
| Category | Select | 项目分类 | Web App, Mobile App, CLI Tool |
| Cover | Files & Media | 封面图片 | [上传图片] |

## 📋 步骤 2: 创建项目集合页面

1. **在数据库中创建新页面**
   - 在主页面下创建子页面
   - 设置 Type 属性为 "Projects"

2. **关联数据库**
   - 将项目集合页面设置为刚才创建的数据库的页面
   - 或者在数据库中创建这个页面

## 📋 步骤 3: 添加项目数据

在项目数据库的 Table View 中添加项目：

| Title | Status | Technologies | GitHub | Demo | Period | Category |
|-------|--------|-------------|--------|------|--------|----------|
| 博客系统 | Completed | Hugo, TypeScript | https://github.com/... | https://blog.example.com | 2023.01 - 2023.06 | Web App |
| 任务管理器 | Active | React, Node.js | https://github.com/... | - | 2023.06 - 2023.08 | Web App |
| 天气应用 | Development | React Native | https://github.com/... | - | 2023.08 - Present | Mobile App |

## 📋 步骤 4: 配置同步

1. **运行同步命令**
   ```bash
   python -m notion_sync
   ```

2. **生成的文件结构**
   ```
   content/
   ├── projects.md                 # 项目集合页（从数据库生成）
   └── projects/
       ├── blog-system.md         # 单独项目详情页
       ├── task-manager.md
       └── weather-app.md
   ```

## 🎨 自定义样式

生成的项目页面将包含：

- ✅ **响应式卡片布局**
- ✅ **状态标签** (Active, Completed, Development, Archived)
- ✅ **技术栈标签** (彩色渐变)
- ✅ **GitHub 和 Demo 链接**
- ✅ **悬停动画效果**
- ✅ **滚动进入动画**

## 🔧 高级配置

### 1. 自定义状态颜色
在 CSS 中修改状态颜色：
```css
.status-active { background: #10b981; }
.status-completed { background: #3b82f6; }
.status-development { background: #f59e0b; }
.status-archived { background: #6b7280; }
```

### 2. 添加自定义字段
在 Notion 数据库中添加新属性，然后在模板中引用：
```html
{{ if .Params.custom_field }}
<p>{{ .Params.custom_field }}</p>
{{ end }}
```

### 3. 调整布局
修改 `projects.css` 中的网格设置：
```css
.projects-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
}
```

## 📱 使用效果

访问 `/projects/` 页面，你将看到：

1. **项目集合页**：所有项目的卡片式展示
2. **项目详情页**：点击项目卡片查看详细信息
3. **Table View 管理后台**：在 Notion 中通过表格统一管理

这种方式的优势：
- 🎯 **直观管理**：在 Notion 表格中批量编辑项目
- 🔄 **自动同步**：修改后自动更新网站
- 📊 **数据可视化**：Table View 提供清晰的概览
- 🔍 **易于筛选**：按状态、技术栈等快速筛选