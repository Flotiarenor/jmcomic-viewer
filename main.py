# main.py
import webview
import os
import json
from PIL import Image
import io
import base64
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import natsort

# --- 确保安装了所有依赖 ---
# pip install pywebview Pillow natsort

class ComicViewerApi:
    """
    漫画查看器的后端API，提供所有核心功能。
    这个类的实例将通过 pywindow.js_api 暴露给前端。
    """
    def __init__(self):
        """初始化状态和路径。"""
        self.comics_base_dir: Path = Path("本子")
        self.current_comic_dir: Optional[Path] = None
        self.current_image_index: int = 0
        self.image_files: List[str] = []
        self.is_ai_version = False
        self.original_comic_dir: Optional[Path] = None
        self.ai_comic_dir: Optional[Path] = None
        
        self.all_comics_data: List[Dict[str, Any]] = []
        self.filtered_comics_data: List[Dict[str, Any]] = []
        self.predefined_tags: List[str] = []

        # 初始化时加载数据
        self.load_predefined_tags()
        self.load_comics_list()

    # --- API: 漫画列表和筛选 ---
    def get_comics_list(self) -> List[Dict[str, Any]]:
        """获取筛选后的漫画列表，每个条目包含base64编码的缩略图。"""
        result_list = []
        for comic_data in self.filtered_comics_data:
            comic_path = Path(comic_data['path'])
            preview_image = self.get_preview_image(comic_path)
            thumbnail_base64 = None
            if preview_image:
                thumbnail_base64 = self.image_to_base64(preview_image, (100, 140))
            
            result_list.append({
                'id': comic_data['id'],
                'title': comic_data['title'],
                'author': comic_data['author'],
                'tags': comic_data['tags'],
                'path': str(comic_path),
                'thumbnail': thumbnail_base64
            })
        return result_list

    def apply_filters(self, search_text: str, selected_tags: List[str]):
        """根据搜索文本和标签筛选漫画。"""
        self.filtered_comics_data = []
        search_text = search_text.lower()
        current_tags = set(selected_tags)

        for comic in self.all_comics_data:
            # 搜索过滤
            if search_text and not (search_text in comic['id'].lower() or
                                   search_text in comic['title'].lower() or
                                   search_text in comic['author'].lower()):
                continue
            # 标签过滤
            if current_tags and not current_tags.issubset(set(comic['tags'])):
                continue
            
            self.filtered_comics_data.append(comic)
        
        # 返回新的列表，前端会更新
        return self.get_comics_list()

    def get_predefined_tags(self) -> List[str]:
        """获取预定义标签列表。"""
        return self.predefined_tags

    # --- API: 漫画查看器 ---
    def open_comic(self, comic_path_str: str) -> Dict[str, Any]:
        """打开一个漫画，准备查看。"""
        self.current_comic_dir = Path(comic_path_str)
        self.original_comic_dir = self.current_comic_dir
        self.ai_comic_dir = self.current_comic_dir / "ai"
        self.is_ai_version = False
        
        self.load_comic_images()
        info = self.load_comic_info(self.current_comic_dir / "album_info.json")
        
        return {
            "info": info,
            "total_pages": len(self.image_files),
            "is_ai_available": self.ai_comic_dir.exists()
        }

    def get_current_image_data(self) -> Optional[Dict[str, Any]]:
        """获取当前图片的base64编码和元信息。"""
        if not self.image_files or self.current_image_index >= len(self.image_files):
            return None
            
        current_image_path = self.image_files[self.current_image_index]
        
        # 获取章节信息
        chapter_info = ""
        relative_path = os.path.relpath(current_image_path, self.current_comic_dir)
        path_parts = Path(relative_path).parts
        if len(path_parts) > 1:
            chapter_info = f" [{path_parts[0]}]"
        
        try:
            img = Image.open(current_image_path)
            base64_data = self.image_to_base64(img)
            return {
                "image_data": base64_data,
                "page_info": f"{self.current_image_index + 1}/{len(self.image_files)}{chapter_info}",
                "filename": os.path.basename(current_image_path)
            }
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None

    def navigate_image(self, direction: str) -> Optional[Dict[str, Any]]:
        """导航到上一张或下一张图片。"""
        if direction == "prev" and self.current_image_index > 0:
            self.current_image_index -= 1
        elif direction == "next" and self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
        else:
            return None  # 已到边界
        
        return self.get_current_image_data()

    def toggle_ai_version(self) -> Dict[str, Any]:
        """切换AI修复版本。"""
        if not self.current_comic_dir or not self.ai_comic_dir.exists():
            return {"error": "AI版本不可用"}

        if self.is_ai_version:
            self.current_comic_dir = self.original_comic_dir
        else:
            self.current_comic_dir = self.ai_comic_dir
        
        self.is_ai_version = not self.is_ai_version
        
        # 重新加载图片，并尝试保持位置
        current_position_ratio = self.current_image_index / len(self.image_files) if self.image_files else 0
        self.load_comic_images()
        if self.image_files:
            new_index = int(current_position_ratio * len(self.image_files))
            self.current_image_index = min(new_index, len(self.image_files) - 1)
        
        return {
            "is_ai_version": self.is_ai_version,
            "total_pages": len(self.image_files),
            "current_image": self.get_current_image_data()
        }

    # --- 内部辅助方法 ---
    def load_comics_list(self):
        """从文件系统加载所有漫画数据。"""
        if not self.comics_base_dir.is_dir():
            print("警告: 未找到本子目录！")
            return
        
        self.all_comics_data = []
        comic_dirs = [d for d in self.comics_base_dir.iterdir() if d.is_dir()]
        
        for comic_dir in comic_dirs:
            json_path = comic_dir / "album_info.json"
            info = self.load_comic_info(json_path)
            self.all_comics_data.append({
                'path': str(comic_dir),
                'id': comic_dir.name,
                'info': info,
                'title': info.get("title", comic_dir.name),
                'author': info.get("author", "未知作者"),
                'tags': info.get("tags", [])
            })
        
        self.filtered_comics_data = self.all_comics_data.copy()

    def load_predefined_tags(self):
        """从config.json加载预定义标签。"""
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.predefined_tags = config.get("tags", [])
    
    def load_comic_info(self, json_path: Path) -> Dict[str, Any]:
        """加载单个漫画的JSON信息。"""
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_preview_image(self, comic_path: Path) -> Optional[Image.Image]:
        """获取漫画的预览图。"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png']
        chapter_dirs = [d for d in comic_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        search_paths = sorted(chapter_dirs) if chapter_dirs else [comic_path]
        
        for search_path in search_paths:
            for ext in image_extensions:
                files = list(search_path.glob(ext))
                if files:
                    try:
                        return Image.open(files[0])
                    except Exception:
                        continue
        return None

    def load_comic_images(self):
        """加载当前漫画的所有图片路径。"""
        if not self.current_comic_dir: return
        
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']
        self.image_files = []
        current_dir = Path(self.current_comic_dir)
        
        chapter_dirs = [d for d in current_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if chapter_dirs:
            for chapter_dir in natsort.natsorted(chapter_dirs):
                chapter_files = []
                for ext in image_extensions:
                    chapter_files.extend(chapter_dir.glob(ext))
                self.image_files.extend(natsort.natsorted(chapter_files))
        else:
            all_files = []
            for ext in image_extensions:
                all_files.extend(current_dir.glob(ext))
            self.image_files = natsort.natsorted(all_files)
        
        self.current_image_index = 0

    def image_to_base64(self, image: Image.Image, size: Optional[tuple] = None) -> str:
        """将PIL图片对象转换为Base64字符串。"""
        if size:
            image = image.resize(size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"


def main():
    """启动PyWebView应用。"""
    api = ComicViewerApi()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(current_dir, 'index.html')
    # 创建窗口
    window = webview.create_window(
        '本子查看器',
        url=f'file://{html_file_path}', # 加载本地HTML文件
        js_api=api,        # 暴露API给JS
        width=1440,
        height=900
    )
    
    # 启动应用
    webview.start(debug=False) # debug=True 时会打开开发者工具，方便调试

if __name__ == '__main__':
    main()
