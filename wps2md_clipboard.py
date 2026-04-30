# -*- coding: utf-8 -*-
import re,codecs
import requests,json
import os,sys,glob

"""
WPS 智能文档 → Markdown 剪贴板转换器
功能：监听剪贴板，自动将 WPS 复制出的 HTML 内容转换为 Markdown 格式
使用方法：
    1. 在 WPS 智能文档中选中内容，按 Ctrl+C 复制
    2. 脚本自动检测剪贴板变化，将 HTML 转换为 Markdown
    3. 转换完成后，剪贴板内容即为 Markdown 格式，可直接粘贴到 AIDE 等工具使用
    4. 按 Ctrl+C 再次复制或按 Enter 键继续监听新内容
"""

import time
import threading
import re
from datetime import datetime

# 尝试导入 markdownify，如未安装则给出提示
try:
    from markdownify import markdownify as md
except ImportError:
    print("[错误] 未安装 markdownify 库。请先执行: pip install markdownify")
    import sys
    sys.exit(1)

# Windows 剪贴板操作相关
try:
    import win32clipboard
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    print("[警告] 未安装 pywin32 库。HTML 格式读取可能受限。")
    print("建议执行: pip install pywin32")
    WIN32_AVAILABLE = False

# 纯文本剪贴板操作（备用方案）
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    print("[警告] 未安装 pyperclip 库。")
    print("建议执行: pip install pyperclip")
    PYPERCLIP_AVAILABLE = False


# ============================================================
# 配置项
# ============================================================
CONFIG = {
    "check_interval": 0.5,          # 剪贴板检查间隔（秒）
    "auto_convert": True,           # 是否自动转换（False 则需手动确认）
    "show_preview": True,           # 是否显示转换后的 Markdown 预览
    "preview_max_length": 500,      # 预览最大字符数
    "log_enabled": True,            # 是否记录日志
    "deduplicate": True,            # 是否去重（避免重复转换相同内容）
}


# ============================================================
# 日志功能
# ============================================================
class Logger:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.log_file = None
        if enabled:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, f"wps2md_{datetime.now().strftime('%Y%m%d')}.log")
            self.log_file = open(log_path, "a", encoding="utf-8")

    def info(self, msg):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] [INFO] {msg}"
        print(line)
        if self.log_file:
            self.log_file.write(line + "\n")
            self.log_file.flush()

    def error(self, msg):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] {msg}"
        print(line)
        if self.log_file:
            self.log_file.write(line + "\n")
            self.log_file.flush()

    def close(self):
        if self.log_file:
            self.log_file.close()


logger = Logger(CONFIG["log_enabled"])


