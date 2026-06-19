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
    "normalize_cjk_latin_spacing": true
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
      "first_line_indent_pt": 24
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

## Figures

If `features.wrap_figures` is true, a valid figure block is a one-column, two-row, borderless table:

1. First row: embedded figure paragraph.
2. Second row: figure caption paragraph.
3. Caption style comes from `styles.figure_caption`.
4. Cell margins are zero.
5. Borders are nil.

Caption detection must use the confirmed `patterns.figure_caption`. Do not assume that every `Figure <number>` sentence is a caption; the default English pattern excludes `Figure 1 shows ...`.

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

## CJK-Latin Spacing

If `features.normalize_cjk_latin_spacing` is true, remove spaces between CJK characters and Latin letters or digits.

Examples:

```text
Wrong: 我 love 你
Right: 我love你

Wrong: 第 1 个 model
Right: 第1个model
```

The formatter should remove only this pattern:

```text
CJK + spaces + Latin/digit
Latin/digit + spaces + CJK
```

Do not remove spaces between Latin words.

The inspection report must include:

```text
cjk_latin_spacing_issue_count
cjk_latin_spacing_examples
```

The formatting report must include:

```text
cjk_latin_spaces_removed
```

## Formula Protection

If `features.protect_formulas` is true, compare pre/post hashes of all `m:oMath` and `m:oMathPara` nodes. If the count or hash sequence changes, abort before saving.

Do not rewrite formula XML.
