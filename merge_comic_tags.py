import json
import os
from collections import defaultdict
from typing import List, Dict, Any

def merge_and_filter_tags(json_files: List[str], weight_threshold: float = 0.1) -> Dict[str, Any]:
    """
    合并多个JSON标签文件并根据权重阈值过滤标签，按权重降序排序
    """
    merged_tags = {}
    tag_counts = defaultdict(int)
    tag_weights_sum = defaultdict(float)
    
    total_files = len(json_files)
    print(f"开始处理 {total_files} 个JSON文件...")
    
    # 1. 读取所有文件并累加权重和计数
    for i, json_file in enumerate(json_files, 1):
        print(f"正在处理文件 {i}/{total_files}: {os.path.basename(json_file)}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
                
            # 遍历列表中每一个标签字典
            for data in data_list:
                if isinstance(data, dict):
                    for tag, weight in data.items():
                        tag_weights_sum[tag] += weight
                        tag_counts[tag] += 1
                else:
                    print(f"警告：JSON文件 {json_file} 中存在非字典条目")
                    
        except Exception as e:
            print(f"处理文件 {json_file} 时出错: {str(e)}")
            continue
    
    # 2. 计算平均权重并过滤
    print("\n计算平均权重并过滤标签...")
    original_tag_count = len(tag_counts)
    
    for tag in list(tag_counts.keys()):  # 使用list()避免在迭代时修改字典
        avg_weight = tag_weights_sum[tag] / tag_counts[tag]
        if avg_weight >= weight_threshold:
            merged_tags[tag] = avg_weight
        else:
            # 移除不符合条件的标签
            del tag_weights_sum[tag]
            del tag_counts[tag]
    
    # 按权重降序排序
    sorted_merged_tags = dict(sorted(merged_tags.items(), key=lambda x: x[1], reverse=True))
    
    print(f"原始标签数: {original_tag_count}, 过滤后标签数: {len(sorted_merged_tags)}")
    return sorted_merged_tags

def find_manga_directories(comic_dir: str, update_all: bool = False) -> List[str]:
    """
    查找需要处理的漫画目录
    
    参数:
        comic_dir: 漫画根目录
        update_all: 是否更新所有漫画，False则只处理没有merged_tags.json的
    """
    manga_dirs = []
    print(f"正在扫描漫画目录: {comic_dir}")
    
    if not os.path.isdir(comic_dir):
        raise ValueError(f"目录不存在: {comic_dir}")
    
    # 遍历comic目录下的所有数字ID文件夹
    for item in os.listdir(comic_dir):
        item_path = os.path.join(comic_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            album_info_path = os.path.join(item_path, 'merged_tags.json')
            
            # 如果要更新所有或者该漫画还没有merged_tags.json
            if update_all or not os.path.exists(album_info_path):
                tag_dir = os.path.join(item_path, 'tag')
                if os.path.exists(tag_dir) and os.path.isdir(tag_dir):
                    manga_dirs.append(item_path)
                    print(f"找到待处理漫画: {item}")
    
    if not manga_dirs:
        print("没有找到需要处理的漫画目录")
    
    return manga_dirs

def process_single_manga(manga_dir: str, weight_threshold: float = 0.1) -> bool:
    """
    处理单个漫画目录
    
    参数:
        manga_dir: 漫画目录路径
        weight_threshold: 权重阈值
    
    返回:
        是否处理成功
    """
    try:
        tag_dir = os.path.join(manga_dir, 'tag')
        if not os.path.exists(tag_dir):
            print(f"警告: {manga_dir} 中没有tag目录")
            return False
        
        # 查找所有JSON文件
        json_files = []
        for root, _, files in os.walk(tag_dir):
            for file in files:
                if file.lower().endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print(f"警告: {tag_dir} 中没有找到JSON文件")
            return False
        
        print(f"\n处理漫画目录: {os.path.basename(manga_dir)}")
        print(f"找到 {len(json_files)} 个JSON文件")
        
        # 合并并过滤标签
        merged_tags = merge_and_filter_tags(json_files, weight_threshold)
        
        # 保存结果到 merged_tags.json
        output_file = os.path.join(manga_dir, 'merged_tags.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_tags, f, indent=2, ensure_ascii=False)
        
        print(f"漫画 {os.path.basename(manga_dir)} 处理完成!")
        print(f"保留标签数: {len(merged_tags)}")
        print(f"结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"处理漫画 {manga_dir} 时出错: {str(e)}")
        return False

def save_merged_tags(merged_tags: Dict[str, Any], output_file: str):
    """将合并后的标签保存到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_tags, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 50)
    print("漫画标签合并与过滤工具")
    print("=" * 50)

    # 使用 input 替代 argparse
    comic_dir = input("请输入漫画根目录路径 (例如: comic): ").strip()
    if not comic_dir:
        comic_dir = 'comic'
    
    threshold_input = input("请输入权重阈值 (默认: 0.1): ").strip()
    try:
        weight_threshold = float(threshold_input) if threshold_input else 0.1
    except ValueError:
        print("输入格式错误，使用默认阈值 0.1")
        weight_threshold = 0.1

    update_choice = input("处理模式选择:\n1. 只处理没有merged_tags.json的漫画 (默认)\n2. 更新所有漫画\n请输入选择 (1/2): ").strip()
    update_all = update_choice == '2'

    try:
        # 查找所有需要处理的漫画目录
        manga_dirs = find_manga_directories(comic_dir, update_all)
        
        if not manga_dirs:
            print("没有找到需要处理的漫画目录")
            return
        
        print(f"\n总共需要处理 {len(manga_dirs)} 个漫画")
        
        # 处理每个漫画
        success_count = 0
        for manga_dir in manga_dirs:
            if process_single_manga(manga_dir, weight_threshold):
                success_count += 1
        
        print(f"\n处理完成!")
        print(f"成功处理: {success_count}/{len(manga_dirs)} 个漫画")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == '__main__':
    main()
