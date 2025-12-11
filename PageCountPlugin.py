from jmcomic import JmOptionPlugin, JmModuleConfig

class PageCountPlugin(JmOptionPlugin):
    """
    在下载过程中实时统计总图片数
    利用 before_album 重置计数器，before_photo 累加每个章节的图片数
    """
    plugin_key = 'page_counter'
    
    # 类变量存储结果：album_id -> total_pages
    # 使用字典支持多本子的并发统计
    _results = {}
    
    def invoke(self, **kwargs) -> None:
        """
        插件入口，由 jmcomic 在特定事件触发时调用
        通过判断 kwargs 中的参数类型来识别事件
        """
        # before_album 事件：包含 album 参数
        if 'album' in kwargs:
            album = kwargs['album']
            # 重置该 album_id 的计数器
            self._results[album.album_id] = 0
        
        # before_photo 事件：包含 photo 参数
        elif 'photo' in kwargs:
            photo = kwargs['photo']
            # 累加当前章节的图片数
            album_id = photo.from_album.album_id
            chapter_pages = len(photo)  # 这就是真实的章节图片数！
            
            # 累加（确保 album_id 已存在）
            if album_id not in self._results:
                self._results[album_id] = 0
            self._results[album_id] += chapter_pages
    
    @classmethod
    def get_total_pages(cls, album_id: str) -> int:
        """获取指定本子的总图片数"""
        return cls._results.get(album_id, 0)
    
    @classmethod
    def reset(cls, album_id: str = None):
        """重置计数器（可选）"""
        if album_id:
            cls._results.pop(album_id, None)
        else:
            cls._results.clear()