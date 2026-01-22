"""
主同步模块
整合 Notion 客户端和 Hugo 生成器
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table

from .config import SyncConfig, get_config
from .notion_client import NotionClient, NotionPost, NotionProject
from .hugo_generator import HugoGenerator

import shutil

class BlogSyncer:
    """博客同步器主类"""
    
    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config or get_config()
        self.console = Console()
        
        # 初始化客户端
        self.notion_client = NotionClient(self.config.notion)
        self.hugo_generator = HugoGenerator(self.config.hugo)
    
    def _clean_gen_dirs(self):
        """清理生成目录"""
        # 清理 posts 目录
        posts_dir = self.config.hugo.content_dir
        if posts_dir.exists():
            print(f"清理旧目录: {posts_dir}")
            shutil.rmtree(posts_dir)
        posts_dir.mkdir(parents=True, exist_ok=True)
            
        # 清理 content/data 目录 (注意不是根目录的 data)
        data_dir = self.config.hugo.content_dir.parent / "data"
        if data_dir.exists():
            print(f"清理旧目录: {data_dir}")
            shutil.rmtree(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        project_dir = self.config.hugo.content_dir.parent / "projects"
        if project_dir.exists():
            print(f"清理旧目录: {project_dir}")
            shutil.rmtree(project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)

    async def sync(self, force: bool = False) -> bool:
        """执行同步操作"""
        try:
            print("开始同步 Notion 到 Hugo...")
            
            # 清理目录
            self._clean_gen_dirs()
            
            # 从 Notion 获取所有文章
            all_pages = self.notion_client.get_posts()
            # 过滤掉项目页面，只保留文章和普通页面
            # Debug: Print filtered items
            filtered_projects = [p for p in all_pages if p.is_project() or p.is_projects_page()]
            if filtered_projects:
                print(f"过滤掉 {len(filtered_projects)} 个项目页面: {[p.title for p in filtered_projects]}")
            
            posts = [p for p in all_pages if not p.is_project() and not p.is_projects_page()]
            
            if not posts:
                print("[OK] 没有找到文章")
            
            # 从 Notion 获取所有项目
            projects = self.notion_client.get_projects()
            
            if not projects:
                print("[OK] 没有找到项目")
            
            # 显示同步概览
            if posts:
                self._show_sync_summary(posts)
            if projects:
                self._show_projects_summary(projects)
            
            # 处理文章
            if posts:
                # 清理旧文章
                self.hugo_generator.clean_old_posts(posts)
                
                # 生成 Hugo 文章
                posts_generated = await self.hugo_generator.generate_posts(posts, self.notion_client)
                print(f"[OK] 生成了 {posts_generated} 篇文章")
            
            # 处理项目
            if projects:
                try:
                    # 清理旧项目
                    self.hugo_generator.clean_old_projects(projects)
                    
                    # 生成项目页面
                    projects_generated = await self.hugo_generator.generate_projects(projects, self.notion_client)
                    print(f"[OK] 生成了 {projects_generated} 个项目页面")
                except Exception as e:
                    print(f"[ERROR] 处理项目时出错: {e}")
                    import traceback
                    traceback.print_exc()
            
            print("[OK] 同步完成！")
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ERROR] 同步失败: {e}")
            return False
    
    def _show_sync_summary(self, posts):
        """显示同步概览"""
        published_count = sum(1 for post in posts if post.is_published())
        draft_count = len(posts) - published_count
        
        print(f"同步概览:")
        print(f"  发布文章: {published_count} 篇")
        print(f"  草稿文章: {draft_count} 篇")
        print(f"  总计: {len(posts)} 篇")
        
        # 显示文章列表
        if len(posts) <= 10:
            posts_table = Table(title="文章列表")
            posts_table.add_column("标题", style="cyan")
            posts_table.add_column("状态", style="green")
            posts_table.add_column("标签", style="yellow")
            
            for post in posts:
                status = "发布" if post.is_published() else "草稿"
                tags = ", ".join(post.tags) if post.tags else "无"
                posts_table.add_row(post.title, status, tags)
            
            self.console.print(posts_table)
    
    def _show_projects_summary(self, projects):
        """显示项目同步概览"""
        active_count = sum(1 for project in projects if project.is_active())
        inactive_count = len(projects) - active_count
        
        print(f"项目同步概览:")
        print(f"  活跃项目: {active_count} 个")
        print(f"  非活跃项目: {inactive_count} 个")
        print(f"  总计: {len(projects)} 个")
        
        # 显示项目列表
        if len(projects) <= 10:
            projects_table = Table(title="项目列表")
            projects_table.add_column("标题", style="cyan")
            projects_table.add_column("状态", style="green")
            projects_table.add_column("分类", style="yellow")
            projects_table.add_column("技术栈", style="blue")
            
            for project in projects:
                status = "活跃" if project.is_active() else "非活跃"
                category = project.category or "未分类"
                technologies = ", ".join(project.technologies[:3])  # 只显示前3个
                if len(project.technologies) > 3:
                    technologies += f" (+{len(project.technologies) - 3})"
                
                projects_table.add_row(project.title, status, category, technologies)
            
            self.console.print(projects_table)


def cli():
    """Notion-Hugo 同步工具"""
    
    @click.group()
    def main():
        """Notion-Hugo 同步工具"""
        pass
    
    @main.command()
    @click.option("--clean", is_flag=True, help="清理无用的图片文件")
    def sync(clean):
        """同步 Notion 内容到 Hugo"""
        syncer = BlogSyncer()
        
        async def run_sync():
            success = await syncer.sync()
            
            # 如果指定了清理选项，清理无用图片
            if success and clean:
                print("\n开始清理无用图片...")
                # 需要重新获取文章列表来进行清理
                posts = syncer.notion_client.get_posts()
                syncer.hugo_generator.clean_unused_images(posts)
            
            sys.exit(0 if success else 1)
        
        asyncio.run(run_sync())

    main()
