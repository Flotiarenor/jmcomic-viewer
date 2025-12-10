import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from PIL import Image, ImageTk
import glob
from typing import Dict, List, Set, Optional, Any
from pathlib import Path

class ComicViewer:
    """
    一个用于浏览和查看本地漫画集合的GUI应用程序。

    该应用程序提供两个主要界面：
    1.  选择界面：显示漫画列表，支持搜索和标签筛选。
    2.  查看器界面：浏览单个漫画的页面，支持缩放、拖动和信息查看。
    """
    def __init__(self, root: tk.Tk):
        """初始化漫画查看器的主窗口和所有必要的状态变量。"""
        self.root = root
        self.root.title("本子查看器")
        self.root.geometry("1440x1280")
        
        # --- 核心路径和数据 ---
        self.comics_base_dir: Path = Path("本子")
        self.current_comic_dir: Optional[Path] = None
        
        # --- 查看器相关状态 ---
        self.current_image_index: int = 0
        self.image_files: List[str] = [] # 保留为str列表，因为PIL可以接受
        self.current_image: Optional[Image.Image] = None
        self.photo: Optional[ImageTk.PhotoImage] = None

        # --- AI修复版本相关状态 ---
        self.is_ai_version = False
        self.original_comic_dir = None
        self.ai_comic_dir = None
        
        # --- 缩放和拖动相关状态 ---
        self.scale_factor: float = 1.0
        self.drag_start_x: int = 0
        self.drag_start_y: int = 0
        self.image_offset_x: int = 0
        self.image_offset_y: int = 0
        self.original_offset_x: int = 0
        self.original_offset_y: int = 0
        
        # --- 搜索和筛选相关状态 ---
        self.all_comics_data: List[Dict[str, Any]] = []  # 存储所有本子数据
        self.filtered_comics_data: List[Dict[str, Any]] = []  # 存储筛选后的本子数据
        self.current_tags: Set[str] = set()  # 当前选择的标签
        
        # --- UI 事件绑定 ---
        self.root.after(1, self._setup_ui_and_load) # 延迟调用以避免初始化问题

    def _setup_ui_and_load(self) -> None:
        """按顺序构建UI、加载标签和漫画列表。"""
        self._setup_ui()
        self.load_comics_list()

    def _setup_ui(self) -> None:
        """构建并初始化整个用户界面，使用 grid 布局。"""
        # 主容器，使用 grid 以获得更好的控制
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 分别构建两个主要界面
        self._setup_selection_ui()
        self._setup_viewer_ui()

        # 初始时只显示选择界面
        self.selection_frame.grid(row=0, column=0, sticky="nsew")
        self.viewer_frame.grid_forget()  # 隐藏查看器界面

        # 绑定所有事件
        self._bind_events()

    def _setup_selection_ui(self) -> None:
        """构建漫画选择界面的所有组件。"""
        self.selection_frame = ttk.Frame(self.main_frame)
        
        # --- 1. 搜索和筛选区域 ---
        self.search_frame = ttk.LabelFrame(self.selection_frame, text="搜索和筛选", padding=(10, 5))
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=(0, 0), pady=(0, 10))
        self.search_frame.grid_columnconfigure(1, weight=1)

        # 搜索框行
        ttk.Label(self.search_frame, text="搜索:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # [逻辑修正] 列表缩放标签移至此处，功能更明确
        scale_frame = ttk.Frame(self.search_frame)
        scale_frame.grid(row=0, column=2, padx=10)
        ttk.Label(scale_frame, text="封面缩放:").pack(side=tk.LEFT)
        self.list_zoom_label = ttk.Label(scale_frame, text="100%")
        self.list_zoom_label.pack(side=tk.LEFT, padx=5)
        
        self.clear_filter_button = ttk.Button(self.search_frame, text="清除筛选", command=self.clear_filters)
        self.clear_filter_button.grid(row=0, column=3, padx=(10, 0))

        # --- 2. 标签筛选区域 ---
        tags_frame = ttk.Frame(self.search_frame)
        tags_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(5, 0))
        ttk.Label(tags_frame, text="标签:").pack(side=tk.LEFT, padx=(0, 5))
        self.tags_container = ttk.Frame(tags_frame) # 重命名 tags_frame 为 tags_container
        self.tags_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- 3. 漫画列表区域 ---
        self.comics_list_frame = ttk.LabelFrame(self.selection_frame, text="本子列表", padding=(10, 5))
        self.comics_list_frame.grid(row=1, column=0, sticky="nsew")
        self.selection_frame.grid_rowconfigure(1, weight=1)
        
        self.comics_canvas = tk.Canvas(self.comics_list_frame)
        self.comics_scrollbar = ttk.Scrollbar(self.comics_list_frame, orient="vertical", command=self.comics_canvas.yview)
        self.comics_scrollable_frame = ttk.Frame(self.comics_canvas)
        
        self.comics_scrollable_frame.bind("<Configure>", lambda e: self.comics_canvas.configure(scrollregion=self.comics_canvas.bbox("all")))
        self.comics_canvas.create_window((0, 0), window=self.comics_scrollable_frame, anchor="nw")
        self.comics_canvas.configure(yscrollcommand=self.comics_scrollbar.set)
        
        self.comics_canvas.pack(side="left", fill="both", expand=True)
        self.comics_scrollbar.pack(side="right", fill="y")

    def _setup_viewer_ui(self) -> None:
        """构建漫画查看器界面的所有组件。"""
        self.viewer_frame = ttk.Frame(self.main_frame)
        self.viewer_frame.grid_rowconfigure(1, weight=1)
        self.viewer_frame.grid_columnconfigure(0, weight=1)

        # --- 1. 顶部工具栏 ---
        self.button_frame = ttk.Frame(self.viewer_frame)
        self.button_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 0), pady=(0, 10))
        
        self.back_button = ttk.Button(self.button_frame, text="返回列表", command=self.show_selection)
        self.back_button.pack(side=tk.LEFT, padx=5)
        self.previous_button = ttk.Button(self.button_frame, text="上一页", command=self.show_previous_image)
        self.previous_button.pack(side=tk.LEFT, padx=5)
        self.next_button = ttk.Button(self.button_frame, text="下一页", command=self.show_next_image)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        zoom_group = ttk.Frame(self.button_frame)
        zoom_group.pack(side=tk.LEFT, padx=20)
        self.zoom_in_button = ttk.Button(zoom_group, text="放大(+)", command=lambda: self.zoom_image(1.2))
        self.zoom_in_button.pack(side=tk.LEFT, padx=5)
        self.zoom_out_button = ttk.Button(zoom_group, text="缩小(-)", command=lambda: self.zoom_image(0.8))
        self.zoom_out_button.pack(side=tk.LEFT, padx=5)
        self.reset_zoom_button = ttk.Button(zoom_group, text="重置缩放", command=self.reset_zoom)
        self.reset_zoom_button.pack(side=tk.LEFT, padx=5)
        self.toggle_ai_button = ttk.Button(self.button_frame, text="切换修复版本", command=self.toggle_ai_version)
        self.toggle_ai_button.pack(side=tk.LEFT, padx=5)

        self.page_info = ttk.Label(self.button_frame, text="")
        self.page_info.pack(side=tk.RIGHT, padx=10)
        
        # --- 2. 主查看区域 (图片 + 信息) ---
        self.viewer_main_frame = ttk.Frame(self.viewer_frame)
        self.viewer_main_frame.grid(row=1, column=0, sticky="nsew")
        self.viewer_main_frame.grid_columnconfigure(0, weight=3) # 图片区权重高
        self.viewer_main_frame.grid_columnconfigure(1, weight=0) # 信息区权重固定
        self.viewer_main_frame.grid_rowconfigure(0, weight=1)

        # 图片显示区域
        self.image_frame = ttk.Frame(self.viewer_main_frame)
        self.image_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        self.image_canvas = tk.Canvas(self.image_frame, bg="gray15")
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 信息显示区域
        self.info_frame = ttk.LabelFrame(self.viewer_main_frame, text="本子信息")
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        self.info_frame.grid_propagate(False)
        self.info_frame.config(width=300)

        self.info_text = tk.Text(self.info_frame, wrap=tk.WORD, state=tk.DISABLED, width=35)
        self.info_scrollbar = ttk.Scrollbar(self.info_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=self.info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_events(self) -> None:
        """绑定所有事件处理器。"""
        self.image_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.image_canvas.bind("<Button-1>", self.on_mouse_click)
        self.image_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        self.root.bind("<Key>", self.on_key_press)
        self.root.bind("<plus>", lambda e: self.zoom_image(1.2))
        self.root.bind("<minus>", lambda e: self.zoom_image(0.8))
        self.root.bind("<0>", lambda e: self.reset_zoom())
        
        # Linux 滚轮兼容
        self.root.bind("<Button-4>", lambda e: self.zoom_image(1.1))
        self.root.bind("<Button-5>", lambda e: self.zoom_image(0.9))
        
        self.root.focus_set()
        self.root.bind("<Configure>", self.on_window_resize)

    def load_comics_list(self):
        """加载本子列表"""
        # 使用 pathlib 进行路径检查
        if not self.comics_base_dir.is_dir():
            messagebox.showwarning("警告", "未找到本子目录！")
            return
            
        # 清除现有内容
        for widget in self.comics_scrollable_frame.winfo_children():
            widget.destroy()
            
        # 获取所有本子目录并加载数据
        self.all_comics_data = []
        comic_dirs = [d for d in self.comics_base_dir.iterdir() if d.is_dir()]
        
        for comic_dir in comic_dirs:
            # 使用 pathlib 构建 json_path
            json_path = comic_dir / "album_info.json"
            info = self.load_comic_info(json_path)
            
            comic_data = {
                'path': str(comic_dir), # 保持为字符串以兼容旧代码
                'id': comic_dir.name,
                'info': info,
                'title': info.get("title", comic_dir.name),
                'author': info.get("author", "未知作者"),
                'tags': info.get("tags", [])
            }
            self.all_comics_data.append(comic_data)
            
        self.filtered_comics_data = self.all_comics_data.copy()
        
        self.load_predefined_tags()
        self.update_tags_filter()
        self.display_comics_list()
    
    def load_predefined_tags(self):
        """从config.json加载预定义标签"""
        self.predefined_tags = []
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.predefined_tags = config.get("tags", [])
    
    def update_tags_filter(self):
        """更新标签筛选按钮（使用预定义标签）"""
        # 清除现有的标签按钮
        for widget in self.tags_container.winfo_children():
            widget.destroy()
        
        tags_to_show = self.predefined_tags
        for tag in tags_to_show:
            # 使用 StringVar 以便更好的状态管理
            tag_var = tk.StringVar(value="off")
            button = ttk.Checkbutton(
                self.tags_container, 
                text=tag, 
                variable=tag_var,
                onvalue="on", 
                offvalue="off",
                command=lambda t=tag, v=tag_var: self.on_tag_toggle(t, v)
            )
            button.pack(side=tk.LEFT, padx=2, pady=2)

    def on_tag_toggle(self, tag: str, var: tk.StringVar):
        """标签切换时的处理"""
        if var.get() == "on":
            self.current_tags.add(tag)
        else:
            self.current_tags.discard(tag)
        self.apply_filters()
        
    def on_search_change(self, *args):
        """搜索内容变化时的处理"""
        self.apply_filters()
        
    def apply_filters(self):
        """应用搜索和标签筛选"""
        search_text = self.search_var.get().lower()
        self.filtered_comics_data = []
        
        for comic in self.all_comics_data:
            # 搜索过滤
            if search_text and not (search_text in comic['id'].lower() or
                                   search_text in comic['title'].lower() or
                                   search_text in comic['author'].lower()):
                continue
                    
            # 标签过滤
            if self.current_tags and not self.current_tags.issubset(set(comic['tags'])):
                continue
                    
            self.filtered_comics_data.append(comic)
            
        self.display_comics_list()
        
    def clear_filters(self):
        """清除所有筛选条件"""
        self.search_var.set("")
        self.current_tags.clear()
        for widget in self.tags_container.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                var = widget.cget('variable')
                if var:
                    var.set("off")
        self.filtered_comics_data = self.all_comics_data.copy()
        self.display_comics_list()
        
    def display_comics_list(self):
        """显示本子列表"""
        for widget in self.comics_scrollable_frame.winfo_children():
            widget.destroy()
        for comic_data in self.filtered_comics_data:
            self.create_comic_item(comic_data)
            
    def create_comic_item(self, comic_data):
        """创建本子项目显示"""
        comic_path = Path(comic_data['path'])
        info = comic_data['info']
        item_frame = ttk.Frame(self.comics_scrollable_frame, relief="raised", borderwidth=1)
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        preview_image = self.get_preview_image(comic_path)
        if preview_image:
            # 注意：此处的 list_zoom_label 是用于封面缩放的，需要单独实现
            # 此处保留原始逻辑，您可以后续添加封面缩放
            preview_photo = ImageTk.PhotoImage(preview_image.resize((100, 140), Image.Resampling.LANCZOS))
            preview_label = ttk.Label(item_frame, image=preview_photo)
            preview_label.image = preview_photo  # 保持引用
            preview_label.pack(side=tk.LEFT, padx=5)
        else:
            placeholder = ttk.Label(item_frame, text="无预览", width=15)
            placeholder.pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.Frame(item_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        title_label = ttk.Label(info_frame, text=comic_data['title'], font=("Arial", 12, "bold"))
        title_label.pack(anchor="w")
        author_label = ttk.Label(info_frame, text=f"作者: {comic_data['author']}")
        author_label.pack(anchor="w")
        
        tags = comic_data['tags']
        if tags:
            tags_text = " ".join(tags[:5])
            tags_label = ttk.Label(info_frame, text=f"标签: {tags_text}")
            tags_label.pack(anchor="w")
        
        try:
             total_pages = len(list(comic_path.glob('*.*'))) - 1 # 减去json
        except:
             total_pages = 0
        pages_label = ttk.Label(info_frame, text=f"页数: {total_pages}")
        pages_label.pack(anchor="w")
        
        def on_click(event=None):
            self.open_comic(str(comic_path))
            
        item_frame.bind("<Button-1>", on_click)
        for child in item_frame.winfo_children():
            child.bind("<Button-1>", on_click)
            
    def load_comic_info(self, json_path: Path):
        """加载本子信息"""
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
        
    def get_preview_image(self, comic_path: Path) -> Optional[Image.Image]:
        """获取预览图片（从第一章或根目录）"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png']
        
        # 先尝试从章节目录获取
        chapter_dirs = [d for d in comic_path.iterdir() 
                        if d.is_dir() and not d.name.startswith('.')]
        
        search_paths = []
        if chapter_dirs:
            # 从第一章目录获取
            search_paths.append(sorted(chapter_dirs, key=lambda x: x.name)[0])
        # 也从根目录获取（兼容单章节）
        search_paths.append(comic_path)
        
        for search_path in search_paths:
            for ext in image_extensions:
                files = list(search_path.glob(ext))
                if files:
                    try:
                        return Image.open(files[0])
                    except Exception:
                        continue
        return None
        
    def open_comic(self, comic_path_str: str):
        """打开本子"""
        self.current_comic_dir = Path(comic_path_str)
        self.original_comic_dir = Path(comic_path_str)  # 保存原始路径
        self.ai_comic_dir = Path(comic_path_str) / "ai"  # AI版本路径
        self.is_ai_version = False  # 重置为原始版本
        self.toggle_ai_button.config(text="切换修复版本")  # 重置按钮文本
        
        self.load_comic_images()
        self.load_comic_info_display()
        self.show_viewer()
        self.show_current_image()
        
    def load_comic_images(self):
        """加载本子图片（兼容多章节）"""
        if not self.current_comic_dir: 
            return
        
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']
        self.image_files = []
        current_dir_str = str(self.current_comic_dir)
        
        # 检查是否有多章节目录
        chapter_dirs = [d for d in Path(current_dir_str).iterdir() 
                        if d.is_dir() and not d.name.startswith('.')]
        
        if chapter_dirs:
            # 多章节模式：按章节顺序收集图片
            for chapter_dir in sorted(chapter_dirs, key=lambda x: x.name):
                for ext in image_extensions:
                    files = glob.glob(os.path.join(str(chapter_dir), ext))
                    files.extend(glob.glob(os.path.join(str(chapter_dir), ext.upper())))
                    self.image_files.extend(sorted(files))
        else:
            # 单章节模式：直接在根目录找图片
            for ext in image_extensions:
                files = glob.glob(os.path.join(current_dir_str, ext))
                files.extend(glob.glob(os.path.join(current_dir_str, ext.upper())))
                self.image_files.extend(sorted(files))
        
        self.image_files = list(set(self.image_files))  # 去重
        self.image_files.sort()  # 确保排序
        self.current_image_index = 0
        self.reset_view()

    def toggle_ai_version(self):
        """切换到AI处理版本或原始版本（保持章节结构）"""
        if not self.current_comic_dir:
            return
        
        if self.original_comic_dir is None:
            self.original_comic_dir = self.current_comic_dir
            self.ai_comic_dir = self.current_comic_dir / "ai"
        
        if self.is_ai_version:
            # 切换回原始版本
            self.current_comic_dir = self.original_comic_dir
            self.toggle_ai_button.config(text="切换修复版本")
        else:
            # 切换到AI版本
            if not self.ai_comic_dir.exists():
                messagebox.showwarning("警告", "AI处理版本文件夹不存在")
                return
            self.current_comic_dir = self.ai_comic_dir
            self.toggle_ai_button.config(text="切换原始版本")
        
        self.is_ai_version = not self.is_ai_version
        
        # 重新加载图片（保持当前浏览位置）
        current_position_ratio = self.current_image_index / len(self.image_files) if self.image_files else 0
        self.load_comic_images()
        
        # 尽量保持相同的浏览位置
        if self.image_files:
            new_index = int(current_position_ratio * len(self.image_files))
            self.current_image_index = min(new_index, len(self.image_files) - 1)
        
        self.show_current_image()

    def load_comic_info_display(self):
        """加载本子信息显示"""
        if not self.current_comic_dir: return
        
        json_path = self.current_comic_dir / "album_info.json"
        info = self.load_comic_info(json_path)
        
        total_pages = len(self.image_files) if hasattr(self, 'image_files') else 0
        
        info_lines = [
            f"标题: {info.get('title', '未知')}",
            f"作者: {info.get('author', '未知作者')}",
            f"ID: {info.get('album_id', '未知')}",
            f"页数: {total_pages} 页",
            f"下载时间: {info.get('download_time', '未知')}",
        ]
        
        tags = info.get('tags', [])
        if tags:
            info_lines.append(f"标签: {' '.join(tags)}")
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "\n".join(info_lines))
        self.info_text.config(state=tk.DISABLED)
      
    def show_viewer(self):
        """显示查看器界面"""
        self.selection_frame.grid_forget()
        self.viewer_frame.grid(row=0, column=0, sticky="nsew")
        self.root.focus_set()
        
    def show_selection(self):
        """显示选择界面"""
        self.viewer_frame.grid_forget()
        self.selection_frame.grid(row=0, column=0, sticky="nsew")
    
    def show_previous_image(self):
        """上一张图片"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.reset_view()
            self.show_current_image()
            
    def show_next_image(self):
        """下一张图片"""
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.reset_view()
            self.show_current_image()
        else:
            pass

    def show_current_image(self):
        """显示当前图片（包含章节信息）"""
        if not self.image_files or self.current_image_index >= len(self.image_files):
            return
            
        current_image_path = self.image_files[self.current_image_index]
        img_name = os.path.basename(current_image_path)
        
        # 获取当前图片所属章节
        chapter_info = ""
        relative_path = os.path.relpath(current_image_path, self.current_comic_dir)
        path_parts = Path(relative_path).parts
        if len(path_parts) > 1:
            chapter_info = f" [{path_parts[0]}]"
        
        self.page_info.config(text=f"{self.current_image_index+1}/{len(self.image_files)}{chapter_info} ({img_name})")
        
        try:
            image_path = Path(current_image_path)
            self.current_image = Image.open(image_path)
            self.display_image()
        except Exception as e:
            print(f"加载图片失败: {e}")
        
    def display_image(self):
        """在Canvas上显示当前图片"""
        if not self.current_image:
            return
            
        self.image_canvas.delete("all")
        
        img_width, img_height = self.current_image.size
        
        # 获取画布尺寸
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()

        # 确保画布已初始化尺寸
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.display_image)
            return
        
        # 首次加载且图片较大时自动缩放
        if (self.scale_factor == 1.0 and 
            (img_width > canvas_width or img_height > canvas_height)):
            # 计算自动缩放比例，保持图片完整显示
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            self.scale_factor = min(scale_x, scale_y)
            # 确保不会放大图片
            self.scale_factor = min(self.scale_factor, 1.0)
        
        scaled_width = int(img_width * self.scale_factor)
        scaled_height = int(img_height * self.scale_factor)
        
        # 使用 Image.Resampling.LANCZOS (Pillow 9+)
        self.photo = ImageTk.PhotoImage(self.current_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS))

        x = (canvas_width // 2) + self.image_offset_x
        y = (canvas_height // 2) + self.image_offset_y
        
        self.image_canvas.create_image(x, y, image=self.photo, anchor="center")

        
        # 更新查看器和列表页的缩放标签
        zoom_text = f"{int(self.scale_factor * 100)}%"
        # self.page_info.config(text=f"{self.current_image_index+1}/{len(self.image_files)} ({img_name}) | 缩放: {zoom_text}") # 可选方案
        
    def zoom_image(self, factor):
        """缩放图片，以鼠标为中心"""
        new_scale = self.scale_factor * factor
        new_scale = max(0.05, min(new_scale, 5.0))
        
        mouse_x = self.image_canvas.winfo_pointerx() - self.image_canvas.winfo_rootx()
        mouse_y = self.image_canvas.winfo_pointery() - self.image_canvas.winfo_rooty()
        
        center_x = self.image_canvas.winfo_width() // 2
        center_y = self.image_canvas.winfo_height() // 2
        
        rel_x = mouse_x - center_x - self.image_offset_x
        rel_y = mouse_y - center_y - self.image_offset_y
        
        new_rel_x = rel_x * (new_scale / self.scale_factor)
        new_rel_y = rel_y * (new_scale / self.scale_factor)
        
        self.image_offset_x += rel_x - new_rel_x
        self.image_offset_y += rel_y - new_rel_y
        
        self.scale_factor = new_scale
        self.display_image()
    
    def reset_zoom(self):
        """重置缩放和位置"""
        self.scale_factor = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.display_image()
    
    def reset_view(self):
        """重置视图"""
        self.scale_factor = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.original_offset_x = 0
        self.original_offset_y = 0
        
    def on_mouse_wheel(self, event):
        """鼠标滚轮缩放 (Windows/macOS)"""
        if event.delta > 0:
            self.zoom_image(1.1)
        else:
            self.zoom_image(0.9)
            
    def on_mouse_click(self, event):
        """鼠标点击开始拖动"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.original_offset_x = self.image_offset_x
        self.original_offset_y = self.image_offset_y
        
    def on_mouse_drag(self, event):
        """鼠标拖动"""
        if self.drag_start_x is not None:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            self.image_offset_x = self.original_offset_x + dx
            self.image_offset_y = self.original_offset_y + dy
            self.display_image()
                
    def on_mouse_release(self, event):
        """鼠标释放"""
        self.drag_start_x = None
        self.drag_start_y = None
        
    def on_key_press(self, event):
        """键盘按键处理"""
        key = event.keysym.lower()
        if key in ("up", "w", "a", "left"):
            self.show_previous_image()
        elif key in ("down", "s", "space", "d", "right"):
            self.show_next_image()
        elif key in ("escape", "b"):
            self.show_selection()
            
    def on_window_resize(self, event):
        """窗口大小变化"""
        # 只当是主窗口在调整大小时才重绘
        if event.widget == self.root and hasattr(self, 'viewer_frame') and self.viewer_frame.winfo_viewable():
            if hasattr(self, '_resize_timer'):
                self.root.after_cancel(self._resize_timer)
                
            self._resize_timer = self.root.after(100, self.display_image)

def main():
    try:
        root = tk.Tk()
        app = ComicViewer(root)
        root.mainloop()
    except Exception as e:
        import traceback
        messagebox.showerror("错误", f"程序出错: {str(e)}\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()

