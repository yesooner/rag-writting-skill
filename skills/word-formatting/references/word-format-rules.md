# Word Format Rules

## Confirmation Form

Always present an editable table before modifying a Word document. The user must be able to change fonts, sizes, spacing, indentation, and enabled features.

Minimum table columns:

```markdown
| Part | Style name | Chinese font | English font | Size pt | Bold | Alignment | Line spacing | Space before pt | Space after pt | First-line indent | Notes |
```

Suggested role names are generic and may be changed:

- `title`
- `subtitle`
- `abstract_head`
- `abstract_body`
- `keywords`
- `h1`
- `h2`
- `h3`
- `body`
- `figure`
- `figure_caption`
- `table_caption`
- `table_text`
- `reference`
- `formula`

## JSON Config

The confirmed form should be converted to JSON with this shape:

```json
{
  "page": {
    "width_cm": 21.0,
    "height_cm": 29.7,
    "top_cm": 2.5,
    "bottom_cm": 2.5,
    "left_cm": 3.0,
    "right_cm": 2.5,
    "header_cm": 1.5,
    "footer_cm": 1.5
  },
  "header_footer": {
    "enabled": true,
    "header_text": "document_stem",
    "page_number": true
  },
  "features": {
    "wrap_figures": true,
    "format_tables": true,
    "superscript_citations": true,
    "protect_formulas": true,
    "normalize_cjk_latin_spacing": true,
    "remove_unused_styles": true
  },
  "formula": {
    "output_format": "MathML",
    "parameter_output_format": "MathML",
    "body_parameter_output_format": "MathML"
  },
  "figures": {
    "table_image_width_cm": 7.7,
    "preserve_aspect_ratio": true
  },
  "styles": {
    "body": {
      "name": "Body",
      "font_cn": "SimSun",
      "font_en": "Times New Roman",
      "size_pt": 12,
      "bold": false,
      "alignment": "justify",
      "line_spacing": 1.5,
      "space_before_pt": 0,
      "space_after_pt": 0,
      "first_line_indent_pt": 24,
      "q_format": true,
      "ui_priority": 50,
      "outline_level": null,
      "keep_next": false,
      "keep_lines": true
    },
    "h1": {
      "name": "H1",
      "font_cn": "SimHei",
      "font_en": "Times New Roman",
      "size_pt": 14,
      "bold": true,
      "alignment": "left",
      "line_spacing": 1.5,
      "space_before_pt": 0,
      "space_after_pt": 0,
      "first_line_indent_pt": 0,
      "q_format": true,
      "ui_priority": 10,
      "outline_level": 0,
      "keep_next": true,
      "keep_lines": true
    }
  },
  "patterns": {
    "figure_caption": ["^图\\s*\\d+", "^Figure\\s+\\d+\\s+(?!shows\\b)"],
    "table_caption": ["^表\\s*\\d+", "^Table\\s+\\d+"],
    "reference": ["^\\[\\d+\\]"],
    "h1": ["^\\d+\\s+"],
    "h2": ["^\\d+\\.\\d+\\s+"],
    "h3": ["^\\d+\\.\\d+\\.\\d+\\s+"]
  }
}
```

## Office Style Metadata

Every configured paragraph style must explicitly define:

```text
size_pt
line_spacing
alignment
q_format
ui_priority
keep_next
keep_lines
```

Heading styles must also define:

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

Inspection and formatting reports must include `style_office_metadata_issues`.

## Figures

If `features.wrap_figures` is true, a valid figure block is a one-column, two-row, borderless table:

1. First row: embedded figure paragraph.
2. Second row: figure caption paragraph.
3. Caption style comes from `styles.figure_caption`.
4. Cell margins are zero.
5. Borders are nil.

Caption detection must use the confirmed `patterns.figure_caption`. Do not assume that every `Figure <number>` sentence is a caption; the default English pattern excludes `Figure 1 shows ...`.

Figure-table image sizing:

- Default `figures.table_image_width_cm` is `7.7`.
- Images in figure tables are resized to the configured width.
- Preserve aspect ratio by default with `figures.preserve_aspect_ratio=true`.
- Do not force fixed height unless the user explicitly confirms distortion or cropping is acceptable.
- Inspection and formatting reports must include `figure_table_image_widths_cm`.

## Tables

If `features.format_tables` is true:

- regular tables use `styles.table_text`
- header row is bold unless the style config says otherwise
- figure tables remain borderless
- ordinary tables use simple black academic borders by default

## Citations

If `features.superscript_citations` is true, split in-text citation markers into independent runs and set:

```xml
w:vertAlign w:val="superscript"
```

Default citation pattern:

```text
[1]
[4,5,6]
[15,18]
[25-27]
```

Do not superscript paragraphs matching `patterns.reference` or paragraphs styled with the configured reference style.

## CJK-Alphanumeric Spacing

If `features.normalize_cjk_latin_spacing` is true, remove spaces between CJK characters and Latin letters or Arabic digits.

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

The formatter should remove only this pattern:

```text
CJK + spaces + Latin letter/digit
Latin letter/digit + spaces + CJK
```

This includes technical abbreviations and model names such as `UHPC`, `UHPC-NC`, `RC`, `UJ-1`, `RAW`, `CDP`, `ABAQUS`, and `Cohesive` when they touch Chinese prose. It also includes compact number-unit tokens and dimension expressions when they touch Chinese prose, such as `400mm`, `51.6m`, `40MPa`, and `1500×400×3000mm`.

Do not remove spaces between Latin words. In Chinese body text, remove redundant spaces in number-unit and figure/table-number expressions such as `400 mm even`, `51.6 m high`, `each row 8 bars`, `Figure 1 shows`, and `Table 6 cumulative energy dissipation`.

When a spacing issue spans multiple Word runs, the formatter may rewrite the full paragraph text only if the paragraph has no formulas, drawings, or pictures.

The inspection report must include:

```text
cjk_alnum_spacing_issue_count
cjk_alnum_spacing_examples
cjk_latin_spacing_issue_count
cjk_latin_spacing_examples
```

The formatting report must include:

```text
cjk_alnum_spaces_removed
cjk_latin_spaces_removed
```

## Unused Styles

If `features.remove_unused_styles` is true, delete unused custom styles after formatting. Do not delete:

```text
Word built-in styles
styles currently used by paragraphs or tables
styles named in the confirmed config
Normal
Default Paragraph Font
Normal Table
```

## Formula Protection

If `features.protect_formulas` is true, compare pre/post hashes of all `m:oMath` and `m:oMathPara` nodes. If the count or hash sequence changes, abort before saving.

Do not rewrite formula XML. Paragraph-level spacing normalization must skip paragraphs containing formulas.

## Formula Output

Formula output format must be `MathML`.

Use:

```json
{
  "formula": {
    "output_format": "MathML",
    "parameter_output_format": "MathML",
    "body_parameter_output_format": "MathML"
  }
}
```

For `.docx` formatting, Word's internal OMML formula XML is preserved and hash-checked. MathML is the required output format for exported formula content, formula parameter descriptions, inline parameters in body paragraphs, downstream article artifacts, QA reports, and handoff descriptions.

Inspection and formatting reports must include:

```text
formula_output_format
formula_parameter_output_format
body_parameter_output_format
```

