import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

# Create a new workbook and select the active worksheet
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Age Data"

# Define column headers
headers = ["Age", "Image Filename"]

# Add headers with formatting
header_font = Font(bold=True, size=12)
header_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
header_alignment = Alignment(horizontal="center", vertical="center")

for col_num, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col_num, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_alignment

# Set column widths
ws.column_dimensions["A"].width = 15
ws.column_dimensions["B"].width = 30

# Add a few empty rows for data
for row in range(2, 12):
    ws.cell(row=row, column=1)
    ws.cell(row=row, column=2)

# Save the workbook
wb.save("template.xlsx")
print("Excel template created: template.xlsx") 