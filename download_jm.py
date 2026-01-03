# download_jm.py
import os
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import jmcomic
from jmcomic import JmModuleConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jm_downloader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 引入插件模块
try:
    from PageCountPlugin import PageCountPlugin
    plug_available = True
except ImportError:
    plug_available = False
    logging.warning("PageCountPlugin 未找到，将使用基础统计方法")

class AlbumDownloader:
    def __init__(self, download_dir: str="./本子"):
        self.download_dir = os.path.abspath(download_dir)
        self._client = None
        self._ensure_download_dir()
        
        if plug_available:
            JmModuleConfig.register_plugin(PageCountPlugin)

    def _ensure_download_dir(self):
        """确保下载目录存在"""
        os.makedirs(self.download_dir, exist_ok=True)

    def get_client(self):
        """获取JM客户端实例（单例模式）"""
        if not self._client:
            option = self.create_option()
            self._client = option.build_jm_client()
        return self._client

    def create_option(self, base_dir=None, is_multi_chapter=False):
        """创建下载配置"""
        if base_dir is None:
            base_dir = self.download_dir

        dir_rule = "Bd / Pindextitle" if is_multi_chapter else "Bd"

        option_dict: = {
            "dir_rule": {
                "base_dir": base_dir,
                "rule": dir_rule
            },
            "download": {
                "cache": True,
                "image": {
                    "decode": True,
                    "suffix": ".jpg"
                },
                "threading": {
                    "image": 10,
                    "photo": 4
                }
            }
        }
        
        # 如果插件可用，添加插件配置
        if plug_available:
            option_dict["plugins"] = {
                "before_album": [{"plugin": "page_counter"}],
                "before_photo": [{"plugin": "page_counter"}]
            }
            
        return jmcomic.JmOption.construct(option_dict)

    def save_album_info_to_json(self, album_detail, folder_path: str, real_page_count=None):
        """保存漫画信息到JSON文件"""
        try:
            # 处理album_detail可能是元组的情况
            if isinstance(album_detail, (list, tuple)):
                album = album_detail[0]
            else:
                album = album_detail

            # 提取章节信息
            chapters = []
            if hasattr(album, 'chapter_list') and album.chapter_list:
                for chap in album:
                    chapters.append({
                        'chapter_id': getattr(chap, 'id', ''),
                        'title': getattr(chap, 'name', ''),
                        'page_count': len(chap)
                    })
            
            # 构建信息字典
            info = {
                "oname": getattr(album, 'oname', 'unknown'),
                "album_id": str(getattr(album, 'album_id', 'unknown')),
                "actors": getattr(album, 'actors', 'None'),
                "title": getattr(album, 'name', '未知主标题'),
                "author": getattr(album, 'author', '未知作者'),
                "tags": list(getattr(album, 'tags', [])),
                "chapter_count": len(album),
                "total_page_count": real_page_count or getattr(album, 'page_count', 0),
                "chapters": chapters,
                "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 保存到JSON文件
            json_path = os.path.join(folder_path, "album_info.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2, default=str)
            
            logging.info(f"漫画信息已保存到: {json_path}")
            return True
            
        except Exception as e:
            logging.error(f"保存JSON信息失败: {e}", exc_info=True)
            return False

    def download_album(self, album_id, download_dir=None):
        """下载漫画"""
        if download_dir is None:
            download_dir = os.path.join(self.download_dir, album_id)
        
        os.makedirs(download_dir, exist_ok=True)

        try:
            client = self.get_client()
            album_detail = client.get_album_detail(album_id)

            chapter_count = len(album_detail)
            is_multi_chapter = chapter_count > 1

            logging.info(f"准备下载漫画: [{album_detail.name}] (ID: {album_id})")
            logging.info(f"  - 总章节数: {chapter_count}")
            logging.info(f"  - 初始总图片数: {album_detail.page_count}")

            option = self.create_option(download_dir, is_multi_chapter=is_multi_chapter)

            logging.info("开始下载...")
            album = jmcomic.download_album(album_id, option)

            # 获取真实页数
            if plug_available:
                real_page_count = PageCountPlugin.get_total_pages(album_id)
                PageCountPlugin.reset(album_id)
            else:
                # 如果没有插件，手动计算
                real_page_count = sum(len(client.get_photo_detail(ch.photo_id)) for ch in album_detail)
            
            logging.info(f"下载完成！真实总图片数: {real_page_count}，保存在: {download_dir}")

            self.save_album_info_to_json(album, download_dir, real_page_count)
            return True
            
        except Exception as e:
            logging.error(f"下载失败: {str(e)}", exc_info=True)
            return False

    def update_album_info_only(self, album_id):
        """仅更新漫画信息（不下载）"""
        try:
            client = self.get_client()
            album_detail = client.get_album_detail(album_id)
            
            # 手动统计图片数量
            total_pages = 0
            for chapter in album_detail:
                photo_detail = client.get_photo_detail(chapter.photo_id)
                total_pages += len(photo_detail)
            
            folder_path = os.path.join(self.download_dir, album_id)
            os.makedirs(folder_path, exist_ok=True)
            
            self.save_album_info_to_json(album_detail, folder_path, total_pages)
            logging.info(f"漫画信息更新完成！真实总图片数: {total_pages}")
            return True
            
        except Exception as e:
            logging.error(f"获取漫画信息失败: {e}", exc_info=True)
            return False

    def get_album_id_from_user(self):
        """从用户输入获取漫画ID"""
        album_id = input("请输入漫画ID: ").strip()
        if not album_id:
            logging.warning("漫画ID不能为空！")
            return None
        if not album_id.isdigit():
            logging.warning("漫画ID必须为数字！")
            return None
        return album_id

    def update_all_local_album_info(self, max_workers=5):
        """更新所有本地漫画的信息"""
        if not os.path.exists(self.download_dir):
            logging.warning("下载目录不存在")
            return

        folders = [f for f in os.listdir(self.download_dir) if f.isdigit()]
        if not folders:
            logging.info("未找到任何漫画目录")
            return
            
        logging.info(f"找到 {len(folders)} 个漫画目录，开始更新信息...")

        def process_album(album_id):
            try:
                client = self.get_client()
                album_detail = client.get_album_detail(album_id)
                
                total_pages = 0
                for chapter in album_detail:
                    photo_detail = client.get_photo_detail(chapter.photo_id)
                    total_pages += len(photo_detail)
                
                folder_path = os.path.join(self.download_dir, album_id)
                self.save_album_info_to_json(album_detail, folder_path, total_pages)
                return album_id, True, total_pages
            except Exception as e:
                logging.error(f"更新漫画 {album_id} 失败", exc_info=True)
                return album_id, False, 0

        # 使用线程池并发处理
        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_album, aid) for aid in folders]
            
            for i, future in enumerate(as_completed(futures), 1):
                aid, success, pages = future.result()
                if success:
                    success_count += 1
                    logging.info(f"[{i}/{len(folders)}] 更新成功: {aid} ({pages} 页)")
                else:
                    logging.error(f"[{i}/{len(folders)}] 更新失败: {aid}")

        logging.info(f"更新完成！成功: {success_count}/{len(folders)}")

    def show_menu(self):
        """显示菜单"""
        print("\n" + "="*50)
        print("JMComic 漫画信息管理器")
        print("="*50)
        print("1. 下载漫画并保存信息")
        print("2. 获取/更新漫画元信息（不下载图片）")
        print("3. 更新所有本地漫画的信息")
        print("0. 退出程序")
        print("="*50)


    def run(self):
        while True:
            self.show_menu()
            choice = input("请选择操作 (0-3): ").strip() # <--- 提示也改一下

            if choice == "0":
                # ...
                break
            elif choice == "1":
                album_id = self.get_album_id_from_user()
                if album_id:
                    self.download_album(album_id)
            elif choice == "2": # <--- 合并处理逻辑
                album_id = self.get_album_id_from_user()
                if album_id:
                    self.update_album_info_only(album_id)
            elif choice == "3":
                confirm = input("确定要更新所有本地漫画的信息吗？(y/N): ").strip().lower()
                if confirm == 'y':
                    self.update_all_local_album_info()
                else:
                    logging.info("操作已取消")
            else:
                logging.warning("无效选择，请重新输入！")



def main():
    """主函数"""
    downloader = AlbumDownloader()
    downloader.run()


if __name__ == "__main__":
    main()