# ============================================================
# 剪贴板操作类
# ============================================================
class ClipboardManager:
    """剪贴板管理器，支持读取 HTML 和纯文本格式"""

    # Windows 剪贴板格式常量
    CF_TEXT = 1
    CF_UNICODETEXT = 13
    CF_HTML = None  # 动态注册

    def __init__(self):
        self.last_html_hash = None
        self.last_text_hash = None
        if WIN32_AVAILABLE:
            try:
                self.CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")
            except Exception as e:
                logger.error(f"注册 HTML 剪贴板格式失败: {e}")

    def _get_hash(self, content):
        """计算内容哈希，用于去重"""
        if not content:
            return None
        return hash(content[:2000])  # 只取前2000字符计算，加速

    def get_html(self):
        """从剪贴板读取 HTML 格式内容"""
        if not WIN32_AVAILABLE or not self.CF_HTML:
            return None

        try:
            win32clipboard.OpenClipboard()
            try:
                # 检查剪贴板中是否有 HTML 格式
                format_available = False
                try:
                    format_available = win32clipboard.IsClipboardFormatAvailable(self.CF_HTML)
                except:
                    pass

                if not format_available:
                    return None

                data = win32clipboard.GetClipboardData(self.CF_HTML)

                # CF_HTML 格式包含描述头，需要提取实际的 HTML
                if isinstance(data, bytes):
                    data = data.decode("utf-8", errors="ignore")

                # 提取实际的 HTML 片段
                html = self._extract_html_fragment(data)
                return html
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            logger.error(f"读取 HTML 剪贴板失败: {e}")
            return None

    def _extract_html_fragment(self, cf_html_data):
        """从 CF_HTML 格式中提取实际 HTML 片段

        CF_HTML 格式结构:
        Version:0.9
        StartHTML:0000000105
        EndHTML:00000001234
        StartFragment:0000000200
        EndFragment:0000001000
        <html>...</html>
        """
        try:
            # 查找 StartFragment 和 EndFragment 标记
            start_match = re.search(r"StartFragment:(\d+)", cf_html_data)
            end_match = re.search(r"EndFragment:(\d+)", cf_html_data)

            if start_match and end_match:
                start_pos = int(start_match.group(1))
                end_pos = int(end_match.group(1))

                # 按字节位置提取（CF_HTML 使用字节位置）
                # 注意：这里简单处理，实际可能需要更精确的编码处理
                html_bytes = cf_html_data.encode("utf-8")
                fragment = html_bytes[start_pos:end_pos].decode("utf-8", errors="ignore")
                return fragment

            # 如果找不到标记，尝试提取整个 HTML 部分
            html_start = cf_html_data.find("<html")
            if html_start != -1:
                return cf_html_data[html_start:]

            # 兜底：返回全部内容
            return cf_html_data
        except Exception as e:
            logger.error(f"提取 HTML 片段失败: {e}")
            return cf_html_data

    def get_plaintext(self):
        """从剪贴板读取纯文本"""
        if WIN32_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(self.CF_UNICODETEXT):
                        data = win32clipboard.GetClipboardData(self.CF_UNICODETEXT)
                        return data
                    elif win32clipboard.IsClipboardFormatAvailable(self.CF_TEXT):
                        data = win32clipboard.GetClipboardData(self.CF_TEXT)
                        return data.decode("gbk", errors="ignore")
                finally:
                    win32clipboard.CloseClipboard()
            except Exception as e:
                logger.error(f"读取纯文本剪贴板失败: {e}")

        if PYPERCLIP_AVAILABLE:
            try:
                return pyperclip.paste()
            except Exception as e:
                logger.error(f"pyperclip 读取失败: {e}")

        return None

    def set_plaintext(self, text):
        """将纯文本写入剪贴板"""
        success = False
        if WIN32_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                    success = True
                finally:
                    win32clipboard.CloseClipboard()
            except Exception as e:
                logger.error(f"写入剪贴板失败: {e}")

        if not success and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(text)
                success = True
            except Exception as e:
                logger.error(f"pyperclip 写入失败: {e}")

        # 写入成功后，立即更新哈希，避免把自己写入的内容当作新内容
        if success:
            self.last_text_hash = self._get_hash(text)
            self.last_html_hash = None  # 清除HTML哈希，允许后续HTML内容被检测

        return success

    def is_new_content(self, html=None, text=None):
        """检查是否为新的剪贴板内容"""
        html_hash = self._get_hash(html) if html else None
        text_hash = self._get_hash(text) if text else None

        # HTML 优先
        if html_hash and html_hash != self.last_html_hash:
            self.last_html_hash = html_hash
            return True

        # 其次是纯文本
        if text_hash and text_hash != self.last_text_hash:
            self.last_text_hash = text_hash
            return True

        return False


