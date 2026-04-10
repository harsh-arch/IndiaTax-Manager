# utils.py
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from decimal import Decimal

def format_money(value):
    """Helper to format Decimal to currency string for PDF"""
    if isinstance(value, Decimal):
         # Use standard string formatting for consistency
         return "${:,.2f}".format(value)
    try:
        # Try converting potential floats/strings if needed, be cautious
        dec_value = Decimal(str(value))
        return "${:,.2f}".format(dec_value)
    except:
        return str(value) # Fallback

def generate_summary_pdf(summary_data):
    """Generates a PDF summary report using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Tax Summary Report - {summary_data.get('year', 'N/A')}", styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    # Basic Info
    story.append(Paragraph(f"Filing Status: {summary_data.get('filing_status', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Summary Table Data
    summary_table_data = [
        ['Description', 'Amount'],
        ['Gross Income', format_money(summary_data.get('gross_income'))],
        ['Itemized Deductions (Calculated)', format_money(summary_data.get('itemized_deductions'))],
        ['Standard Deduction', format_money(summary_data.get('standard_deduction'))],
        ['Deduction Taken', format_money(summary_data.get('chosen_deduction'))],
        ['Taxable Income', format_money(summary_data.get('taxable_income'))],
        ['Calculated Tax (Before Credits)', format_money(summary_data.get('calculated_tax'))],
        ['Total Tax Credits Applied', f"- {format_money(summary_data.get('total_credits'))}"],
        ['Final Tax Liability', format_money(summary_data.get('final_tax_liability'))]
    ]

    # Summary Table Style
    summary_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Header row background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'), # Align amounts right
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Bold final liability
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
         ('BACKGROUND', (0, -1), (-1,-1), colors.lightgrey),
    ])

    # Create and style summary table
    summary_table = Table(summary_table_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(summary_table_style)
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # Tax Breakdown Table
    story.append(Paragraph("Tax Bracket Breakdown", styles['h2']))
    story.append(Spacer(1, 0.1*inch))

    breakdown_data = [['Income Up To', 'Rate', 'Taxable Amount', 'Tax Paid']]
    if summary_data.get('tax_breakdown'):
        for item in summary_data['tax_breakdown']:
             limit = item.get('limit', 'N/A')
             if limit == 'Infinity': limit = 'Above Last'
             breakdown_data.append([
                 limit,
                 item.get('rate', 'N/A'),
                 format_money(item.get('taxable_amount')),
                 format_money(item.get('tax_paid'))
             ])
    else:
         breakdown_data.append(['N/A', 'N/A', 'N/A', 'N/A'])


    breakdown_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Align amounts right
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    breakdown_table = Table(breakdown_data, colWidths=[1.5*inch, 1*inch, 1.75*inch, 1.75*inch])
    breakdown_table.setStyle(breakdown_table_style)
    story.append(breakdown_table)
    story.append(Spacer(1, 0.3*inch))

    # Disclaimer
    story.append(Paragraph("<para align=center><font size=9><i>Disclaimer: Educational purposes only. Consult a tax professional.</i></font></para>", styles['Normal']))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer