# debug_frontend.py
import webview
import os
import json
import threading
from flask import Flask, send_file
from datetime import datetime

class MockAPI:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.cover_dir = os.path.join(self.base_path, "test", "cover")
        os.makedirs(self.cover_dir, exist_ok=True)
        
        # 漫画数据
        self.comics_data = [
            {
                "id": 1,
                "comic_id": "187420",
                "title": "[黑暗大法师个人整合] [武藤まと] こあくまは小动物 + 4Pリーフレット",
                "author": "武藤まと",
                "cover_url": "http://127.0.0.1:18080/api/cover/187420",
                "page_count": 199,
                "read_status": "reading",
                "last_read_page": 25
            },
            {
                "id": 2,
                "comic_id": "1197224",
                "title": "无表情系女友的发情开关",
                "author": "ユイザキカズヤ",
                "cover_url": "http://127.0.0.1:18080/api/cover/1197224",
                "page_count": 59,
                "read_status": "unread",
                "last_read_page": 0
            }
        ]

    # 注意：这些方法需要是实例方法，不是静态方法
    def get_comics_list(self):
        print("API调用: get_comics_list")
        return self.comics_data

    def search_comics(self, keyword):
        print(f"API调用: search_comics, 关键词: {keyword}")
        if not keyword:
            return self.comics_data
        return [c for c in self.comics_data if keyword.lower() in c['title'].lower() or keyword.lower() in c['author'].lower()]

    def get_downloads(self):
        print("API调用: get_downloads")
        return [
            {"id": 1, "title": "测试下载1", "status": "downloading", "progress": 65},
            {"id": 2, "title": "测试下载2", "status": "completed", "progress": 100}
        ]

    def get_favorites(self):
        print("API调用: get_favorites")
        return self.comics_data[:1]

    def get_cover_image(self, comic_id):
        """获取封面图片路径"""
        extensions = ['jpg', 'jpeg', 'png', 'gif']
        patterns = [
            f"{comic_id}cover",
            f"{comic_id}",
            f"{int(comic_id):05d}" if comic_id.isdigit() else comic_id
        ]
        
        for pattern in patterns:
            for ext in extensions:
                cover_path = os.path.join(self.cover_dir, f"{pattern}.{ext}")
                if os.path.exists(cover_path):
                    return cover_path
        return None

# 创建Flask应用
def create_image_server():
    app = Flask(__name__)
    
    # 创建API实例供Flask使用
    api_instance = MockAPI()
    
    @app.route('/api/cover/<comic_id>')
    def serve_cover(comic_id):
        cover_path = api_instance.get_cover_image(comic_id)
        if cover_path and os.path.exists(cover_path):
            return send_file(cover_path)
        else:
            raise FileNotFoundError(f"封面图片不存在：{comic_id}")
    return app, api_instance

def main():
    # 创建图片服务器和API实例
    image_app, api_instance = create_image_server()
    
    # 在单独线程中运行图片服务器
    server_thread = threading.Thread(
        target=lambda: image_app.run(host='127.0.0.1', port=18080, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    
    # 等待服务器启动
    import time
    time.sleep(1)
    
    print("图片服务器已启动: http://127.0.0.1:18080")
    
    # 创建主窗口 - 修复API暴露方式
    webview.create_window(
        "漫画库调试模式",
        "ui/index.html",
        width=1200,
        height=800,
        resizable=True,
        js_api=api_instance  # 直接传递API实例，而不是字典
    )
    webview.start(debug=True)

if __name__ == '__main__':
    main()
