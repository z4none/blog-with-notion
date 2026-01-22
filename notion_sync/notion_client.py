"""
Notion API 客户端
处理与 Notion 数据库的交互
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from notion_client import Client
import httpx

from .config import NotionConfig


class NotionPost:
    """Notion 博客文章数据模型"""
    
    def __init__(self, page_data: Dict[str, Any]):
        # 安全检查
        if page_data is None:
            raise ValueError("page_data 不能为 None")
            
        self.page_data = page_data
        
        # 安全获取字段
        self.id = page_data.get("id", "")
        self.properties = page_data.get("properties", {})
        self.created_time = page_data.get("created_time", "")
        self.last_edited_time = page_data.get("last_edited_time", "")
        
    @property
    def title(self) -> str:
        """获取标题"""
        title_prop = self.properties.get("Title", self.properties.get("title", {}))
        
        # 安全检查
        if title_prop is None or title_prop.get("type") != "title":
            return ""
            
        title_content = title_prop.get("title", [])
        if title_content:
            # 合并所有文本片段
            full_title = "".join([item["text"]["content"] for item in title_content])
            return full_title
        return ""
       
    @property
    def slug(self) -> str:
        """获取 slug"""
        slug_prop = self.properties.get("Slug", self.properties.get("slug", {}))
        if slug_prop.get("type") == "rich_text" and slug_prop.get("rich_text"):
            # 合并所有文本片段
            full_slug = "".join([item["text"]["content"] for item in slug_prop["rich_text"]])
            return full_slug
        return ""
    
    @property
    def tags(self) -> List[str]:
        """获取标签（优先使用新的 Tag 属性，兼容旧的 Tags）"""
        tags_prop = self.properties.get("Tag", self.properties.get("Tags", self.properties.get("tags", {})))
        if tags_prop.get("type") == "multi_select":
            return [tag["name"] for tag in tags_prop.get("multi_select", [])]
        return []
    
    @property
    def status(self) -> str:
        """获取状态"""
        status_prop = self.properties.get("Status", self.properties.get("status", {}))
        
        # 安全检查
        if status_prop is None or status_prop.get("type") != "select":
            return "Draft"
            
        select_data = status_prop.get("select")
        if select_data is not None:
            return select_data.get("name", "Draft")
        return "Draft"
    
    @property
    def date(self) -> str:
        """获取日期"""
        date_prop = self.properties.get("Date", self.properties.get("date", {}))
        if date_prop.get("type") == "date" and date_prop.get("date"):
            return date_prop["date"]["start"]
        return self.created_time.split("T")[0]
    
    @property
    def excerpt(self) -> str:
        """获取摘要"""
        excerpt_prop = self.properties.get("Excerpt", self.properties.get("excerpt", {}))
        if excerpt_prop.get("type") == "rich_text" and excerpt_prop.get("rich_text"):
            # 合并所有文本片段
            full_excerpt = "".join([item["text"]["content"] for item in excerpt_prop["rich_text"]])
            return full_excerpt
        return ""
    
    @property
    def description(self) -> str:
        """获取描述（从 excerpt 或 description 属性）"""
        # 优先使用 excerpt
        if self.excerpt:
            return self.excerpt
            
        # 尝试从 description 属性获取
        desc_prop = self.properties.get("Description", self.properties.get("description", {}))
        if desc_prop.get("type") == "rich_text" and desc_prop.get("rich_text"):
            return "".join([item["text"]["content"] for item in desc_prop["rich_text"]])
        
        return ""
    
    @property
    def post_type(self) -> str:
        """获取文章类型 (Post 或 Page)"""
        type_prop = self.properties.get("Type", self.properties.get("type", {}))
        
        # 安全检查
        if type_prop is None:
            return "Post"
            
        if type_prop.get("type") == "select":
            select_data = type_prop.get("select")
            if select_data is not None:
                return select_data.get("name", "Post")
                
        return "Post"
    
    def is_published(self) -> bool:
        """检查是否为发布状态"""
        return self.status.lower() != "draft"
    
    def is_page(self) -> bool:
        """检查是否为页面"""
        return self.post_type == "Page"

    @property
    def cover_url(self) -> Optional[str]:
        """Get cover image URL if exists"""
        cover = self.page_data.get("cover")
        if cover is None:
            return None
            
        cover_type = cover.get("type")
        if cover_type == "external":
            return cover.get("external", {}).get("url")
        elif cover_type == "file":
            return cover.get("file", {}).get("url")
        return None

    @property
    def project_status(self) -> str:
        """获取项目状态"""
        status_prop = self.properties.get("Project Status", self.properties.get("project_status", {}))
        if status_prop.get("type") == "select":
            return status_prop.get("select", {}).get("name", "active")
        return "active"
    
    @property
    def technologies(self) -> List[str]:
        """获取技术栈"""
        tech_prop = self.properties.get("Technologies", self.properties.get("technologies", {}))
        if tech_prop.get("type") == "multi_select":
            return [tech["name"] for tech in tech_prop.get("multi_select", [])]
        return []
    
    @property
    def project_period(self) -> str:
        """获取项目时间"""
        period_prop = self.properties.get("Period", self.properties.get("period", {}))
        if period_prop.get("type") == "rich_text" and period_prop.get("rich_text"):
            return "".join([item["text"]["content"] for item in period_prop["rich_text"]])
        return ""
    
    @property
    def github_url(self) -> Optional[str]:
        """获取 GitHub 链接（优先使用 URL 属性，兼容 GitHub）"""
        github_prop = self.properties.get("URL", self.properties.get("GitHub", self.properties.get("github", {})))
        if github_prop.get("type") == "url":
            return github_prop.get("url")
        return None
    
    @property
    def demo_url(self) -> Optional[str]:
        """获取 Demo 链接"""
        demo_prop = self.properties.get("Demo", self.properties.get("demo", {}))
        if demo_prop.get("type") == "url":
            return demo_prop.get("url")
        return None
    
    @property
    def project_category(self) -> str:
        """获取项目分类"""
        category_prop = self.properties.get("Category", self.properties.get("category", {}))
        if category_prop.get("type") == "select":
            return category_prop.get("select", {}).get("name", "")
        return ""
    
    @property
    def project_type_name(self) -> str:
        """获取项目类型 (ProjectType)"""
        type_prop = self.properties.get("ProjectType", self.properties.get("project_type", {}))
        if type_prop.get("type") == "select":
            select_data = type_prop.get("select")
            if select_data:
                return select_data.get("name", "")
        return ""
    
    def is_project(self) -> bool:
        """检查是否为项目页面"""
        return self.post_type == "Project"
    
    def is_projects_page(self) -> bool:
        """检查是否为项目集合页面"""
        return self.post_type == "Projects"
    
    @property
    def database_id(self) -> Optional[str]:
        """获取页面关联的数据库ID"""
        return self.page_data.get("parent", {}).get("database_id") if self.page_data.get("parent") else None


class NotionProject:
    """Notion 项目数据模型 - 使用与Post统一的字段"""
    
    def __init__(self, page_data: Dict[str, Any]):
        self.page_data = page_data
        self.id = page_data["id"]
        self.properties = page_data["properties"]
        self.created_time = page_data["created_time"]
        self.last_edited_time = page_data["last_edited_time"]
        
        # 使用 NotionPost 的实例来复用所有属性获取逻辑
        self.post = NotionPost(page_data)
    
    # === 统一字段 - 直接复用NotionPost的逻辑 ===
    
    @property
    def title(self) -> str:
        """获取项目标题"""
        return self.post.title
    
    @property
    def description(self) -> str:
        """获取项目描述"""
        return self.post.description
    
    @property
    def status(self) -> str:
        """获取项目状态"""
        return self.post.status
    
    @property
    def tags(self) -> List[str]:
        """获取标签（作为技术栈）"""
        return self.post.tags
    
    @property
    def technologies(self) -> List[str]:
        """获取技术栈（与tags统一）"""
        return self.tags
    
    @property
    def excerpt(self) -> str:
        """获取摘要"""
        return self.post.excerpt
    
    @property
    def slug(self) -> str:
        """获取项目slug"""
        return self.post.slug or self._generate_slug()
    
    @property
    def date(self) -> str:
        """获取项目日期"""
        return self.post.date
    
    @property
    def cover_url(self) -> Optional[str]:
        """获取封面图片 URL（直接取页面封面）"""
        return self.post.cover_url
    
    # === 项目特有字段 ===
    
    @property
    def github_url(self) -> Optional[str]:
        """获取 GitHub 链接"""
        return self.post.github_url
    
    @property
    def demo_url(self) -> Optional[str]:
        """获取 Demo 链接"""
        return self.post.demo_url
    
    @property
    def period(self) -> str:
        """获取项目时间"""
        return self.post.project_period
    
    @property
    def category(self) -> str:
        """获取项目分类"""
        return self.post.project_category

    @property
    def project_type(self) -> str:
        """获取项目具体类型 (ProjectType)"""
        return self.post.project_type_name
    
    # === 方法 ===
    
    def _generate_slug(self) -> str:
        """从标题生成 slug"""
        import re
        slug = re.sub(r'[^\w\s-]', '', self.title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def is_active(self) -> bool:
        """检查项目是否为活跃状态"""
        return self.status.lower() not in ["draft", "archived"]
    
    def is_published(self) -> bool:
        """检查是否为发布状态"""
        return self.post.is_published()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "technologies": self.technologies,
            "tags": self.tags,
            "github": self.github_url,
            "demo": self.demo_url,
            "period": self.period,
            "category": self.category,
            "cover": self.cover_url,
            "slug": self.slug,
            "date": self.date,
            "excerpt": self.excerpt,
            "project_type": self.project_type
        }


class NotionClient:
    """Notion API 客户端封装"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        
        # 设置代理环境变量（这是最简单的方法）
        if config.proxy_url:
            import os
            os.environ['HTTP_PROXY'] = config.proxy_url
            os.environ['HTTPS_PROXY'] = config.proxy_url
            print(f'NotionClient init with proxy: {config.proxy_url}')
        else:
            # 清除代理环境变量
            import os
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)
            print(f'NotionClient init without proxy')
            
        self.client = Client(auth=config.token)
        print(f'NotionClient initialized successfully')
    
    def get_posts(self) -> List[NotionPost]:
        """获取博客文章列表"""
        try:
            print("正在从 Notion 获取文章...")
            
            # client.search 实际上是同步的！
            response = self.client.search(
                sort={
                    "timestamp": "last_edited_time",
                    "direction": "descending"
                }
            )
            
            results = response.get("results", [])
            
            # 过滤掉没有标题的文章
            valid_posts = []
            for page in results:
                post = NotionPost(page)
                # 检查是否有有效标题（不是默认的无标题文章）
                if post.title and post.title != "·":
                    valid_posts.append(post)
            
            print(f"找到 {len(valid_posts)} 篇文章")
            return valid_posts
            
        except Exception as e:
            print(f"获取文章失败: {e}")
            return []
    
    def get_page_content(self, page_id: str) -> str:
        """获取页面内容（正文）"""
        try:
            # 获取页面的 blocks（内容块）
            blocks = self.client.blocks.children.list(block_id=page_id)
            
            # 将 blocks 转换为 Markdown
            content_parts = []
            for block in blocks.get("results", []):
                content_parts.append(self._block_to_markdown(block))
            
            return "\n\n".join(content_parts)
            
        except Exception as e:
            print(f"获取页面内容失败: {e}")
            return ""
    
    def _block_to_markdown(self, block: Dict[str, Any]) -> str:
        """将 Notion block 转换为 Markdown"""
        block_type = block.get("type", "")
        
        if block_type == "paragraph":
            text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
            return text if text else ""
        
        elif block_type == "heading_1":
            text = self._extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
            return f"# {text}" if text else ""
        
        elif block_type == "heading_2":
            text = self._extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
            return f"## {text}" if text else ""
        
        elif block_type == "heading_3":
            text = self._extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
            return f"### {text}" if text else ""
        
        elif block_type == "bulleted_list_item":
            text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
            return f"- {text}" if text else ""
        
        elif block_type == "numbered_list_item":
            text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
            return f"1. {text}" if text else ""
        
        elif block_type == "code":
            text = self._extract_rich_text(block.get("code", {}).get("rich_text", []))
            language = block.get("code", {}).get("language", "")
            return f"```{language}\n{text}\n```" if text else ""
        
        elif block_type == "image":
            image_url = block.get("image", {}).get("file", {}).get("url", "") or \
                       block.get("image", {}).get("external", {}).get("url", "")
            return f"![image]({image_url})" if image_url else ""
        
        return ""
    
    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """从富文本中提取纯文本"""
        result = []
        for text_item in rich_text:
            content = text_item.get("text", {}).get("content", "")
            if text_item.get("text", {}).get("link"):
                url = text_item["text"]["link"]["url"]
                content = f"[{content}]({url})"
            
            # 处理格式
            if text_item.get("annotations", {}).get("bold"):
                content = f"**{content}**"
            if text_item.get("annotations", {}).get("italic"):
                content = f"*{content}*"
            if text_item.get("annotations", {}).get("strikethrough"):
                content = f"~~{content}~~"
            if text_item.get("annotations", {}).get("code"):
                content = f"`{content}`"
            
            result.append(content)
        
        return "".join(result)
    
    def get_database_pages(self, database_id: str) -> List[NotionPost]:
        """获取数据库中的所有页面（简化版本，通过搜索过滤）"""
        try:
            print(f"正在从数据库 {database_id} 获取项目...")
            
            # 获取所有页面，然后过滤
            all_posts = self.get_posts()
            db_posts = []
            
            for post in all_posts:
                if post.database_id == database_id and post.is_project():
                    db_posts.append(post)
            
            print(f"从数据库中找到 {len(db_posts)} 个项目")
            return db_posts
            
        except Exception as e:
            print(f"获取数据库内容失败: {e}")
            return []
    
    def get_projects(self) -> List[NotionProject]:
        """获取所有项目"""
        try:
            print("正在从 Notion 获取项目...")
            
            # 获取所有页面
            response = self.client.search(
                sort={
                    "timestamp": "last_edited_time",
                    "direction": "descending"
                }
            )
            
            # 检查响应是否有效
            if response is None:
                print("Notion API 返回了 None 响应")
                return []
            
            results = response.get("results", [])
            
            if not results:
                print("没有找到任何页面")
                return []
            
            # 过滤项目
            projects = []
            for page in results:
                try:
                    # 检查page是否有效
                    if page is None:
                        continue
                    
                    post = NotionPost(page)
                    
                    # 检查是否为项目页面
                    if post.is_project() and post.title and post.title != "·":
                        projects.append(NotionProject(page))
                        
                except Exception as page_error:
                    print(f"处理页面时出错: {page_error}")
                    continue
            
            print(f"找到 {len(projects)} 个项目")
            return projects
            
        except Exception as e:
            print(f"获取项目失败: {e}")
            return []
    
    def get_projects_from_database(self, database_id: str) -> List[NotionProject]:
        """从指定数据库获取项目"""
        try:
            print(f"正在从数据库 {database_id} 获取项目...")
            
            # 获取所有页面，然后过滤
            all_projects = self.get_projects()
            db_projects = []
            
            for project in all_projects:
                if project.post.database_id == database_id:
                    db_projects.append(project)
            
            print(f"从数据库中找到 {len(db_projects)} 个项目")
            return db_projects
            
        except Exception as e:
            print(f"获取数据库项目失败: {e}")
            return []