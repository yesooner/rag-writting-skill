# RAG Writing Skill

[English](README.md)

<p align="center">
  <a href="./README.md"><img alt="Language English" src="https://img.shields.io/badge/Language-English-lightgrey"></a>
  <a href="./README.zh-CN.md"><img alt="语言 中文" src="https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E4%B8%AD%E6%96%87-blue"></a>
  <a href="./LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-orange"></a>
</p>

RAG Writing Skill 是一套面向 Claude Code 和 Codex 的通用写作辅助 skill，用于整理论文资料、生成 typed RAG cards、管理资料角色、修复顺序编码制引用，并按用户确认的格式表修改 Word 文档。

## 功能概览

本仓库包含 4 个子 skill：

```text
article-rag-chunking
source-role-policy
citation-registry
word-formatting
```

默认协作流程：

```text
source-role-policy
-> article-rag-chunking
-> citation-registry
-> word-formatting（仅在需要处理 .docx 时使用）
```

## Claude Code 调用

作为 Claude Code plugin 安装后，使用命名空间调用：

```text
/rag-writing-skill:article-rag-chunking
/rag-writing-skill:source-role-policy
/rag-writing-skill:citation-registry
/rag-writing-skill:word-formatting
```

验证 plugin：

```powershell
claude plugin validate .
```

## Codex 调用

Codex 不依赖 Claude Code slash command。可以用自然语言或显式 skill 名触发：

```text
use article-rag-chunking
use source-role-policy
use citation-registry
use word-formatting
```

## Python 环境

推荐使用独立 Python 环境，不要默认安装到 conda `base`。

```powershell
python -m pip install -r requirements.txt
```

或：

```powershell
conda env create -f environment.yml
conda activate rag-writing-skill
```

运行验证：

```powershell
python -X utf8 scripts\verify_release.py --root .
```

## article-rag-chunking

用途：读取论文、专利、标准、报告、数据说明或笔记来源，抽取本地和可选外部元数据，生成 typed RAG cards，并输出需要用户确认的默认排序表。

关键规则：

- 第一次执行 RAG job 时，必须先询问用户 `output_root`。
- 所有生成文件必须写入 `<output_root>` 下。
- 支持 Markdown/Text 和结构化 JSON 作为 carding 输入。
- 同一 `source_id` 同时存在结构化 JSON 和 Markdown 时，优先使用结构化 JSON；如果 JSON 只是元数据，则回退到 Markdown。
- 不得编造 DOI、引用量、期刊指标或缺失标识符。
- 默认排序表只是建议，用户确认前不得写入 confirmed ranking。

主要输出目录：

```text
<output_root>\cleaned
<output_root>\metadata
<output_root>\cards
<output_root>\ranking
<output_root>\logs
```

支持的 `content_kind`：

```text
section
text
table
figure
equation
data
term
citation
standard_clause
patent_claim
method
result
```

常见映射：

```text
正文段落 -> text -> section_card 或 evidence_card
章节标题 -> section -> section_card
表格 -> table -> table_card
图片、图题、图注 -> figure -> figure_card
公式、公式说明 -> equation -> equation_card
Excel/CSV/数据说明 -> data -> data_card
术语定义、中英术语 -> term -> term_card
文献条目、引用上下文 -> citation -> citation_card
标准条文 -> standard_clause -> standard_card
专利权利要求、摘要、说明书片段 -> patent_claim -> patent_card
方法步骤、算法、模型设置 -> method -> method_card
结果、机制、对比、结论证据 -> result -> result_card
```

标准管线：

```powershell
python -X utf8 skills\article-rag-chunking\scripts\run_rag_pipeline.py `
  --input-dir "<source-folder>" `
  --output-root "<output_root>" `
  --providers crossref,openalex
```

本地离线模式：

```powershell
python -X utf8 skills\article-rag-chunking\scripts\run_rag_pipeline.py `
  --input-dir "<source-folder>" `
  --output-root "<output_root>" `
  --no-network
```

## source-role-policy

用途：分类资料来源，并设置可见引用和文末参考文献权限。

来源类别：

```text
A_core
B_background
C_method
D_internal
unclassified
```

| source_class | 含义 | 默认可见引用 | 默认进入参考文献 |
|---|---|---:|---:|
| `A_core` | 核心目标来源、主要证据、关键对比、核心专利或核心标准 | 是 | 是 |
| `B_background` | 背景、综述、研究现状和问题提出 | 是 | 是 |
| `C_method` | 方法、模型、流程、标准、公式、指标或术语 | 是 | 是 |
| `D_internal` | 项目数据、内部报告、笔记、私有文件或未公开资料 | 否 | 否 |
| `unclassified` | 暂不能确定分类，必须等待用户确认 | 否 | 否 |

