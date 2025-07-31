from mcp.server import FastMCP
from jmcomic import (
    create_option_by_file, JmOption, JmAlbumDetail, JmSearchPage, 
    JmCategoryPage, download_album, JmcomicException, JmMagicConstants
)
import os
import asyncio
import json
import itertools
import functools
import threading
import time
import argparse
import yaml
from PIL import Image
from typing import List, Optional

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='JM Comic MCP Server')
    parser.add_argument('--storage-path', type=str, help='自定义下载存储路径')
    # 使用parse_known_args来忽略未知参数，这样可以兼容mcp dev命令
    args, unknown = parser.parse_known_args()
    return args

def update_config_file(storage_path: str):
    """更新配置文件中的存储路径"""
    config_file = 'op.yml'
    try:
        # 读取现有配置
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 更新存储路径
        if 'dir_rule' not in config:
            config['dir_rule'] = {}
        config['dir_rule']['base_dir'] = storage_path
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"已更新配置文件 {config_file}，存储路径: {storage_path}")
        return True
    except Exception as e:
        print(f"更新配置文件失败: {e}")
        return False

# 解析命令行参数
args = parse_args()

# 如果提供了存储路径参数，更新配置文件
if args.storage_path:
    update_config_file(args.storage_path)

# It's good practice to use an option file for jmcomic
# For now, we can create a default one.
# A file `op.yml` could be created in the future for customization.
try:
    option = create_option_by_file('op.yml')
except FileNotFoundError:
    option = JmOption.default()

client = option.new_jm_client()
app = FastMCP('jm-comic-server')

# 统一的参数映射表
PARAM_MAPPINGS = {
    'order': {
        'latest': JmMagicConstants.ORDER_BY_LATEST,   # 'mr'
        'view': JmMagicConstants.ORDER_BY_VIEW,       # 'mv'
        'picture': JmMagicConstants.ORDER_BY_PICTURE, # 'mp'
        'like': JmMagicConstants.ORDER_BY_LIKE        # 'tf'
    },
    'time': {
        'today': JmMagicConstants.TIME_TODAY,   # 't'
        'week': JmMagicConstants.TIME_WEEK,     # 'w'
        'month': JmMagicConstants.TIME_MONTH,   # 'm'
        'all': JmMagicConstants.TIME_ALL        # 'a'
    },
    'category': {
        'all': JmMagicConstants.CATEGORY_ALL,               # '0'
        'doujin': JmMagicConstants.CATEGORY_DOUJIN,         # 'doujin'
        'single': JmMagicConstants.CATEGORY_SINGLE,         # 'single'
        'short': JmMagicConstants.CATEGORY_SHORT,           # 'short'
        'another': JmMagicConstants.CATEGORY_ANOTHER,       # 'another'
        'hanman': JmMagicConstants.CATEGORY_HANMAN,         # 'hanman'
        'meiman': JmMagicConstants.CATEGORY_MEIMAN,         # 'meiman'
        'doujin_cosplay': JmMagicConstants.CATEGORY_DOUJIN_COSPLAY, # 'doujin_cosplay'
        '3d': JmMagicConstants.CATEGORY_3D,                 # '3D'
        'english_site': JmMagicConstants.CATEGORY_ENGLISH_SITE  # 'english_site'
    }
}

def get_mapped_value(param_type: str, user_value: str, default_key: str = 'all') -> str:
    """
    根据参数类型和用户输入值获取对应的JM常量值
    
    Args:
        param_type: 参数类型 ('order', 'time', 'category')
        user_value: 用户输入的值
        default_key: 如果找不到映射时使用的默认键
    
    Returns:
        对应的JM常量值
    """
    mapping = PARAM_MAPPINGS.get(param_type, {})
    
    # 尝试获取用户输入值对应的常量
    result = mapping.get(user_value.lower())
    if result is not None:
        return result
    
    # 如果没找到，使用默认键
    result = mapping.get(default_key)
    if result is not None:
        return result
    
    # 如果默认键也没找到，使用第一个可用的值
    if mapping:
        return list(mapping.values())[0]
    
    # 最后的保险：返回一个安全的默认值
    return JmMagicConstants.CATEGORY_ALL if param_type == 'category' else \
           JmMagicConstants.TIME_ALL if param_type == 'time' else \
           JmMagicConstants.ORDER_BY_LATEST

