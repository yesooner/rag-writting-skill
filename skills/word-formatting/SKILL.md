---
name: word-formatting
description: Configure, inspect, and apply user-confirmed Word .docx formatting. Use when Claude Code needs to format Word documents from a flexible style table, create document styles, wrap figures and captions into tables, superscript in-text citations, preserve formulas, or audit .docx formatting without relying on project-specific manuscript rules.
---

# Word Formatting

## Required Behavior

Before modifying any `.docx`, show the user a formatting form and wait for confirmation. Do not apply built-in manuscript-specific defaults without user confirmation.

The form must be editable and should include at least these columns:

```markdown
| Part | Style name | Chinese font | English font | Size pt | Bold | Alignment | Line spacing | Space before pt | Space after pt | First-line indent | Notes |
|---|---|---|---|---:|---|---|---:|---:|---:|---|---|
| Body | Body | SimSun | Times New Roman | 12 | No | Justify | 1.5 | 0 | 0 | 2 chars | Main paragraphs |
| Heading 1 | H1 | SimHei | Times New Roman | 14 | Yes | Left | 1.5 | 0 | 0 | None | Top-level sections |
| Figure caption | Figure Caption | SimSun | Times New Roman | 10.5 | Yes | Center | 1.0 | 0 | 0 | None | Caption below figure |
```

After the user confirms, convert the confirmed form to a JSON config and run `scripts/format_docx.py --config <config.json>`.

## Scripts

Use a user-selected Python environment with the dependencies from `requirements.txt`:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
& <python> -X utf8 <script> ...
```

Generate a configurable template:

```powershell
& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\word-formatting\scripts\format_docx.py `
  --write-template "<config.json>"
```

Format after confirmation:

```powershell
& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\word-formatting\scripts\format_docx.py `
  --docx "<target.docx>" --config "<confirmed-config.json>"
```

Inspect without modifying:

```powershell
& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\word-formatting\scripts\inspect_docx.py `
  --docx "<target.docx>" --config "<confirmed-config.json>"
```

Do not install dependencies into conda `base` unless the user explicitly chooses to do so. Prefer an isolated environment and pass it as `<python>`.

## Config Model

Read `references/word-format-rules.md` before changing the config schema or script behavior.

The config controls:

- page setup
- header/footer
- style names and typography
- Office style metadata
- paragraph classification patterns
- figure wrapping
- figure table image sizing
- Word caption fields
- table formatting
- citation superscripting
- formula protection
- formula output format
- CJK-alphanumeric spacing normalization
- unused custom style removal

No style name is hardcoded as a project-specific requirement. Style names are whatever the confirmed config says.

The default page margins are:

```text
top 2.5 cm
bottom 2.5 cm
left 3.0 cm
right 2.5 cm
```

## Office Style Metadata

Every configured paragraph style must explicitly define typography and Office style metadata.

Required typography fields:

```text
size_pt
line_spacing
alignment
```

Required Office metadata fields:

```text
q_format
ui_priority
keep_next
keep_lines
```

Heading styles must also define outline levels:

```text
h1 outline_level=0
h2 outline_level=1
h3 outline_level=2
```

The formatter must write these values into Word style XML:

```text
w:qFormat
w:uiPriority
w:pPr/w:outlineLvl
w:pPr/w:keepNext
w:pPr/w:keepLines
```

The formatting and inspection reports must include `style_office_metadata_issues`. A clean document should report an empty list.

## CJK-Alphanumeric Spacing

For Chinese-English and Chinese-number mixed text, do not add spaces between CJK characters and Latin letters or Arabic digits.

Examples:

```text
Wrong: CJK_char love CJK_char
Right: CJK_charloveCJK_char

Wrong: CJK_char 1 CJK_char model
Right: CJK_char1CJK_charmodel

Wrong: CJK_char UHPC CJK_char
Right: CJK_charUHPCCJK_char

Wrong: CJK_char 400mm CJK_char
Right: CJK_char400mmCJK_char

Wrong: CJK_char 400 mm CJK_char
Right: CJK_char400mmCJK_char

Wrong: 51.6 m CJK_char
Right: 51.6mCJK_char

Wrong: 1500 × 400 × 3000 mm
Right: 1500×400×3000mm

Wrong: CJK_char 8 CJK_char
Right: CJK_char8CJK_char

Wrong: CJK_char 1 CJK_char
Right: CJK_char1CJK_char
```

The formatter must treat spaces matching this pattern as formatting defects:

```text
CJK + spaces + Latin letter/digit
Latin letter/digit + spaces + CJK
```

This includes technical abbreviations and model names such as `UHPC`, `UHPC-NC`, `RC`, `UJ-1`, `RAW`, `CDP`, `ABAQUS`, and `Cohesive` when they touch Chinese prose. It also includes compact number-unit tokens and dimension expressions when they touch Chinese prose, such as `400mm`, `51.6m`, `40MPa`, and `1500×400×3000mm`. In Chinese body text, remove redundant spaces in expressions such as `400 mm even`, `51.6 m high`, `each row 8 bars`, `Figure 1 shows`, and `Table 6 cumulative energy dissipation`.

Inspection must report both the new generic fields and the legacy compatibility fields:

