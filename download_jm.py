import jmcomic
import os
import json
from datetime import datetime

class AlbumDownloader:
    def __init__(self, download_dir="./本子"):
        self.download_dir = download_dir
        self.album_id = None
        
    def create_option(self, base_dir=None):
        """创建下载配置"""
        if base_dir is None:
            base_dir = self.download_dir
            
        option_dict = {
            "dir_rule": {
                "base_dir": base_dir,
                "rule": "Bd"  # 所有文件都在根目录下
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
        return jmcomic.JmOption.construct(option_dict)
    
    def save_album_info_to_json(self, album_detail, folder_path: str):
        """保存本子信息到JSON文件"""
        try:
            album_id = str(getattr(album_detail[0], 'album_id', 'unknown'))
            name = getattr(album_detail[0], 'oname', '未知标题')
            title = getattr(album_detail[0], 'name', '未知主标题')
            author = getattr(album_detail[0], 'author', '未知作者')
            tags = list(getattr(album_detail[0], 'tags', []))
        except Exception as e:
            print(f"提取本子信息出错: {e}")
            return False

        info = {
            "album_id": album_id,
            "title": title,
            "author": author,
            "tags": tags,
            "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        json_path = os.path.join(folder_path, "album_info.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2, default=str)
            print(f"本子信息已保存到: {json_path}")
            return True
        except Exception as e:
            print(f"保存JSON信息失败: {e}")
            return False

    def update_album_info_only(self, album_id):
        """仅获取并保存本子信息，不下载图片"""
        try:
            option = self.create_option()
            client = option.build_jm_client()
            album_detail = client.get_album_detail(album_id)
            folder_path = os.path.join(self.download_dir, album_id)
            os.makedirs(folder_path, exist_ok=True)
            self.save_album_info_to_json(album_detail, folder_path)
            return True
        except Exception as e:
            print(f"获取本子信息失败: {e}")
            return False

    def download_album_to_single_folder(self, album_id, download_dir=None):
        """下载指定ID的本子到同一个文件夹内"""
        if download_dir is None:
            download_dir = os.path.join(self.download_dir, album_id)
        os.makedirs(download_dir, exist_ok=True)

        try:
            option = self.create_option(download_dir)
            print(f"开始下载本子 {album_id} ...")
            album = jmcomic.download_album(album_id, option)
            print(f"本子 {album_id} 下载完成！保存在: {download_dir}")
            self.save_album_info_to_json(album, download_dir)
            return True
        except Exception as e:
            print(f"下载失败: {str(e)}")
            return False

    def get_album_id_from_user(self):
        """从用户输入获取本子ID"""
        album_id = input("请输入本子ID: ").strip()
        if not album_id:
            print("本子ID不能为空！")
            return None
        if not album_id.isdigit():
            print("本子ID必须为数字！")
            return None
        return album_id

    def update_all_local_album_info(self):
        """更新所有本地已存在的本子信息"""
        if not os.path.exists(self.download_dir):
            print("下载目录不存在")
            return

        folders = [f for f in os.listdir(self.download_dir) if f.isdigit()]
        print(f"找到 {len(folders)} 个本子目录，开始更新信息...")

        for i, album_id in enumerate(folders, 1):
            print(f"\n[{i}/{len(folders)}] 更新本子信息: {album_id}")
            self.update_album_info_only(album_id)

    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("JMComic 本子信息管理器")
        print("="*50)
        print("1. 下载本子并保存信息")
        print("2. 仅获取并保存本子信息（不下载）")
        print("3. 更新指定本子的信息")
        print("4. 更新所有本地本子的信息")
        print("0. 退出程序")
        print("="*50)

    def run(self):
        """主运行循环"""
        while True:
            self.show_menu()
            choice = input("请选择操作 (0-4): ").strip()
            
            if choice == "0":
                print("感谢使用，再见！")
                break
            elif choice == "1":
                album_id = self.get_album_id_from_user()
                if album_id:
                    self.download_album_to_single_folder(album_id)
            elif choice == "2":
                album_id = self.get_album_id_from_user()
                if album_id:
                    self.update_album_info_only(album_id)
            elif choice == "3":
                album_id = self.get_album_id_from_user()
                if album_id:
                    self.update_album_info_only(album_id)
            elif choice == "4":
                confirm = input("确定要更新所有本地本子的信息吗？(y/N): ").strip().lower()
                if confirm == 'y':
                    self.update_all_local_album_info()
                else:
                    print("操作已取消")
            else:
                print("无效选择，请重新输入！")

def main():
    downloader = AlbumDownloader()
    downloader.run()

if __name__ == "__main__":
    main()