# PDF转换工具函数
def sorted_numeric_filenames(file_list: List[str]) -> List[str]:
    """对文件名按数字部分排序"""
    def extract_number(s: str) -> int:
        name, _ = os.path.splitext(s)
        return int(''.join(filter(str.isdigit, name)) or 0)
    return sorted(file_list, key=extract_number)


def sorted_numeric_subdirs(subdir_list: List[str]) -> List[str]:
    """对子目录按数字排序，非数字目录排在最后"""
    def sort_key(x: str) -> tuple:
        if x.isdigit():
            return (0, int(x))
        else:
            return (1, x)
    return sorted(subdir_list, key=sort_key)


def convert_images_to_pdf(input_folder: str, output_path: str, pdf_name: str) -> bool:
    """
    将指定文件夹中的图片转换为PDF
    
    Args:
        input_folder: 输入文件夹路径，包含图片的目录
        output_path: 输出PDF的目录
        pdf_name: PDF文件名（不需要扩展名）
    
    Returns:
        bool: 转换是否成功
    """
    start_time = time.time()
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    # 确保输出目录存在
    output_path = os.path.normpath(output_path)
    os.makedirs(output_path, exist_ok=True)
    
    # 生成完整的PDF路径
    pdf_full_path = os.path.join(output_path, f"{os.path.splitext(pdf_name)[0]}.pdf")
    
    # 检查PDF是否已存在
    if os.path.exists(pdf_full_path):
        print(f"跳过已有PDF：{pdf_name}.pdf")
        return True
    
    image_paths = []
    
    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误：输入文件夹不存在 {input_folder}")
        return False
    
    # 获取所有子目录并排序
    try:
        subdirs = [d for d in os.listdir(input_folder) 
                  if os.path.isdir(os.path.join(input_folder, d))]
        subdirs = sorted_numeric_subdirs(subdirs)
    except Exception as e:
        print(f"错误：无法读取目录 {input_folder}，原因：{e}")
        return False
    
    # 如果没有子目录，直接处理当前目录的图片
    if not subdirs:
        try:
            files = [f for f in os.listdir(input_folder)
                    if os.path.isfile(os.path.join(input_folder, f)) 
                    and os.path.splitext(f)[1].lower() in allowed_extensions]
            files = sorted_numeric_filenames(files)
            for f in files:
                image_paths.append(os.path.join(input_folder, f))
        except Exception as e:
            print(f"警告：读取文件夹失败 {input_folder}，原因：{e}")
    else:
        # 处理子目录中的图片
        for subdir in subdirs:
            subdir_path = os.path.join(input_folder, subdir)
            try:
                files = [f for f in os.listdir(subdir_path)
                        if os.path.isfile(os.path.join(subdir_path, f)) 
                        and os.path.splitext(f)[1].lower() in allowed_extensions]
                files = sorted_numeric_filenames(files)
                for f in files:
                    image_paths.append(os.path.join(subdir_path, f))
            except Exception as e:
                print(f"警告：读取子目录失败 {subdir_path}，原因：{e}")
    
    if not image_paths:
        print(f"错误：在 {input_folder} 中未找到任何图片文件")
        return False
    
    try:
        def open_image(path: str) -> Optional[Image.Image]:
            """安全地打开图片并转换为RGB模式"""
            try:
                img = Image.open(path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                return img
            except Exception as e:
                print(f"警告：无法打开图片 {path}，原因：{e}")
                return None
        
        # 使用生成器延迟加载图片，避免内存占用过高
        print(f"[转换] 转换中：{pdf_name}")
        print(f"开始生成PDF：{pdf_full_path}")
        
        # 打开第一张图片作为PDF的基础
        valid_images = []
        for path in image_paths:
            img = open_image(path)
            if img:
                valid_images.append(img)
        
        if not valid_images:
            print("错误：没有有效图片可生成PDF")
            return False
        
        # 保存为PDF
        first_image = valid_images[0]
        other_images = valid_images[1:] if len(valid_images) > 1 else []
        
        first_image.save(
            pdf_full_path,
            "PDF",
            save_all=True,
            append_images=other_images,
            optimize=True,
            quality=85  # 设置压缩质量以减小文件大小
        )
        
        # 关闭所有图片以释放内存
        for img in valid_images:
            img.close()
        
        print(f"[成功] 成功生成PDF：{pdf_full_path}")
        print(f"处理完成，耗时 {time.time() - start_time:.2f} 秒")
        return True
        
    except Exception as e:
        print(f"[失败] 生成PDF失败：{e}")
        return False


def is_recent_directory(dir_path: str, max_age_minutes: int = 10) -> bool:
    """检查目录是否是最近创建的"""
    try:
        creation_time = os.path.getctime(dir_path)
        current_time = time.time()
        age_minutes = (current_time - creation_time) / 60
        return age_minutes <= max_age_minutes
    except:
        return False


def convert_album_to_pdf(album_dir: str, base_output_dir: Optional[str] = None) -> bool:
    """
    将下载的漫画专辑转换为PDF
    
    Args:
        album_dir: 专辑目录路径
        base_output_dir: PDF输出基础目录，如果为None则使用专辑目录的父目录
    
    Returns:
        bool: 转换是否成功
    """
    if not os.path.exists(album_dir):
        print(f"错误：专辑目录不存在 {album_dir}")
        return False
    
    # 获取专辑名称
    album_name = os.path.basename(album_dir)
    
    # 确定输出目录
    if base_output_dir is None:
        base_output_dir = os.path.dirname(album_dir)
    
    print(f"\n[转换] 开始转换专辑：{album_name}")
    
    # 转换为PDF
    success = convert_images_to_pdf(
        input_folder=album_dir,
        output_path=base_output_dir,
        pdf_name=album_name
    )
    
    if success:
        print(f"[完成] 专辑 {album_name} 转换完成")
    else:
        print(f"[失败] 专辑 {album_name} 转换失败")
    
    return success

@app.tool()
async def search_comic(
    query: str, 
    page: int = 1,
    main_tag: int = 0,
    order_by: str = 'latest',
    time_period: str = 'all',
    category: str = 'all'
) -> str:
    """
    Searches for comics on jmcomic with advanced filtering options.

    Args:
        query: The search query.
        page: The page number to retrieve. Defaults to 1.
        main_tag: Main tag filter. Defaults to 0.
        order_by: Sort order. Options: 'latest', 'view', 'picture', 'like'. Defaults to 'latest'.
        time_period: Time period filter. Options: 'today', 'week', 'month', 'all'. Defaults to 'all'.
        category: Category filter. Options: 'all', 'doujin', 'single', 'short', 'another', 
                 'hanman', 'meiman', 'doujin_cosplay', '3d', 'english_site'. Defaults to 'all'.

    Returns:
        A JSON string containing the search results.
    """
    try:
        # 使用统一的映射表获取对应的常量值
        order_value = get_mapped_value('order', order_by, 'latest')
        time_value = get_mapped_value('time', time_period, 'all')
        category_value = get_mapped_value('category', category, 'all')
        
        loop = asyncio.get_running_loop()
        func = functools.partial(
            client.search,
            search_query=query,
            page=page,
            main_tag=main_tag,
            order_by=order_value,
            time=time_value,
            category=category_value,
            sub_category=None
        )
        search_page: JmSearchPage = await loop.run_in_executor(
            None, func
        )
        results = []
        for album_id, title in itertools.islice(search_page, 20):  # 返回20个结果
            results.append({"id": album_id, "title": title})
        
        if not results:
            return json.dumps({"message": "No results found."})
        
        # 返回更详细的搜索信息
        response = {
            "search_params": {
                "query": query,
                "page": page,
                "main_tag": main_tag,
                "order_by": order_by,
                "time_period": time_period,
                "category": category
            },
            "constants_used": {
                "order_by": order_value,
                "time": time_value,
                "category": category_value
            },
            "results": results,
            "total_results": len(results)
        }
        
        return json.dumps(response, ensure_ascii=False)
    except JmcomicException as e:
        return json.dumps({"error": f"jmcomic error: {e}"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}"})

@app.tool()
async def get_album_details(album_id: str) -> str:
    """
    Gets the details of a comic album.

    Args:
        album_id: The ID of the album.

    Returns:
        A JSON string containing the album details.
    """
    try:
        loop = asyncio.get_running_loop()
        func = functools.partial(client.get_album_detail, album_id)
        album: JmAlbumDetail = await loop.run_in_executor(
            None, func
        )
        details = {
            "id": album.id,
            "title": album.title,
            "author": album.author,
            "tags": album.tags,
            "description": album.description,
        }
        return json.dumps(details, ensure_ascii=False)
    except JmcomicException as e:
        return json.dumps({"error": f"jmcomic error: {e}"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}"})

@app.tool()
async def get_ranking_list(period: str = 'week') -> str:
    """
    Gets the comic ranking list for a given period.

    Args:
        period: The time period for the ranking. Can be 'week', 'month', 'all'. Defaults to 'week'.

    Returns:
        A JSON string containing the ranking list.
    """
    try:
        loop = asyncio.get_running_loop()
        ranking_page = None
        period_lower = period.lower()

        if period_lower == 'month':
            func = functools.partial(client.month_ranking, page=1)
            ranking_page = await loop.run_in_executor(None, func)
        elif period_lower == 'all':
            func = functools.partial(
                client.categories_filter,
                page=1,
                category=JmMagicConstants.CATEGORY_ALL,
                time=JmMagicConstants.TIME_ALL,
                order_by=JmMagicConstants.ORDER_BY_VIEW
            )
            ranking_page = await loop.run_in_executor(None, func)
        else:  # Default to 'week'
            func = functools.partial(client.week_ranking, page=1)
            ranking_page = await loop.run_in_executor(None, func)

        results = []
        for album_id, title in itertools.islice(ranking_page, 10):
            results.append({"id": album_id, "title": title})
            
        return json.dumps(results, ensure_ascii=False)
    except JmcomicException as e:
        return json.dumps({"error": f"jmcomic error: {e}"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}"})

@app.tool()
async def filter_comics_by_category(
    category: str = 'all',
    time_period: str = 'all',
    order_by: str = 'latest',
    page: int = 1
) -> str:
    """
    Filters comics by category, time period, and sorting method.

    Args:
        category: The category to filter by. Options: 'all', 'doujin', 'single', 'short', 
                 'another', 'hanman', 'meiman', 'doujin_cosplay', '3D', 'english_site'.
                 Defaults to 'all'.
        time_period: The time period to filter by. Options: 'today', 'week', 'month', 'all'.
                    Defaults to 'all'.
        order_by: Sort order. Options: 'latest', 'view', 'picture', 'like'. Defaults to 'latest'.
        page: Page number to retrieve. Defaults to 1.

    Returns:
        A JSON string containing the filtered results.
    """
    try:
        # 使用统一的映射表获取对应的常量值
        category_value = get_mapped_value('category', category, 'all')
        time_value = get_mapped_value('time', time_period, 'all')
        order_value = get_mapped_value('order', order_by, 'latest')
        
        # 执行筛选请求
        loop = asyncio.get_running_loop()
        func = functools.partial(
            client.categories_filter,
            page=page,
            category=category_value,
            time=time_value,
            order_by=order_value
        )
        
        category_page: JmCategoryPage = await loop.run_in_executor(None, func)
        
        results = []
        for album_id, title in itertools.islice(category_page, 20):  # 返回20个结果
            results.append({"id": album_id, "title": title})
        
        if not results:
            return json.dumps({
                "message": f"No results found for category: {category}, time: {time_period}, order: {order_by}"
            })
        
        response = {
            "filters": {
                "category": category,
                "time_period": time_period,
                "order_by": order_by,
                "page": page
            },
            "results": results,
            "total_results": len(results)
        }
        
        return json.dumps(response, ensure_ascii=False)
        
    except JmcomicException as e:
        return json.dumps({"error": f"jmcomic error: {e}"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}"})

@app.tool()
async def download_comic_album(album_id: str, convert_to_pdf: bool = True) -> str:
    """
    Downloads a comic album and optionally converts it to PDF.

    Args:
        album_id: The ID of the album to download.
        convert_to_pdf: Whether to convert the downloaded images to PDF after download completes.

    Returns:
        A message indicating the download status and PDF conversion status.
    """
    def download_and_convert():
        """下载并转换的函数，在后台线程中运行"""
        try:
            print(f"[下载] 开始下载专辑 {album_id}")
            print(f"[调试] 下载目录: {option.dir_rule.base_dir}")
            
            # 先获取专辑详情以得到标题
            album_detail = client.get_album_detail(album_id)
            album_title = album_detail.title
            print(f"[调试] 专辑标题: {album_title}")
            
            # 执行下载
            download_album(album_id, option)
            print(f"[完成] 专辑 {album_id} 下载完成")
            
            # 检查下载目录
            download_dir = option.dir_rule.base_dir
            print(f"[调试] 检查下载目录: {download_dir}")
            
            # 使用专辑标题查找目录
            album_dir = os.path.join(download_dir, album_title)
            
            # 列出下载目录中的所有内容
            if os.path.exists(download_dir):
                entries = os.listdir(download_dir)
                print(f"[调试] 下载目录内容: {entries}")
                
                # 寻找专辑文件夹
                print(f"[调试] 期望的专辑目录（按标题）: {album_dir}")
                
                if os.path.exists(album_dir):
                    print(f"[调试] 找到专辑目录: {album_dir}")
                    # 列出专辑目录内容
                    album_contents = os.listdir(album_dir)
                    print(f"[调试] 专辑目录内容: {album_contents}")
                else:
                    print(f"[调试] 专辑目录不存在，查找可能的目录...")
                    # 查找可能的专辑目录 - 使用多种匹配策略
                    found_by_title = False
                    for entry in entries:
                        entry_path = os.path.join(download_dir, entry)
                        if os.path.isdir(entry_path):
                            print(f"[调试] 发现目录: {entry}")
                            # 策略1：完全匹配标题
                            if entry == album_title:
                                album_dir = entry_path
                                print(f"[调试] 完全匹配标题: {album_dir}")
                                found_by_title = True
                                break
                            # 策略2：标题包含关系
                            elif album_title in entry or entry in album_title:
                                album_dir = entry_path
                                print(f"[调试] 部分匹配标题: {album_dir}")
                                found_by_title = True
                                break
                    
                    # 如果通过标题没找到，再尝试其他策略
                    if not found_by_title:
                        for entry in entries:
                            entry_path = os.path.join(download_dir, entry)
                            if os.path.isdir(entry_path):
                                # 策略3：包含专辑ID
                                if album_id in entry:
                                    album_dir = entry_path
                                    print(f"[调试] 通过ID匹配: {album_dir}")
                                    break
                                # 策略4：最近创建的目录
                                elif is_recent_directory(entry_path, max_age_minutes=30):
                                    album_dir = entry_path
                                    print(f"[调试] 最近创建的目录: {album_dir}")
                                    break
            
            if convert_to_pdf:
                print(f"[转换] 开始转换专辑 {album_id} 为PDF")
                
                if os.path.exists(album_dir):
                    print(f"[调试] 使用目录进行转换: {album_dir}")
                    success = convert_album_to_pdf(album_dir, download_dir)
                    if success:
                        print(f"[成功] 专辑 {album_id} PDF转换完成")
                        # 检查PDF是否真的生成了
                        pdf_path = os.path.join(download_dir, f"{os.path.basename(album_dir)}.pdf")
                        if os.path.exists(pdf_path):
                            print(f"[验证] PDF文件已生成: {pdf_path}")
                        else:
                            print(f"[警告] PDF文件未找到: {pdf_path}")
                    else:
                        print(f"[失败] 专辑 {album_id} PDF转换失败")
                else:
                    print(f"[调试] 专辑目录不存在，查找可能的目录...")
                    # 查找可能的专辑目录
                    found_dir = None
                    if os.path.exists(download_dir):
                        # 获取所有目录并按创建时间排序
                        dir_candidates = []
                        for item in os.listdir(download_dir):
                            item_path = os.path.join(download_dir, item)
                            if os.path.isdir(item_path):
                                try:
                                    creation_time = os.path.getctime(item_path)
                                    dir_candidates.append({
                                        'path': item_path,
                                        'name': item,
                                        'creation_time': creation_time,
                                        'age_minutes': (time.time() - creation_time) / 60
                                    })
                                except:
                                    continue
                        
                        # 按创建时间排序，最新的在前
                        dir_candidates.sort(key=lambda x: x['creation_time'], reverse=True)
                        
                        # 查找最合适的目录
                        for candidate in dir_candidates:
                            print(f"[尝试] 检查目录: {candidate['name']} (创建于{candidate['age_minutes']:.1f}分钟前)")
                            
                            # 优先级1：完全匹配专辑标题
                            if candidate['name'] == album_title:
                                print(f"[找到] 完全匹配标题: {candidate['path']}")
                                found_dir = candidate['path']
                                break
                            
                            # 优先级2：部分匹配专辑标题
                            elif album_title in candidate['name'] or candidate['name'] in album_title:
                                print(f"[找到] 部分匹配标题: {candidate['path']}")
                                found_dir = candidate['path']
                                break
                            
                            # 优先级3：包含专辑ID的目录
                            elif album_id in candidate['name']:
                                print(f"[找到] 专辑ID匹配目录: {candidate['path']}")
                                found_dir = candidate['path']
                                break
                            
                            # 优先级4：最近30分钟内创建的目录（可能是刚下载的）
                            elif candidate['age_minutes'] <= 30:
                                # 检查目录是否包含图片文件
                                try:
                                    contents = os.listdir(candidate['path'])
                                    has_images = any(
                                        os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
                                        for f in contents
                                        if os.path.isfile(os.path.join(candidate['path'], f))
                                    )
                                    if has_images:
                                        print(f"[找到] 最近创建的图片目录: {candidate['path']}")
                                        found_dir = candidate['path']
                                        break
                                except:
                                    continue
                    
                    if found_dir:
                        print(f"[转换] 使用找到的目录进行转换: {found_dir}")
                        success = convert_album_to_pdf(found_dir, download_dir)
                        if success:
                            print(f"[成功] 专辑 {album_id} 使用 {found_dir} 转换PDF成功")
                            # 检查PDF是否真的生成了
                            pdf_path = os.path.join(download_dir, f"{os.path.basename(found_dir)}.pdf")
                            if os.path.exists(pdf_path):
                                print(f"[验证] PDF文件已生成: {pdf_path}")
                            else:
                                print(f"[警告] PDF文件未找到: {pdf_path}")
                        else:
                            print(f"[失败] 专辑 {album_id} PDF转换失败")
                    else:
                        print(f"[错误] 无法找到专辑 {album_id} 的下载目录")
            
        except JmcomicException as e:
            print(f"[错误] 下载专辑 {album_id} 失败: {e}")
            import traceback
            print(f"[调试] 详细错误信息:")
            traceback.print_exc()
        except Exception as e:
            print(f"[错误] 处理专辑 {album_id} 时发生错误: {e}")
            import traceback
            print(f"[调试] 详细错误信息:")
            traceback.print_exc()
    
    try:
        # 在后台线程中执行下载和转换
        thread = threading.Thread(target=download_and_convert, daemon=True)
        thread.start()
        
        conversion_msg = " 并转换为PDF" if convert_to_pdf else ""
        return f"专辑 {album_id} 的下载{conversion_msg}已在后台开始执行。请查看控制台输出获取详细信息。"
        
    except Exception as e:
        return f"启动专辑 {album_id} 下载失败: {e}"

@app.tool()
async def convert_album_to_pdf_tool(album_id: str, album_dir: Optional[str] = None) -> str:
    """
    Converts a downloaded comic album to PDF.

    Args:
        album_id: The ID of the album.
        album_dir: Optional custom path to the album directory. If not provided, 
                  will use the default download directory + album_id.

    Returns:
        A message indicating the conversion status.
    """
    try:
        # 确定专辑目录
        if album_dir is None:
            download_dir = option.dir_rule.base_dir
            album_dir = os.path.join(download_dir, album_id)
        
        if not os.path.exists(album_dir):
            return f"错误：专辑目录不存在 {album_dir}"
        
        # 在后台执行转换
        loop = asyncio.get_running_loop()
        
        def convert():
            base_output_dir = os.path.dirname(album_dir)
            return convert_album_to_pdf(album_dir, base_output_dir)
        
        success = await loop.run_in_executor(None, convert)
        
        if success:
            return f"[成功] 专辑 {album_id} 已成功转换为PDF"
        else:
            return f"[失败] 专辑 {album_id} PDF转换失败"
            
    except Exception as e:
        return f"转换专辑 {album_id} 为PDF时发生错误: {e}"



if __name__ == "__main__":
    app.run(transport='stdio')