支持的 `source_type`：

```text
paper
review
patent
standard
code
guideline
regulation
report
dataset
spreadsheet
note
book
thesis
web
```

关键规则：

- A/B/C/D 的定义由 `source-role-policy` 负责。
- 专利、标准、规范和指南是 `source_type`。
- `D_internal` 默认只作为内部证据。
- `source_class` 不决定参考文献编号。

## citation-registry

用途：登记可见引用，按正文首次出现顺序分配参考文献编号，去重来源，并重建 GB/T 7714 风格的顺序编码制参考文献。

规则：

- 按正文首次可见引用位置编号。
- 同一来源重复引用时沿用首次编号。
- 同步修改正文引用编号和文末参考文献编号。
- 不按 source class、排序表、作者、年份或重要性排序参考文献。
- 不得编造 DOI 或标识符。
- 内部数据证据默认不进入文末参考文献，除非用户明确允许。

## word-formatting

用途：根据用户确认的格式表检查和修改 `.docx` 文件。

必须先确认的格式表至少包括：

| 部分 | 样式名 | 中文字体 | 英文字体 | 字号 pt | 加粗 | 对齐 | 行距 | 段前 pt | 段后 pt | 首行缩进 | 备注 |
|---|---|---|---|---:|---|---|---:|---:|---:|---|---|
| 正文 | Body | 宋体 | Times New Roman | 12 | 否 | 两端对齐 | 1.5 | 0 | 0 | 2 字符 | 正文段落 |
| 一级标题 | H1 | 黑体 | Times New Roman | 14 | 是 | 左对齐 | 1.5 | 0 | 0 | 无 | 顶层章节 |
| 二级标题 | H2 | 黑体 | Times New Roman | 12 | 是 | 左对齐 | 1.5 | 0 | 0 | 无 | 二级章节 |
| 图题 | Figure Caption | 宋体 | Times New Roman | 10.5 | 是 | 居中 | 1.0 | 0 | 0 | 无 | 图下方题注 |
| 表题 | Table Caption | 宋体 | Times New Roman | 10.5 | 是 | 居中 | 1.0 | 0 | 0 | 无 | 表上方题注 |
| 表内文字 | Table Text | 宋体 | Times New Roman | 10.5 | 否 | 居中 | 1.0 | 0 | 0 | 无 | 表格内容 |
| 参考文献 | Reference | 宋体 | Times New Roman | 10.5 | 否 | 两端对齐 | 1.0 | 0 | 0 | 悬挂缩进 | 文末参考文献 |
| 公式 | Formula | Cambria Math | Cambria Math | 12 | 否 | 居中 | 1.0 | 0 | 0 | 无 | 独立公式 |

配置可控制：

- 页面设置
- 页眉页脚
- 样式名和字体
- 段落识别规则
- 图片和图题处理
- 表格格式
- 引用编号上标
- 公式保护
- 中文与英文、数字混排空格规范化

中英数字混排空格规则：

- 中文字符和英文字母、阿拉伯数字之间不保留空格。
- `我 love 你` 应改为 `我love你`。
- `第 1 个 model` 应改为 `第1个model`。
- 检查报告包含 `cjk_alnum_spacing_issue_count`、`cjk_latin_spacing_issue_count` 和示例。
- 只有在确认配置启用 `normalize_cjk_latin_spacing` 时，格式化脚本才自动删除这些空格。

公式保护规则：

- 修改前后检查公式节点或公式 XML 哈希。
- 如果公式或图片数量异常，必须中止保存。
- 不得改变正文文本内容，除非用户确认启用混排空格规范化。

常用命令：

```powershell
python -X utf8 skills\word-formatting\scripts\format_docx.py `
  --write-template "<config.json>"

python -X utf8 skills\word-formatting\scripts\inspect_docx.py `
  --docx "<target.docx>" --config "<confirmed-config.json>"

python -X utf8 skills\word-formatting\scripts\format_docx.py `
  --docx "<target.docx>" --config "<confirmed-config.json>"
```

格式化后的报告应包括：

- 目标文件路径
- 备份文件路径
- 样式完整性
- 图片数量
- 图表格数量
- 正文游离图片段落数量
- 正文引用数量和上标数量
- 参考文献列表编号上标数量
- 公式节点数量和哈希状态
- 普通表格数量
- 中英数字混排空格问题数量和示例
- 启用规范化时删除的中英数字混排空格数量

## 目录结构

```text
.claude-plugin/
skills/
  article-rag-chunking/
  source-role-policy/
  citation-registry/
  word-formatting/
scripts/
requirements.txt
environment.yml
request.txt
README.md
README.zh-CN.md
```
