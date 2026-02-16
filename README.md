# Structural Engineering Helper

This repository now includes a Python program that automatically draws an RC column cross-section with rebars and ties from Excel inputs.

## File
- `draw_column_section.py`

## Install dependencies
```bash
pip install pandas openpyxl matplotlib
```

## Excel input format
Create an Excel file (for example `column_input.xlsx`) with sheet name `Section` and either of the following formats.

### Format A: key/value table
| parameter   | value |
|-------------|-------|
| width_mm    | 500   |
| height_mm   | 700   |
| cover_mm    | 40    |
| bar_dia_mm  | 20    |
| tie_dia_mm  | 10    |
| n_bars_x    | 4     |
| n_bars_y    | 5     |
| output_file | section.png |

### Format B: single-row header table
| width_mm | height_mm | cover_mm | bar_dia_mm | tie_dia_mm | n_bars_x | n_bars_y | output_file |
|----------|-----------|----------|------------|------------|----------|----------|-------------|
| 500      | 700       | 40       | 20         | 10         | 4        | 5        | section.png |

## Run
```bash
python draw_column_section.py column_input.xlsx
```

Optional arguments:
- `--sheet SectionName`
- `--output your_path.png`

The generated image includes:
- Concrete boundary
- Tie centerline (dashed)
- Rebar circles automatically distributed along the perimeter
- Basic section annotation (size, bar count, diameters)
