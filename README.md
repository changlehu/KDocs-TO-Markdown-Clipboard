# KDocs-TO-Markdown-Clipboard

> 将金山智能文档转换为 Markdown 格式，并永久保存图片到本地

## 项目简介

本项目提供了一套完整的解决方案，用于将金山智能文档（WPS 智能文档）转换为 Markdown 格式，并将文档中的图片下载到本地，确保图片永久有效。

## 为什么需要本项目？

### 金山文档官方工具的局限性

金山文档官方提供了 `kdocs-cli` 和 `kdocs-skill` 功能，可以将智能文档转换为 Markdown 格式。然而，这些工具存在以下问题：

1. **内容不完整**：官方工具转换后的 Markdown 是对原内容的重新提取与加工，默认内容与原结构不完全一致
2. **结构丢失**：无法严格保持原文档的完整结构和格式
3. **图片失效**：金山文档自带的图片链接虽然支持浏览，但有时间限制，一段时间后会失效
4. **无法下载图片**：官方 CLI 不支持下载图片到本地

### 本项目的优势

本项目通过以下方式解决了上述问题：

- **完整结构保留**：通过 JSON 获取文档的完整结构，再转换为 Markdown，确保内容完整性
- **图片永久保存**：自动提取文档中的图片链接，下载到本地 `img` 目录
- **链接自动替换**：将文档中的临时图片链接替换为本地图片地址，确保图片永久有效
- **简单易用**：通过剪贴板监听，一键完成转换和图片下载

## 功能特性

- ✅ 自动监听剪贴板，检测金山智能文档的复制内容
- ✅ 将 HTML 格式转换为标准的 Markdown 格式
- ✅ 自动保存转换后的 Markdown 到 `new.md` 文件
- ✅ 提取文档中的智能文档图片链接
- ✅ 下载图片到本地 `img` 目录，以图片 ID 命名
- ✅ 自动替换 Markdown 中的图片链接为本地路径
- ✅ 保持原文档的完整结构和格式

## 使用方法

### 前置要求

确保已安装以下 Python 依赖：

```bash
pip install markdownify pywin32 pyperclip requests
```

### 基本使用

#### 1. 转换智能文档为 Markdown

运行主脚本：

```bash
python wps2md_clipboard.py
```

**操作步骤**：

1. 在浏览器中打开金山智能文档
2. 全选内容区（使用 `Ctrl+A`，可能需要多按几次才能选中全部内容）
3. 按 `Ctrl+C` 复制内容
4. 脚本会自动检测剪贴板变化，将 HTML 转换为 Markdown
5. 转换完成后，Markdown 内容会自动复制到剪贴板，并保存到 `new.md` 文件

**注意**：使用 `Ctrl+A` 选择的内容仅包含内容区的具体内容，不包含标题区。

#### 2. 下载图片并更新链接

运行图片下载脚本：

```bash
python download_images.py
```

**功能说明**：

- 自动读取 `new.md` 文件（或指定的 Markdown 文件）
- 提取文档中的智能文档图片链接
- 下载图片到 `img` 目录，以图片 ID 命名（如 `3e4214aba52cf7d0dc53545e87846ac00a6814cb.png`）
- 自动替换 Markdown 中的图片链接为本地路径（如 `![](img/3e4214aba52cf7d0dc53545e87846ac00a6814cb.png)`）
- 支持指定文件名：`python download_images.py yourfile.md`

## 工作流程

```
金山智能文档 → 复制到剪贴板 → wps2md_clipboard.py → new.md (Markdown 格式)
                                                              ↓
                                                        download_images.py
                                                              ↓
                                              img/ 目录 (图片文件)
                                                              ↓
                                              new.md (更新图片链接)
```

## 配置选项

在 `wps2md_clipboard.py` 中可以调整以下配置：

```python
CONFIG = {
    "check_interval": 0.5,          # 剪贴板检查间隔（秒）
    "auto_convert": True,           # 是否自动转换
    "show_preview": True,           # 是否显示转换后的 Markdown 预览
    "preview_max_length": 500,      # 预览最大字符数
    "log_enabled": True,            # 是否记录日志
    "deduplicate": True,            # 是否去重（避免重复转换相同内容）
}
```

## 文件说明

- `wps2md_clipboard.py` - 主脚本，负责将智能文档转换为 Markdown 格式
- `download_images.py` - 图片下载脚本，负责下载图片并更新链接
- `new.md` - 转换后的 Markdown 文件
- `img/` - 图片存储目录
- `logs/` - 日志文件目录

## 技术实现

### 完整结构保留

本项目通过以下方式确保文档结构的完整性：

1. 从剪贴板获取 HTML 格式的完整内容
2. 使用 `markdownify` 库将 HTML 转换为 Markdown
3. 清理 WPS 特有的 HTML 属性和标记
4. 后处理 Markdown，优化格式

### 图片处理流程

1. 使用正则表达式提取智能文档图片链接（格式：`http://www.kdocs.cn/api/v3/office/copy/.../attach/object/{ID}?`）
2. 提取图片 ID（40 位哈希值）
3. 使用 `requests` 库下载图片
4. 保存为 PNG 格式，以图片 ID 命名
5. 使用正则表达式替换 Markdown 中的图片链接

## 常见问题

### Q: 为什么需要多按几次 Ctrl+A 才能选中全部内容？

A: 金山智能文档的内容区可能包含动态加载的内容，需要多次全选才能确保所有内容都被选中。

### Q: 转换后的 Markdown 格式不理想怎么办？

A: 可以调整 `wps2md_clipboard.py` 中的 `MarkdownConverter` 类的转换参数，或者手动编辑 `new.md` 文件。

### Q: 图片下载失败怎么办？

A: 检查网络连接，确保能够访问金山文档的图片服务器。如果某些图片下载失败，可以重新运行 `download_images.py` 脚本。

### Q: 如何处理多个文档？

A: 为每个文档创建单独的目录，或者使用 `download_images.py yourfile.md` 指定不同的文件名。

## 依赖项

- Python 3.x
- markdownify - HTML 转 Markdown
- pywin32 - Windows 剪贴板操作
- pyperclip - 跨平台剪贴板操作（备用）
- requests - HTTP 请求（下载图片）

## 许可证

MIT License

## 作者

changlehu@gmail.com

## 致谢

感谢金山文档提供的智能文档服务。

---

**注意**：本工具仅用于个人学习和研究，请遵守金山文档的使用条款。
