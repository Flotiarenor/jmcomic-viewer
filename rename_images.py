import os
import glob
import shutil
from datetime import datetime

def rename_images_to_new_folder(source_folder, target_folder=None):
    """
    按创建日期对图片进行重命名，并复制到新文件夹
    
    Args:
        source_folder (str): 源文件夹路径
        target_folder (str): 目标文件夹路径，如果为None则在源文件夹下创建"processed"文件夹
    """
    
    # 支持的图片格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp']
    
    # 创建目标文件夹
    if target_folder is None:
        target_folder = os.path.join(source_folder, "processed")
    
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    # 获取所有图片文件
    image_files = []
    for extension in image_extensions:
        image_files.extend(glob.glob(os.path.join(source_folder, extension)))
    
    if not image_files:
        print("未找到图片文件")
        return
    
    print(f"找到 {len(image_files)} 个图片文件")
    
    # 获取文件信息（路径、创建时间）
    files_info = []
    for file_path in image_files:
        try:
            # 获取创建时间
            creation_time = os.path.getctime(file_path)
            files_info.append({
                'path': file_path,
                'name': os.path.basename(file_path),
                'ctime': creation_time,
                'ext': os.path.splitext(file_path)[1].lower()
            })
        except Exception as e:
            print(f"警告: 无法获取文件信息 {file_path}: {e}")
    
    # 按创建时间排序
    files_info.sort(key=lambda x: x['ctime'])
    
    # 重命名并复制文件
    success_count = 0
    print(f"\n开始处理 {len(files_info)} 个文件...")
    
    for i, file_info in enumerate(files_info, 1):
        try:
            # 生成新文件名（5位数字格式）
            new_filename = f"{i:05d}{file_info['ext']}"
            new_file_path = os.path.join(target_folder, new_filename)
            
            # 检查目标文件是否已存在
            if os.path.exists(new_file_path):
                print(f"警告: 文件 {new_filename} 已存在，跳过 {file_info['name']}")
                continue
            
            # 复制文件到新文件夹并重命名
            shutil.copy2(file_info['path'], new_file_path)
            
            # 显示进度
            creation_date = datetime.fromtimestamp(file_info['ctime']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{i:05d}] {file_info['name']} -> {new_filename} ({creation_date})")
            success_count += 1
            
        except Exception as e:
            print(f"错误: 处理文件失败 {file_info['name']}: {e}")
    
    print(f"\n处理完成！成功处理 {success_count} 个文件")
    print(f"处理后的文件保存在: {target_folder}")

def main():
    print("=== 图片按创建日期重命名工具 ===")
    
    # 获取源文件夹路径
    while True:
        source_folder = input("请输入图片文件夹路径: ").strip().strip('"').strip("'")
        
        if not source_folder:
            print("路径不能为空，请重新输入")
            continue
            
        if not os.path.exists(source_folder):
            print("错误: 文件夹不存在，请重新输入")
            continue
            
        if not os.path.isdir(source_folder):
            print("错误: 输入的路径不是文件夹，请重新输入")
            continue
            
        break
    
    # 询问是否使用默认目标文件夹
    use_default = input("是否在源文件夹下创建'processed'文件夹？(y/n，默认y): ").strip().lower()
    
    target_folder = None
    if use_default not in ['n', 'no', '否']:
        target_folder = os.path.join(source_folder, "processed")
        print(f"将使用目标文件夹: {target_folder}")
    else:
        while True:
            target_folder = input("请输入目标文件夹路径: ").strip().strip('"').strip("'")
            if target_folder:
                break
            print("目标文件夹路径不能为空")
    
    # 确认操作
    print(f"\n源文件夹: {source_folder}")
    print(f"目标文件夹: {target_folder}")
    
    confirm = input("\n确认开始处理吗？这将复制并重命名所有图片(y/n): ").strip().lower()
    
    if confirm in ['y', 'yes', '是', '']:
        try:
            rename_images_to_new_folder(source_folder, target_folder)
        except Exception as e:
            print(f"程序执行出错: {e}")
    else:
        print("操作已取消")

if __name__ == "__main__":
    main()