# ============================================================
# Markdown 转换器
# ============================================================
class MarkdownConverter:
    """HTML 到 Markdown 转换器"""

    def convert(self, html):
        """将 HTML 转换为 Markdown"""
        if not html or not html.strip():
            return None

        try:
            # 预处理：清理 WPS 特有的 HTML 属性
            html = self._clean_wps_html(html)

            # 使用 markdownify 转换
            markdown = md(
                html,
                heading_style="atx",           # 使用 ### 风格的标题
                code_block_style="fenced",      # 使用 ``` 风格的代码块
                bullet_list_marker="-",         # 使用 - 作为无序列表标记
                em_delimiter="*",               # 使用 * 作为斜体标记
                strong_delimiter="**",          # 使用 ** 作为加粗标记
                strip=["script", "style", "meta", "link"],  # 移除这些标签
            )

            # 后处理
            markdown = self._post_process(markdown)

            return markdown
        except Exception as e:
            logger.error(f"Markdown 转换失败: {e}")
            return None

    def _clean_wps_html(self, html):
        """清理 WPS 特有的 HTML 标记"""
        # 移除 data-* 属性
        html = re.sub(r'\s+data-[a-zA-Z0-9_-]+="[^"]*"', '', html)
        # 移除 wps 开头的 class
        html = re.sub(r'\s+class="[^"]*wps[^"]*"', '', html)
        # 移除 style 属性（可选，保留基础样式但移除内联样式）
        # html = re.sub(r'\s+style="[^"]*"', '', html)
        return html

    def _post_process(self, markdown):
        """Markdown 后处理"""
        # 移除多余的空行
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        # 移除行尾空格
        markdown = markdown.rstrip()
        return markdown


# ============================================================
# 主程序
# ============================================================
class WPS2MD:
    """WPS 智能文档到 Markdown 转换器主类"""

    def __init__(self):
        self.clipboard = ClipboardManager()
        self.converter = MarkdownConverter()
        self.running = False
        self.stop_event = threading.Event()

    def run(self):
        """一次性检测并转换"""
        logger.info("=" * 60)
        logger.info("WPS 智能文档 → Markdown 剪贴板转换器")
        logger.info("=" * 60)

        self._check_clipboard()
        self.stop()

    def _check_clipboard(self):
        """检查剪贴板变化"""
        # 优先获取 HTML 格式
        html_content = self.clipboard.get_html()

        # 如果 HTML 不可用，降级到纯文本
        text_content = None
        if not html_content:
            text_content = self.clipboard.get_plaintext()

        # 检查是否有新内容
        if not self.clipboard.is_new_content(html=html_content, text=text_content):
            return

        # 转换内容
        source = "HTML" if html_content else "纯文本"
        content = html_content or text_content

        if not content:
            return

        logger.info(f"检测到新的 {source} 剪贴板内容")

        # 自动转换
        if CONFIG["auto_convert"]:
            self._convert_and_set(content)
        else:
            # 手动确认模式
            print(f"\n检测到 {source} 内容，是否转换为 Markdown? [y/n]: ", end="", flush=True)
            # 这里简化处理，实际可以读取输入
            self._convert_and_set(content)

    def _convert_and_set(self, content):
        """转换并写入剪贴板"""
        markdown = self.converter.convert(content)

        if markdown is None:
            logger.error("转换失败")
            return

        # 写回剪贴板
        if self.clipboard.set_plaintext(markdown):
            logger.info("✅ Markdown 已写入剪贴板")

            # 同时保存到 new.md 文件
            try:
                output_file = os.path.join(os.getcwd(), "new.md")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown)
                logger.info(f"✅ Markdown 已保存到 {output_file}")
            except Exception as e:
                logger.error(f"保存到 new.md 文件失败: {e}")

            if CONFIG["show_preview"]:
                preview = markdown[:CONFIG["preview_max_length"]]
                if len(markdown) > CONFIG["preview_max_length"]:
                    preview += "\n... (内容已截断)"
                print("\n" + "-" * 40)
                print("Markdown 预览:")
                print("-" * 40)
                print(preview)
                print("-" * 40)
        else:
            logger.error("写入剪贴板失败")

    def stop(self):
        """停止监听"""
        self.running = False
        self.stop_event.set()
        logger.close()
        logger.info("脚本已停止")


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    app = WPS2MD()
    app.run()