```text
cjk_alnum_spacing_issue_count
cjk_alnum_spacing_examples
cjk_latin_spacing_issue_count
cjk_latin_spacing_examples
```

Formatting may remove these spaces only when the confirmed config enables:

```json
{
  "features": {
    "normalize_cjk_latin_spacing": true
  }
}
```

When this feature is enabled, the script may remove spaces inside the same Word run. If a spacing issue spans multiple runs and cannot be safely normalized without damaging formatting, report it for manual review instead of silently rewriting the paragraph.

The formatter may normalize text across multiple Word runs only when the paragraph contains no formulas, drawings, or pictures. Paragraphs containing formulas or images must be skipped for spacing rewrite so formula XML and image anchors remain unchanged.

## Unused Styles

When the confirmed config enables:

```json
{
  "features": {
    "remove_unused_styles": true
  }
}
```

delete unused custom styles after formatting. Do not delete Word built-in styles, currently used styles, or configured styles required by the confirmed style table.

## Formula Output

The required formula output format is `MathML`.

Use this config shape:

```json
{
  "formula": {
    "output_format": "MathML",
    "parameter_output_format": "MathML",
    "body_parameter_output_format": "MathML"
  }
}
```

For `.docx` formatting, do not convert or rewrite Word's internal OMML formula XML in place. Treat MathML as the required formula format for exported formula content, formula parameter descriptions, inline parameters in body paragraphs, downstream article artifacts, QA reports, and handoff descriptions.

The formatting and inspection reports must include:

```text
formula_output_format: MathML
formula_parameter_output_format: MathML
body_parameter_output_format: MathML
```

## Format Self-Check System

Before changing a `.docx`, inspect and report the current state. After changing a `.docx`, inspect again and compare.

Required checks:

```text
style completeness
Office style metadata issues
paragraph classification coverage
image count
figure-table count
figure-table image widths
caption SEQ field counts
top-level loose image paragraph count
regular table count
formula node count
formula output format
formula parameter output format
body parameter output format
formula XML/hash status
body citation count
body citation superscript count
body citation unsuperscript examples
reference-list number count
reference-list number superscript count
CJK-Alphanumeric Spacing issue count
CJK-Alphanumeric Spacing examples
unused custom styles removed
```

Figure and caption checks:

- Figures may be wrapped in a one-column, two-row table only after user confirmation.
- Row 1 contains the image.
- Row 2 contains the caption.
- Caption style, font, size, alignment, and spacing must come from the confirmed style table.
- Figure and table captions must be real Word caption fields when `captions.use_word_caption_fields=true`.
- Figure numbers must use `SEQ Figure \* ARABIC`.
- Table numbers must use `SEQ Table \* ARABIC`.
- Preserve the visible caption text while replacing the manual number with the `SEQ` field.
- Skip captions that already contain `SEQ` fields.
- After inserting, deleting, or moving figures or tables, users must update fields in Word/WPS to refresh linked caption numbers.
- Images in figure tables must use a consistent configured width.
- The default figure-table image width is `7.7 cm`.
- Preserve aspect ratio by default. Do not force a fixed height unless the user explicitly confirms distortion or cropping is acceptable.
- The formatting and inspection reports must include `figure_table_image_widths_cm`.

Table checks:

- Table captions and table body text must use the confirmed styles.
- Table body font size and alignment must be checked.
- Header-row bolding or other table conventions must be controlled by config.

Style metadata checks:

- `qFormat` must be present according to the confirmed config.
- `uiPriority` must match the confirmed config.
- Heading outline levels must be `0/1/2` for H1/H2/H3.
- `keepNext` and `keepLines` must match the confirmed config.
- Size, line spacing, and alignment must be explicit in every configured style.

Formula checks:

- Inline and display formulas must remain complete.
- Formula output format must be reported as `MathML`.
- Formula parameter descriptions and inline parameters in body paragraphs must be reported as `MathML` output.
- Formula XML/hash must be checked before and after formatting when `protect_formulas=true`.
- Abort rather than save if formula XML changes unexpectedly.
- Spacing cleanup must not rewrite formula XML.

Citation checks:

- In-text markers such as `[3]` may be superscripted by config.
- Reference-list labels such as `[3]` must not be superscripted unless the confirmed config explicitly enables it.
- Report both body citation superscripts and reference-list superscripts.

## Safety Rules

- Back up the `.docx` before every write.
- Do not change manuscript text content except user-confirmed CJK-alphanumeric spacing normalization.
- Preserve image count.
- Preserve formula XML hashes.
- Abort rather than save if formulas or images are corrupted.
- Do not superscript reference-list labels unless the confirmed config explicitly asks for it.
- Remove unused custom styles by default only when `remove_unused_styles=true`.

## Final Report

After formatting or inspection, report:

- target path
- backup path when formatting
- style completeness
- Office style metadata issues
- image count
- figure-table count
- figure-table image widths
- caption SEQ field counts
- top-level loose image paragraph count
- in-text citation count and superscript count
- reference-list number superscript count
- formula node count and hash status
- formula output format
- formula parameter output format
- body parameter output format
- regular table count
- CJK-Alphanumeric Spacing issue count and examples
- CJK-alphanumeric spaces removed, when normalization is enabled
- unused custom styles removed


