# RAG Writing Skill

[English](README.md)

<p align="center">
  <a href="./README.md"><img alt="Language English" src="https://img.shields.io/badge/Language-English-lightgrey"></a>
  <a href="./README.zh-CN.md"><img alt="语言 中文" src="https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E4%B8%AD%E6%96%87-blue"></a>
  <a href="./LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-orange"></a>
</p>

RAG Writing Skill 是一套面向 Claude Code 和 Codex 的通用写作辅助 skill，用于整理论文资料、生成 typed RAG cards、规划章节 query、执行混合检索、检查断言证据映射、修复顺序编码制引用，并按用户确认的格式表修改 Word 文档。

## 功能概览

本仓库包含 9 个子 skill：

```text
research-workflow
article-rag-chunking
source-role-policy
query-planner
hybrid-retrieval
section-writing-router
claim-evidence-checker
citation-registry
word-formatting
```

默认协作流程：

```text
research-workflow
-> source-role-policy
-> article-rag-chunking
-> query-planner
-> hybrid-retrieval
-> section-writing-router
-> claim-evidence-checker
-> citation-registry
-> word-formatting（仅在需要处理 .docx 时使用）
```

需要完整“人工定题到报告初稿”流程时，优先调用 `research-workflow`。如果资料已经筛选完成、只需要做 RAG 卡片，则直接调用 `article-rag-chunking`。

仅做 RAG 的流程：

```text
source-role-policy
-> article-rag-chunking
-> query-planner
-> hybrid-retrieval
-> section-writing-router
-> claim-evidence-checker
-> citation-registry
-> word-formatting（仅在需要处理 .docx 时使用）
```

## Claude Code 调用

作为 Claude Code plugin 安装后，使用命名空间调用：

```text
/rag-writing-skill:research-workflow
/rag-writing-skill:article-rag-chunking
/rag-writing-skill:source-role-policy
/rag-writing-skill:query-planner
/rag-writing-skill:hybrid-retrieval
/rag-writing-skill:section-writing-router
/rag-writing-skill:claim-evidence-checker
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
use research-workflow
use article-rag-chunking
use source-role-policy
use query-planner
use hybrid-retrieval
use section-writing-router
use claim-evidence-checker
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

## research-workflow

用途：执行完整的人机协作调研流程，从人工定题到 AI 生成综述/报告初稿，再到人工修改定稿。

默认流程：

```text
人工定题
-> AI 辅助检索
-> 人工筛选
-> AI 整理证据
-> 人工确认结论
-> AI 生成报告综述初稿
-> 人工修改定稿
```

默认只生成少量核心文件：

```text
<output_root>\research_brief.md
<output_root>\workflow_state.json
<output_root>\source_candidates.csv
<output_root>\evidence_registry.csv
<output_root>\human_decisions.md
<output_root>\report_draft_v1.md
<output_root>\qa_checklist.md
```

报告初稿和最终稿必须使用版本号命名，例如 `report_draft_v1.md`、`report_draft_v2.md`、`final_report_v1.md`，不得覆盖已有版本。用户可见输出默认使用中文；英文论文题名、专利题名、标准号、DOI、机构名、专有名词和必要原文引文可保留原文。

支持论文、综述、专利、标准、规范、指南、法规、技术规格、报告、数据集和网页来源。暂时没有的标准/规范类资料可标记为 `not_searched` 或 `needed_later`，不得编造。

用于论文写作时，`workflow_state.json` 防止跳步：

```text
query_plan_status -> retrieval_status -> section_draft_status -> claim_check_status -> citation_status
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

## query-planner

用途：把论文任务拆成章节级检索 query。

输出：

```text
<output_root>\queries\query_plan.json
```

脚本：

```powershell
python -X utf8 skills\query-planner\scripts\build_query_plan.py `
  --output-root "<output_root>" --title "<article title>"
```

默认章节目的：

```text
Introduction：背景、研究空白、研究现状
Method：模型设置、参数依据、标准/规范、公式/指标
Results：对比、机制解释、破坏模式
Discussion：局限性、矛盾、工程意义
```

## hybrid-retrieval

用途：基于 card 执行混合检索，包括 BM25 或关键词检索、可选 dense retrieval、source_class 过滤、content_kind 过滤和章节目的 rerank。

输出：

```text
<output_root>\retrieval\retrieval_trace.jsonl
```

脚本：

```powershell
python -X utf8 skills\hybrid-retrieval\scripts\retrieve_cards.py `
  --output-root "<output_root>"
```

## section-writing-router

用途：按论文章节选择不同 RAG 策略。

```text
Introduction -> A_core + B_background
Method -> C_method + standard/equation/method cards
Results -> A_core + result/table/figure cards
Discussion -> A_core + contradiction + limitation evidence
```

## claim-evidence-checker

用途：检查每个事实性断言是否有证据 card、source 权限、页码/位置和引用记录支撑。

输出：

```text
<output_root>\claims\claim_registry.jsonl
<output_root>\claims\evidence_units.jsonl
<output_root>\claims\claim_evidence_map.jsonl
<output_root>\qa\unsupported_claims.csv
<output_root>\qa\weak_evidence_claims.csv
<output_root>\qa\citation_mismatch.csv
```

脚本：

```powershell
python -X utf8 skills\claim-evidence-checker\scripts\check_claim_evidence.py `
  --output-root "<output_root>"
```

检查规则：

```text
事实性 claim 必须有 source_id
关键 claim 必须有 page_or_location
公式 claim 必须有 equation_card 或 C_method source
结果 claim 必须有 result/table/figure 证据
D_internal 默认不能作为公开参考文献证据
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
technical_specification
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
- 专利、标准、规范、指南、法规和技术规格是 `source_type`。
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
- 未使用自定义样式删除

中英数字混排空格规则：

- 中文字符和英文字母、阿拉伯数字之间不保留空格。
- `我 love 你` 应改为 `我love你`。
- `第 1 个 model` 应改为 `第1个model`。
- `中文 UHPC 中文` 应改为 `中文UHPC中文`。
- `中文 400mm 中文` 应改为 `中文400mm中文`。
- `400 mm 甚至` 应改为 `400mm甚至`。
- `51.6 m 高` 应改为 `51.6m高`。
- `1500 × 400 × 3000 mm` 应改为 `1500×400×3000mm`。
- `每排 8 根`、`图 1 所示`、`表 6 累计耗能` 应改为 `每排8根`、`图1所示`、`表6累计耗能`。
- 检查报告包含 `cjk_alnum_spacing_issue_count`、`cjk_latin_spacing_issue_count` 和示例。
- 只有在确认配置启用 `normalize_cjk_latin_spacing` 时，格式化脚本才自动删除这些空格。
- 只有不含公式、图片或绘图对象的段落，才允许跨 Word run 做整段空格清理。

公式保护规则：

- 修改前后检查公式节点或公式 XML 哈希。
- 如果公式或图片数量异常，必须中止保存。
- 不得改变正文文本内容，除非用户确认启用混排空格规范化。
- 空格清理不得重写公式 XML。
- `remove_unused_styles=true` 时默认删除未使用自定义样式；保留 Word 内置样式、正在使用的样式和配置中声明的样式。

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
- 删除的未使用自定义样式

## 目录结构

```text
.claude-plugin/
skills/
  research-workflow/
  article-rag-chunking/
  source-role-policy/
  query-planner/
  hybrid-retrieval/
  section-writing-router/
  claim-evidence-checker/
  citation-registry/
  word-formatting/
scripts/
requirements.txt
environment.yml
request.txt
README.md
README.zh-CN.md
```
