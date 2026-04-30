# -*- coding: utf-8 -*-
import re
import os
import requests
from urllib.parse import urlparse

"""
智能文档图片下载器
功能：读取 Markdown 文档，提取智能文档中的图片链接，下载图片并更新文档链接
使用方法：
    python download_images.py [markdown_file]
    如果不指定文件名，默认读取 new.md
"""

def extract_image_urls(markdown_content):
    """从 Markdown 内容中提取智能文档图片 URL"""
    # 匹配智能文档图片链接格式
    # 格式：http://www.kdocs.cn/api/v3/office/copy/.../attach/object/{ID}?
    pattern = r'https?://www\.kdocs\.cn/api/v3/office/copy/[^\s]+/attach/object/([a-f0-9]{40})\??'
    
    matches = re.findall(pattern, markdown_content)
    return matches

def download_image(url, output_path):
    """下载图片并保存为 PNG"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"下载图片失败 {url}: {e}")
        return False

def update_markdown_images(markdown_content, img_dir='img'):
    """更新 Markdown 中的图片链接"""
    # 确保图片目录存在
    os.makedirs(img_dir, exist_ok=True)
    
    # 提取图片 ID
    image_ids = extract_image_urls(markdown_content)
    
    if not image_ids:
        print("未找到智能文档图片链接")
        return markdown_content, 0
    
    print(f"找到 {len(image_ids)} 个智能文档图片")
    
    downloaded_count = 0
    updated_content = markdown_content
    
    for img_id in image_ids:
        # 构建原始 URL
        original_url = f"http://www.kdocs.cn/api/v3/office/copy/cEdzL041dWF0dEpneW9pQ08yRE4wbmtnZ281N0ROTmw4RXhpblRCckQvR0NOS3ZXblNaNUdldXA4cDkvVzRobUJ0dFhKQ1RWU2FGSjUyK3BreVdEUklnQlNhTUFKTkFnUEd6b1pINnV2cXR0MDB1azVCeXp5QUJVNUhjSldOU1B1enNPNTR1NEsyaXVubDhJTEJPNnJhcHp3ZUZGK0k4bWF0U0hXM3JreGNHeVJROUlUWjFFb01hNFRQelVidkhRam54Z3lqcGZNdGZHcnpVbWxiUnlFMXB0STgxYmtLRUE4cFlyYlhTNUptdEhLeFIrNUFxcGJuZTFsS1FaUzMvbGhKK1ZEM0M3ZVEwPQ==/attach/object/{img_id}?"
        
        # 构建本地图片路径
        local_filename = f"{img_id}.png"
        local_path = os.path.join(img_dir, local_filename)
        relative_path = f"{img_dir}/{local_filename}"
        
        # 检查文件是否已存在
        if os.path.exists(local_path):
            print(f"图片已存在: {local_filename}")
        else:
            # 下载图片
            print(f"正在下载: {img_id}")
            if download_image(original_url, local_path):
                downloaded_count += 1
                print(f"✓ 已保存: {local_path}")
            else:
                print(f"✗ 下载失败: {img_id}")
                continue
        
        # 替换 Markdown 中的链接
        # 匹配完整的智能文档图片链接并替换为本地路径
        old_pattern = rf'https?://www\.kdocs\.cn/api/v3/office/copy/[^\s]+/attach/object/{re.escape(img_id)}\??'
        new_link = f"{relative_path}"
        updated_content = re.sub(old_pattern, new_link, updated_content)
    
    return updated_content, downloaded_count

def main():
    import sys
    
    # 获取输入文件名
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "new.md"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：文件 {input_file} 不存在")
        return
    
    # 读取 Markdown 内容
    print(f"正在读取文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # 更新图片链接
    updated_content, downloaded_count = update_markdown_images(markdown_content)
    
    if downloaded_count > 0 or extract_image_urls(markdown_content):
        # 直接保存更新后的 Markdown
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"✓ 已更新文件: {input_file}")
    
    print(f"\n处理完成！")
    print(f"- 找到图片: {len(extract_image_urls(markdown_content))} 个")
    print(f"- 下载图片: {downloaded_count} 个")
    print(f"- 图片保存目录: img/")

if __name__ == "__main__":
    main()
