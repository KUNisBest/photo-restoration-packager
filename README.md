# Photo Restoration Packager

[English](README.en.md) | [简体中文](README.md)

这是一个可在中文环境使用的 Agent 技能与确定性工具集，用于提高低清照片清晰度、
从 PDF 中提取图片素材，并将处理结果连同来源信息打包。

它重点解决一个常见问题：PDF 或规则书并不是高清平面素材包，页面中的小图可能只有
90–330 像素宽。直接裁剪整页并超分，会让文字不可靠，还会补出不存在的细节。本项目将
原始素材提取、矢量重渲染、AI 辅助放大、质量检查和打包拆成独立步骤。

## 功能

- 使用官方 Real-ESRGAN 便携版提高普通照片清晰度。
- 检查 PDF 图片对象、页面位置、原始尺寸和文字重叠情况。
- 只提取明确加入白名单的无文字图片。
- 按指定 DPI 重新渲染矢量与多图层合成图。
- 避免对已经清晰的 600 dpi 合成图再次执行 AI 放大。
- 生成素材清单、原始预览、最终预览和经过校验的 ZIP。
- 始终保留原始文件。

## 为什么使用白名单

OCR 无法发现所有直接画进栅格图片中的文字。最稳妥的流程是：

1. 审计页面对象。
2. 人工或视觉模型检查哪些图片不含文字。
3. 编写嵌入式对象或裁剪框白名单。
4. 只处理白名单中的素材。
5. 核对数量、尺寸和最终压缩包。

这样可以避免标题、数字、房名、Logo 或教学标注被送进生成式放大器。

## 系统要求

- Python 3.11 或更高版本
- Pillow
- pypdf
- pdfplumber
- Poppler 的 `pdftoppm`
- 可选：支持 Vulkan 的显卡。官方 NCNN 版本也可使用 CPU，但速度明显更慢。

安装 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

确保 `pdftoppm` 已加入 `PATH`。

## 安装为 Codex 技能

将整个仓库目录复制到 Codex 技能目录：

```powershell
Copy-Item . "$HOME\.codex\skills\photo-restoration-packager" -Recurse
```

重启 Codex 或新建任务，让技能元数据重新加载。

中文请求示例：

```text
帮我把这张老照片变清晰，脸不要变形，保留原图并打包。
```

```text
检查这个 PDF 的第 2 页，只提取经过确认的无文字小图，放大后生成一个 ZIP。
```

## 命令行流程

### 1. 审计 PDF 页面

```powershell
python scripts/extract_pdf_assets.py `
  --pdf input.pdf `
  --page 2 `
  --output work/pdf-assets `
  --audit-only
```

检查 `work/pdf-assets/audit.json` 和渲染后的页面。

### 2. 创建白名单

参考 [references/allowlist.example.json](references/allowlist.example.json)：

```json
{
  "items": [
    {
      "name": "story_tile",
      "kind": "embedded",
      "object": "Im59"
    },
    {
      "name": "visitor_pawns",
      "kind": "crop",
      "box": [145.0, 520.0, 248.0, 561.7],
      "dpi": 600
    }
  ]
}
```

- `embedded`：提取 PDF 中原始的图片对象。
- `crop`：按指定 DPI 渲染 PDF 页面，再按左上角原点的页面坐标裁剪。

### 3. 提取白名单素材

```powershell
python scripts/extract_pdf_assets.py `
  --pdf input.pdf `
  --page 2 `
  --output work/pdf-assets `
  --selections selections.json
```

### 4. 只放大低分辨率栅格图

```powershell
python scripts/restore_assets.py `
  --input work/pdf-assets/source `
  --output work/pdf-assets/enhanced-4x `
  --scale 4 `
  --tile 512
```

如果工具不存在，脚本会自动下载官方 Real-ESRGAN NCNN 便携版到临时工具目录。
可以通过 `--gpu` 指定 Vulkan 显卡编号。

600 dpi 的矢量合成图不要放入这个批次，应单独保存到 `vector-renders/`。

### 5. 生成预览

```powershell
python scripts/make_contact_sheet.py `
  --input work/pdf-assets/source `
  --output work/pdf-assets/contact-source.png

python scripts/make_contact_sheet.py `
  --input work/pdf-assets/enhanced-4x work/pdf-assets/vector-renders `
  --output work/pdf-assets/contact-final.png
```

检查两张预览，确认没有文字图片混入，也没有放大失败。

### 6. 打包和校验

```powershell
python scripts/package_results.py `
  --root work/pdf-assets `
  --zip outputs/restored-assets.zip
```

脚本会生成 `qa-report.json`、检查 ZIP CRC，并输出压缩包 SHA256。

## 输出结构

```text
output/
  source/
  enhanced-4x/
  vector-renders/
  contact-source.png
  contact-final.png
  manifest.json
  qa-report.json
  README.md
```

## 保真原则

- `source extract`：不经过生成模型修改的原始解码像素。
- `AI-assisted upscale`：Real-ESRGAN 放大结果，纹理可能是模型补出的。
- `vector re-render`：将 PDF 文字和形状按更高 DPI 重新渲染。
- 不要把 AI 补出的纹理称为“恢复的真实细节”。
- 没有版权方确认时，不要把重建图称为“官方图稿”。
- 人像应单独核对身份一致性，不能只判断是否“更清晰”。
- 正式文档应重建文字和矢量层，不要直接超分整页截图。

详见 [references/fidelity-policy.md](references/fidelity-policy.md) 和
[references/pdf-asset-workflow.md](references/pdf-asset-workflow.md)。

## 测试

```powershell
python tests/smoke_test.py
```

测试包括：

- 技能元数据检查
- Python 脚本语法检查
- 合成图片打包
- ZIP 完整性检查

CI 不运行 GPU 推理，以免依赖特定显卡。

## 第三方项目

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)：BSD-3-Clause
- [GFPGAN](https://github.com/TencentARC/GFPGAN)：Apache-2.0
- [SUPIR](https://github.com/Fanghua-Yu/SUPIR)：无单独许可时仅限非商业使用

详见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。
