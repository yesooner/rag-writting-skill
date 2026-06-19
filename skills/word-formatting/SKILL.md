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
- paragraph classification patterns
- figure wrapping
- table formatting
- citation superscripting
- formula protection
- CJK-Latin spacing normalization

No style name is hardcoded as a project-specific requirement. Style names are whatever the confirmed config says.

## CJK-Latin Spacing

For Chinese-English mixed text, do not add spaces between CJK characters and Latin letters or digits.

Examples:

```text
Wrong: 我 love 你
Right: 我love你

Wrong: 第 1 个 model
Right: 第1个model
```

The formatter must treat spaces matching this pattern as formatting defects:

```text
CJK + spaces + Latin/digit
Latin/digit + spaces + CJK
```

Inspection must report:

```text
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

## Format Self-Check System

Before changing a `.docx`, inspect and report the current state. After changing a `.docx`, inspect again and compare.

Required checks:

```text
style completeness
paragraph classification coverage
image count
figure-table count
top-level loose image paragraph count
regular table count
formula node count
formula XML/hash status
body citation count
body citation superscript count
body citation unsuperscript examples
reference-list number count
reference-list number superscript count
CJK-Latin spacing issue count
CJK-Latin spacing examples
```

Figure and caption checks:

- Figures may be wrapped in a one-column, two-row table only after user confirmation.
- Row 1 contains the image.
- Row 2 contains the caption.
- Caption style, font, size, alignment, and spacing must come from the confirmed style table.

Table checks:

- Table captions and table body text must use the confirmed styles.
- Table body font size and alignment must be checked.
- Header-row bolding or other table conventions must be controlled by config.

Formula checks:

- Inline and display formulas must remain complete.
- Formula XML/hash must be checked before and after formatting when `protect_formulas=true`.
- Abort rather than save if formula XML changes unexpectedly.

Citation checks:

- In-text markers such as `[3]` may be superscripted by config.
- Reference-list labels such as `[3]` must not be superscripted unless the confirmed config explicitly enables it.
- Report both body citation superscripts and reference-list superscripts.

## Safety Rules

- Back up the `.docx` before every write.
- Do not change manuscript text content except user-confirmed CJK-Latin spacing normalization.
- Preserve image count.
- Preserve formula XML hashes.
- Abort rather than save if formulas or images are corrupted.
- Do not superscript reference-list labels unless the confirmed config explicitly asks for it.

## Final Report

After formatting or inspection, report:

- target path
- backup path when formatting
- style completeness
- image count
- figure-table count
- top-level loose image paragraph count
- in-text citation count and superscript count
- reference-list number superscript count
- formula node count and hash status
- regular table count
- CJK-Latin spacing issue count and examples
- CJK-Latin spaces removed, when normalization is enabled

