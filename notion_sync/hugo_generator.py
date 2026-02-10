"""
Hugo 内容生成器
将 Notion 数据转换为 Hugo 兼容的 Markdown 文件
"""

import asyncio
import httpx
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import frontmatter
from pydantic import BaseModel

from .config import HugoConfig
from .notion_client import NotionPost, NotionClient, NotionProject


class HugoGenerator:
    """Hugo 内容生成器"""
    
    def __init__(self, config: HugoConfig):
        self.config = config
        
        # 确保目录存在
        self.config.content_dir.mkdir(parents=True, exist_ok=True)
        self.config.pages_dir.mkdir(parents=True, exist_ok=True)
        self.config.images_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir = Path(self.config.static_dir)
        self.images_dir = Path(self.config.images_dir)
        
        self.http_client = httpx.AsyncClient()
    
    async def generate_posts(self, posts: List[NotionPost], notion_client: NotionClient) -> int:
        """生成 Hugo 文章"""
        generated_count = 0
        
        print(f"开始生成 {len(posts)} 篇文章...")
        
        for i, post in enumerate(posts, 1):
            try:
                print(f"处理第 {i}/{len(posts)} 篇: {post.title}")
                
                # 获取文章内容
                content = notion_client.get_page_content(post.id)
                
                # 生成文件
                self._generate_post_file(post, content)
                generated_count += 1
                
            except Exception as e:
                print(f"[ERROR] 生成失败 {post.title}: {e}")
        
        # TODO: 临时禁用项目集合页面生成，先专注于基本同步
        # self._generate_projects_pages(posts, notion_client)
        print("[INFO] Project pages generation temporarily disabled")
        
        print(f"文章生成完成，共 {generated_count} 篇")
        # self.http_client.aclose()  # 不需要关闭，因为它可能是同步的客户端
        return generated_count
        
    def _download_cover_image(self, image_url: str, post_slug: str) -> str:
        """Download cover image and return relative path"""
        try:
            # Extract image ID for consistent naming
            image_id = self._extract_notion_image_id(image_url)
            if not image_id:
                image_id = str(hash(image_url))
            
            # Get file extension from URL or content type
            ext = ".jpg"  # default
            if "." in image_url:
                url_ext = image_url.split(".")[-1].lower()
                if url_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                    ext = f".{url_ext}"
            
            # Download image
            filename = f"{post_slug}-{image_id}{ext}"
            local_path = self.images_dir / filename
            
            # Use synchronous download
            import httpx
            response = httpx.get(image_url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            
            with open(local_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
            
            return f"/images/{filename}"
        except Exception as e:
            print(f"[ERROR] Failed to download cover image: {e}")
            raise

    def _generate_post_file(self, post: NotionPost, content: str):
        """生成单篇文章"""
        # 处理内容中的图片
        processed_content = self._process_images(content, post.slug)

        cover_path = None
        if post.cover_url:
            try:
                cover_path = self._download_cover_image(post.cover_url, post.slug)
            except Exception as e:
                print(f"[WARNING] Failed to download cover image: {e}")
        
        # 创建 front matter
        front_matter = {
            "title": post.title,
            "date": post.date,
            "lastmod": post.last_edited_time.split("T")[0],
            "slug": post.slug,
            "tags": post.tags,
            "draft": not post.is_published(),
            "summary": post.excerpt,
            "description": post.excerpt,  # 添加 description 字段用于主题显示
            "notion_id": post.id,
            "type": post.post_type,
        }
        
        # 添加项目特定属性
        if post.is_project():
            if post.project_status:
                front_matter["status"] = post.project_status
            if post.technologies:
                front_matter["technologies"] = post.technologies
            if post.project_period:
                front_matter["period"] = post.project_period
            if post.github_url:
                front_matter["github"] = post.github_url
            if post.demo_url:
                front_matter["demo"] = post.demo_url
            if post.project_category:
                front_matter["category"] = post.project_category

        if cover_path:
            front_matter["image"] = cover_path
        
        # 创建 post 对象
        post_obj = frontmatter.Post(processed_content, **front_matter)
        
        # 根据文章类型选择目录和布局
        if post.is_page():
            if post.post_type == "project":
                # 独立项目页面
                front_matter["layout"] = "single-project"
                # 创建 projects 子目录
                projects_dir = self.config.pages_dir / "projects"
                projects_dir.mkdir(parents=True, exist_ok=True)
                filepath = projects_dir / f"{post.slug}.md"
            elif post.post_type == "projects":
                # 项目集合页面
                front_matter["layout"] = "projects"
                filepath = self.config.pages_dir / f"{post.slug}.md"
            else:
                # 普通 Page 类型直接放在 content 目录下
                filepath = self.config.pages_dir / f"{post.slug}.md"
        else:
            # Post 类型放在 posts 目录下
            filepath = self.config.content_dir / f"{post.slug}.md"
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post_obj))
        
        print(f"[OK] 生成文章: {filepath.name}")
    
    def _process_images(self, content: str, post_slug: str) -> str:
        """处理文章中的图片（简化同步版本）"""
        # 匹配 Markdown 图片语法
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def download_and_replace(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            
            # 跳过已经是本地路径的图片
            if not image_url.startswith(("http://", "https://")):
                return match.group(0)
            
            try:
                # 从 Notion URL 中提取稳定的文件 ID
                image_id = self._extract_notion_image_id(image_url)
                
                # 检查图片是否已存在（基于文件 ID）
                existing_file = self._find_existing_image(image_id)
                if existing_file:
                    relative_path = f"/images/{existing_file.name}"
                    print(f"[OK] 使用已存在的图片: {existing_file.name}")
                    return f"![{alt_text}]({relative_path})"
                
                # 使用 httpx 下载图片
                import httpx
                response = httpx.get(image_url, timeout=30, follow_redirects=True)
                response.raise_for_status()
                
                # 获取文件扩展名
                content_type = response.headers.get("content-type", "")
                if "jpeg" in content_type or "jpg" in content_type:
                    ext = ".jpg"
                elif "png" in content_type:
                    ext = ".png"
                elif "gif" in content_type:
                    ext = ".gif"
                elif "webp" in content_type:
                    ext = ".webp"
                else:
                    ext = ".jpg"  # 默认扩展名
                
                # 生成本地文件名：post_slug-image_id.ext
                filename = f"{post_slug}-{image_id}{ext}"
                local_path = self.images_dir / filename
                
                # 保存图片
                with open(local_path, "wb") as f:
                    f.write(response.content)
                
                # 返回新的 Markdown 语法
                relative_path = f"/images/{filename}"
                return f"![{alt_text}]({relative_path})"
                
            except Exception as e:
                print(f"[WARNING] 下载图片失败 {image_url}: {e}")
                return match.group(0)
        
        # 处理所有图片
        processed_content = content
        matches = list(re.finditer(image_pattern, content))
        
        # 从后往前替换，避免位置偏移问题
        for match in reversed(matches):
            replacement = download_and_replace(match)
            processed_content = processed_content.replace(match.group(0), replacement, 1)
        
        return processed_content
    
    def _extract_notion_image_id(self, image_url: str) -> str:
        """从 Notion 图片 URL 中提取稳定的文件 ID"""
        import hashlib
        
        # Notion 图片 URL 格式通常为：
        # https://prod-files-secure.s3.us-west-2.amazonaws.com/USER_ID/FILE_ID/IMAGE_ID/file_name?expires=...
        # 或者
        # https://file.notion.so/f/FILE_ID/IMAGE_ID/file_name?expires=...
        
        try:
            # 方法1：从 URL 路径中提取文件 ID
            if "file.notion.so" in image_url:
                # 格式：https://file.notion.so/f/FILE_ID/...
                parts = image_url.split("/f/")
                if len(parts) > 1:
                    file_id = parts[1].split("/")[0]
                    return file_id[:8]  # 取前8位
            
            elif "s3.amazonaws.com" in image_url:
                # 格式：https://prod-files-secure.s3.us-west-2.amazonaws.com/USER_ID/FILE_ID/...
                # 查找包含 amazonaws.com 的段，然后取后面的第2个段
                parts = image_url.split("/")
                try:
                    # 找到包含 amazonaws.com 的段
                    for i, part in enumerate(parts):
                        if "amazonaws.com" in part and i + 2 < len(parts):
                            file_id = parts[i + 2]  # USER_ID 后面的段是 FILE_ID
                            if len(file_id) >= 8:
                                return file_id[:8]
                except (ValueError, IndexError):
                    pass
                
                # 备用方法：查找可能的文件 ID 模式
                for part in parts:
                    # 查找看起来像文件 ID 的段（包含字母数字，长度合适）
                    if len(part) >= 8 and any(c.isalpha() for c in part) and any(c.isdigit() for c in part):
                        return part[:8]
            
            # 方法2：如果无法提取文件 ID，使用 URL 的稳定部分生成哈希
            # 移除查询参数（包含时间戳和签名）
            stable_url = image_url.split("?")[0]
            # 移除可能的临时路径部分
            stable_url = re.sub(r'/[^/]*expires[^/]*', '', stable_url)
            
            # 生成稳定哈希
            return hashlib.md5(stable_url.encode()).hexdigest()[:8]
            
        except Exception:
            # 如果所有方法都失败，使用完整的 URL 哈希
            return hashlib.md5(image_url.encode()).hexdigest()[:8]
    
    def _find_existing_image(self, image_id: str) -> Optional[Path]:
        """查找是否已存在相同 ID 的图片"""
        if not self.images_dir.exists():
            return None
        
        # 查找所有包含该图片 ID 的文件
        for image_file in self.images_dir.glob(f"*-{image_id}.*"):
            if image_file.is_file():
                return image_file
        
        return None
    
    def clean_old_posts(self, current_posts: List[NotionPost]):
        """清理不再存在的文章"""
        current_slugs = {post.slug for post in current_posts}
        
        # 扫描现有文件
        existing_files = list(self.config.content_dir.glob("*.md"))
        
        for filepath in existing_files:
            try:
                # 读取文件获取 slug
                with open(filepath, "r", encoding="utf-8") as f:
                    post_obj = frontmatter.load(f)
                    slug = post_obj.get("slug", "")
                
                # 如果文章不在当前列表中，删除文件
                if slug and slug not in current_slugs:
                    filepath.unlink()
                    print(f"[WARNING] 删除旧文章: {filepath.name}")
                    
            except Exception as e:
                print(f"[ERROR] 处理文件失败 {filepath}: {e}")
    
    def clean_unused_images(self, current_posts: List[NotionPost]):
        """清理无用的图片文件"""
        if not self.images_dir.exists():
            return
        
        # 获取所有当前文章中使用的图片
        used_images = set()
        for post in current_posts:
            try:
                # 读取文章内容
                post_file = self.config.content_dir / f"{post.slug}.md"
                if post_file.exists():
                    with open(post_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        # 提取图片路径
                        import re
                        image_matches = re.findall(r'!\[([^\]]*)\]\(/images/([^)]+)\)', content)
                        used_images.update(image_matches)
            except Exception as e:
                print(f"[ERROR] 读取文章 {post.slug} 失败: {e}")
        
        # 扫描所有图片文件
        all_images = set()
        for image_file in self.images_dir.glob("*.*"):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                all_images.add(image_file.name)
        
        # 删除未使用的图片
        unused_images = all_images - used_images
        for image_name in unused_images:
            try:
                (self.images_dir / image_name).unlink()
                print(f"[OK] 删除无用图片: {image_name}")
            except Exception as e:
                print(f"[ERROR] 删除图片失败 {image_name}: {e}")
        
        if unused_images:
            print(f"[OK] 清理完成，删除了 {len(unused_images)} 个无用图片")
        else:
            print("[OK] 没有无用图片需要清理")
    
    async def _generate_projects_pages(self, posts: List[NotionPost], notion_client: NotionClient):
        """生成项目相关页面"""
        # 找到项目集合页面
        projects_pages = [post for post in posts if post.is_projects_page()]
        
        for projects_page in projects_pages:
            print(f"处理项目集合页面: {projects_page.title}")
            
            # 获取页面内容
            content = notion_client.get_page_content(projects_page.id)
            
            # 如果页面有关联的数据库，从数据库获取项目
            if projects_page.database_id:
                print(f"从数据库获取项目数据...")
                project_posts = notion_client.get_database_pages(projects_page.database_id)
                
                # 生成项目数据
                projects_data = []
                for project in project_posts:
                    project_data = {
                        "title": project.title,
                        "description": project.description,
                        "status": project.project_status,
                        "technologies": project.technologies,
                        "period": project.project_period,
                        "category": project.project_category,
                        "github": project.github_url,
                        "demo": project.demo_url,
                        "cover": project.cover_url,
                        "slug": project.slug
                    }
                    projects_data.append(project_data)
                
                # 在内容中注入项目数据
                projects_yaml = f"projects:\n"
                for i, project in enumerate(projects_data):
                    projects_yaml += f"  - title: {project['title']}\n"
                    if project['description']:
                        projects_yaml += f"    description: \"{project['description']}\"\n"
                    if project['status']:
                        projects_yaml += f"    status: {project['status']}\n"
                    if project['technologies']:
                        projects_yaml += f"    technologies: [{', '.join(project['technologies'])}]\n"
                    if project['period']:
                        projects_yaml += f"    period: {project['period']}\n"
                    if project['category']:
                        projects_yaml += f"    category: {project['category']}\n"
                    if project['github']:
                        projects_yaml += f"    github: {project['github']}\n"
                    if project['demo']:
                        projects_yaml += f"    demo: {project['demo']}\n"
                    if project['cover']:
                        projects_yaml += f"    cover: {project['cover']}\n"
                    if project['slug']:
                        projects_yaml += f"    slug: {project['slug']}\n"
                    if i < len(projects_data) - 1:
                        projects_yaml += "\n"
                
                # 在页面内容前添加 YAML 前置数据
                full_content = f"---\ntitle: \"{projects_page.title}\"\ntype: \"projects\"\ndescription: \"{projects_page.description}\"\n{projects_yaml}\n---\n\n{content}"
                
            else:
                # 没有关联数据库，使用普通页面处理
                full_content = content
            
            # 生成文件
            self._generate_projects_page_file(projects_page, full_content)
    
    def _generate_projects_page_file(self, post: NotionPost, content: str):
        """生成项目集合页面文件"""
        # 处理内容中的图片
        processed_content = self._process_images(content, post.slug)

        cover_path = None
        if post.cover_url:
            try:
                cover_path = self._download_cover_image(post.cover_url, post.slug)
            except Exception as e:
                print(f"[WARNING] Failed to download cover image: {e}")
        
        # 创建 front matter（如果内容中还没有的话）
        if not content.startswith('---'):
            front_matter = {
                "title": post.title,
                "date": post.date,
                "lastmod": post.last_edited_time.split("T")[0],
                "slug": post.slug,
                "draft": not post.is_published(),
                "notion_id": post.id,
                "type": "projects",
                "description": post.excerpt,
            }

            if cover_path:
                front_matter["image"] = cover_path
            
            # 创建 post 对象
            post_obj = frontmatter.Post(processed_content, **front_matter)
        else:
            # 内容已经包含前置数据，直接使用
            post_obj = frontmatter.loads(processed_content)
        
        # 项目集合页面放在 pages 目录下
        filepath = self.config.pages_dir / f"{post.slug}.md"
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post_obj))
        
        print(f"[OK] 生成项目集合页面: {filepath.name}")
    
    def generate_index(self):
        """生成首页（可选）"""
        index_content = """---
title: "我的博客"
---

欢迎来到我的博客！这里使用 Notion 作为内容管理系统，通过 Hugo 生成静态网站。

## 最新文章

{{< recent_posts >}}
"""
        index_path = self.config.content_dir.parent / "_index.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)
    
    async def generate_projects(self, projects: List[NotionProject], notion_client: NotionClient) -> int:
        """生成 Hugo 项目页面"""
        generated_count = 0
        
        print(f"开始生成 {len(projects)} 个项目...")
        
        # 创建项目目录
        projects_dir = self.config.pages_dir / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成项目集合页
        self._generate_projects_collection_page(projects)
        
        # 生成各个项目详情页
        for i, project in enumerate(projects, 1):
            try:
                print(f"处理第 {i}/{len(projects)} 个项目: {project.title}")
                
                # 获取项目内容（如果有）
                content = notion_client.get_page_content(project.id)
                
                # 生成项目文件
                self._generate_project_file(project, content, projects_dir)
                generated_count += 1
                
            except Exception as e:
                print(f"生成项目 {project.title} 失败: {e}")
                continue
        
        # 生成项目数据文件
        self._generate_projects_data(projects)
        
        print(f"[OK] 生成了 {generated_count} 个项目页面")
        return generated_count
    
    def _generate_projects_collection_page(self, projects: List[NotionProject]):
        """生成项目集合页面"""
        frontmatter = {
            "title": "项目展示",
            "layout": "projects",
            "type": "projects",
            "menu": {
                "main": {
                    "name": "项目",
                    "weight": 20
                }
            }
        }
        
        content = f"""# 我的项目

这里展示了我开发的一些项目作品。

"""
        
        # 按分类组织项目
        categories = {}
        for project in projects:
            category = project.category or "其他"
            if category not in categories:
                categories[category] = []
            categories[category].append(project)
        
        for category, category_projects in categories.items():
            content += f"## {category}\n\n"
            for project in category_projects:
                content += f"- **[{project.title}]({project.slug}/)**: {project.description}\n"
                if project.technologies:
                    content += f"  - 技术栈: {', '.join(project.technologies)}\n"
                if project.github_url:
                    content += f"  - [GitHub]({project.github_url})\n"
                if project.demo_url:
                    content += f"  - [在线演示]({project.demo_url})\n"
                content += "\n"
        
        # 写入文件
        # Use _index.md in projects directory to act as section index
        filepath = self.config.pages_dir / "projects" / "_index.md"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n{content}")
        
        print(f"[OK] 生成项目集合页面: {filepath.name}")
    
    def _generate_project_file(self, project: NotionProject, content: str, projects_dir: Path):
        """生成单个项目文件"""
        frontmatter = {
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "type": "Project",  # Explicitly set type for filtering
            "project_type": project.project_type,
            # "technologies": project.technologies,  # Removed as per request
            "tags": project.tags,
            "slug": project.slug,
            "layout": "single-project", # Use custom layout
            "category": project.category,
            "date": project.date
        }
        
        # 添加可选字段
        if project.github_url:
            frontmatter["github"] = project.github_url
        if project.demo_url:
            frontmatter["demo"] = project.demo_url
        if project.period:
            frontmatter["period"] = project.period
        if project.cover_url:
            # 下载封面图片
            local_cover = self._download_project_cover(project.cover_url, project.slug)
            if local_cover:
                frontmatter["cover"] = local_cover
                frontmatter["image"] = local_cover  # For SEO/OpenGraph
        
        # 处理内容中的图片
        processed_content = self._process_project_images(content, project.slug)
        
        # 写入文件
        filepath = projects_dir / f"{project.slug}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n{processed_content}")
        
        print(f"[OK] 生成项目文件: {filepath.name}")
    
    def _download_project_cover(self, image_url: str, project_slug: str) -> Optional[str]:
        """下载项目封面图片"""
        if not image_url:
            return None
            
        try:
            # 生成文件名
            image_id = self._extract_notion_image_id(image_url)
            if not image_id:
                image_id = f"{project_slug}-cover"
                
            ext = "jpg"  # 默认扩展名
            filename = f"{image_id}.{ext}"
            filepath = self.images_dir / "projects" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 下载图片
            # Use sync httpx.get instead of async client
            response = httpx.get(image_url, follow_redirects=True)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return f"/images/projects/{filename}"
            else:
                print(f"下载封面图片失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"下载封面图片时出错: {e}")
            return None
    
    def _process_project_images(self, content: str, project_slug: str) -> str:
        """处理项目内容中的图片"""
        if not content:
            return ""
            
        def download_and_replace(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            if not image_url:
                return match.group(0)
            
            # 仅仅检查是否为 HTTP(S) 链接
            if not image_url.startswith(("http://", "https://")):
                return match.group(0)
            
            # 下载图片
            local_path = self._download_project_image(image_url, project_slug)
            if local_path:
                return f"![{alt_text}]({local_path})"
            else:
                return match.group(0)
        
        # 处理所有图片
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', download_and_replace, content)
        return content
    
    def _download_project_image(self, image_url: str, project_slug: str) -> Optional[str]:
        """下载项目内容中的图片"""
        try:
            image_id = self._extract_notion_image_id(image_url)
            if not image_id:
                # 使用 hashlib 生成稳定 ID
                import hashlib
                image_id = f"{project_slug}-{hashlib.md5(image_url.encode()).hexdigest()[:8]}"
                
            ext = "jpg"
            filename = f"{image_id}.{ext}"
            filepath = self.images_dir / "projects" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件已存在，直接返回
            if filepath.exists():
                return f"/images/projects/{filename}"
            
            # Use sync httpx.get instead of async client
            import httpx
            response = httpx.get(image_url, follow_redirects=True)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return f"/images/projects/{filename}"
            return None
            
        except Exception as e:
            print(f"下载项目图片时出错: {e}")
            return None
    
    def _generate_projects_data(self, projects: List[NotionProject]):
        """生成项目数据文件（JSON格式）"""
        import json
        
        # 创建数据目录
        data_dir = self.config.content_dir.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典格式
        projects_data = [project.to_dict() for project in projects]
        
        # 写入 JSON 文件
        filepath = data_dir / "projects.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(projects_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 生成项目数据文件: {filepath.name}")
    
    def clean_old_projects(self, current_projects: List[NotionProject]):
        """清理旧的项目文件"""
        projects_dir = self.config.content_dir / "projects"
        if not projects_dir.exists():
            return
        
        current_slugs = {project.slug for project in current_projects}
        
        # 删除不再存在的项目文件
        for filepath in projects_dir.glob("*.md"):
            slug = filepath.stem
            if slug not in current_slugs:
                filepath.unlink()
                print(f"删除旧项目文件: {filepath.name}")
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()
