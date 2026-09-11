> [!WARNING]
> **本项目已停止维护，不再接收任何更新。**
> 后续更新与维护已迁移至通用架构程序工具组 **OmniBox**：<https://github.com/Flotiarenor/OmniBox>
> 本仓库仅作为历史归档保留，请前往新仓库获取最新版本。

# JM Viewer - 本子管理器与查看器（已停止维护 / ARCHIVED）

JM Viewer 是一个采用 Apache 2.0 许可证的开源项目，提供完整的本地漫画管理解决方案。项目包含下载、查看和整理工具，支持原始版本和修复版本的无缝切换，支持多章节。

## 许可证说明

本项目采用 **[Apache License 2.0](./LICENSE)** 开源许可证：
完整许可条款：[https://www.apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0)


## 功能特性

### 📥 下载管理器 (`download_jm.py`)
- **智能下载**: 从指定ID下载本子到本地文件夹
- **信息管理**: 自动保存本子元数据到JSON
- **批量更新**: 一键更新所有已下载本子信息
- **多线程**: 高效下载图片资源

### 🖼️ 图形化查看器 (`jm_viewer-2.0.py`)
- **双界面设计**: 列表浏览 + 图片查看器
- **智能筛选**: 支持按标题、作者、标签搜索
- **高清查看**: 缩放/拖拽/切换翻页方向
- **AI版本切换**: 原始版本与修复版本切换
- **键盘快捷键**: 空格翻页/+-缩放/R键重置

### 🔄 图片重命名工具 (`rename_images.py`)
- **按时间排序**: 按创建日期智能排序图片
- **标准命名**: 生成00001.jpg格式的文件名
- **操作**: 复制文件而非移动(生成文件后需要手动移动，防止误操作)

## 快速设置

```bash
# 克隆仓库
git clone https://github.com/flotiarenor/jm_viewer.git
cd jm_viewer

# 安装依赖
pip install jmcomic 
```

## 使用指南

### 1. 下载本子
```bash
python download_jm.py
```


### 2. 使用查看器
```bash
python jm_viewer-2.0.py
```

- **键盘快捷键**:
  - `空格键`/`右箭头`: 下一页
  - `左箭头`: 上一页
  - `+/-`: 缩放图片
  - `R`: 重置视图
  - `ESC/B`: 返回列表


### 3. 整理外部来源
```bash
python rename_images.py
```

## 项目结构
```
jm_viewer-2.0/
├── LICENSE               # Apache 2.0许可证
├── download_jm.py        # 下载器
├── jm_viewer-2.0.py      # 主查看器
├── rename_images.py      # 图片重命名
├── config.json           # 标签配置文件(自定义的标签列表)
└── comics/               # 单章节存储目录
    ├── [comic_id]/
    │   ├── album_info.json
    │   ├── 00001.jpg
    │   ├── 00002.jpg
    │   └── ai/           # 修复版本目录
    └── [comic_id]/       # 多章节存储目录
        ├── album_info.json
        └──[章节]
            ├── 00001.jpg
            └── 00002.jpg


