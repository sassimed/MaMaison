from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
from datetime import datetime
import base64

# Constants for Tunisia
TVA_RATE = 0.19  # 19% TVA
TIMBRE_FISCAL = 1.0  # 1 DT timbre fiscal
CURRENCY = "DT"  # Dinar Tunisien


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """
    Generate a professional invoice PDF for Smart Life Tunisia.
    
    invoice_data should contain:
    - invoice_number: str
    - date: datetime
    - client_name: str
    - client_email: str
    - client_phone: str
    - client_address: dict (optional)
    - items: list of {product_name, quantity, unit_price, total}
    - total: float (HT)
    - status: str
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_RIGHT
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=5
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333')
    )
    
    elements = []
    
    # ==================== HEADER ====================
    company_info = f"""
    <b><font color="#7C3AED" size="16">Smart Life</font></b><br/>
    <font size="9" color="#666666">Expert en domotique et sécurité connectée</font><br/>
    <font size="9" color="#666666">Tunis, Tunisie</font><br/>
    <font size="9" color="#666666">contact@smartlife.tn</font><br/>
    <font size="9" color="#666666">+216 XX XXX XXX</font><br/>
    <font size="9" color="#666666">MF: XXXXXXX/X/X/XXX</font>
    """
    
    invoice_title = f"""
    <font color="#7C3AED" size="20"><b>FACTURE</b></font><br/>
    <font size="11" color="#666666"># {invoice_data.get('invoice_number', 'N/A')}</font>
    """
    
    header_data = [
        [Paragraph(invoice_title, styles['Normal']), Paragraph(company_info, company_style)]
    ]
    header_table = Table(header_data, colWidths=[10*cm, 7*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10*mm))
    
    # ==================== DATE & INFO ====================
    date_str = invoice_data.get('date', datetime.now()).strftime('%d/%m/%Y')
    
    info_data = [
        ['Date de facture:', date_str],
        ['Statut:', invoice_data.get('status', 'En attente')],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # ==================== CLIENT INFO ====================
    elements.append(Paragraph('Client', section_title))
    
    client_name = invoice_data.get('client_name', 'N/A')
    client_email = invoice_data.get('client_email', '')
    client_phone = invoice_data.get('client_phone', '')
    
    address_details = invoice_data.get('client_address', {})
    address_lines = []
    if address_details:
        if address_details.get('street'):
            address_lines.append(address_details['street'])
        if address_details.get('street2'):
            address_lines.append(address_details['street2'])
        postal_city = []
        if address_details.get('postal_code'):
            postal_city.append(address_details['postal_code'])
        if address_details.get('city'):
            postal_city.append(address_details['city'])
        if postal_city:
            address_lines.append(' '.join(postal_city))
        if address_details.get('country'):
            address_lines.append(address_details['country'])
    
    client_info_text = f"""
    <b>{client_name}</b><br/>
    {f'<font color="#666666">{client_email}</font><br/>' if client_email else ''}
    {f'<font color="#666666">{client_phone}</font><br/>' if client_phone else ''}
    {'<br/>'.join([f'<font color="#666666">{line}</font>' for line in address_lines])}
    """
    
    client_data = [[Paragraph(client_info_text, normal_style)]]
    client_table = Table(client_data, colWidths=[17*cm])
    client_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 8*mm))
    
    # ==================== PRODUCTS TABLE ====================
    elements.append(Paragraph('Produits', section_title))
    
    table_data = [['Description', 'Qté', 'Prix unitaire', 'Montant']]
    
    items = invoice_data.get('items', [])
    for item in items:
        table_data.append([
            item.get('product_name', 'N/A'),
            str(item.get('quantity', 1)),
            f"{item.get('unit_price', 0):.3f} {CURRENCY}",
            f"{item.get('total', 0):.3f} {CURRENCY}"
        ])
    
    products_table = Table(table_data, colWidths=[9*cm, 2*cm, 3*cm, 3*cm])
    products_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9FAFB')) 
          for i in range(2, len(table_data), 2)],
    ]))
    elements.append(products_table)
    elements.append(Spacer(1, 5*mm))
    
    # ==================== TOTALS ====================
    total_ht = invoice_data.get('total', 0)
    discount = invoice_data.get('discount', 0)  # Remise points fidélité
    total_after_discount = total_ht - discount
    tva_amount = total_after_discount * TVA_RATE
    total_ttc = total_after_discount + tva_amount + TIMBRE_FISCAL
    
    total_rows = [
        ['Total HT', f"{total_ht:.3f} {CURRENCY}"],
    ]
    
    if discount > 0:
        total_rows.append(['Remise fidélité', f"-{discount:.3f} {CURRENCY}"])
        total_rows.append(['Total après remise', f"{total_after_discount:.3f} {CURRENCY}"])
    
    total_rows.extend([
        [f'TVA ({int(TVA_RATE * 100)}%)', f"{tva_amount:.3f} {CURRENCY}"],
        ['Timbre fiscal', f"{TIMBRE_FISCAL:.3f} {CURRENCY}"],
        ['Total TTC', f"{total_ttc:.3f} {CURRENCY}"],
    ])
    
    total_table = Table(total_rows, colWidths=[12*cm, 5*cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#7C3AED')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#7C3AED')),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 15*mm))
    
    # ==================== FOOTER ====================
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    
    footer_text = f"""
    <font size="9" color="#999999">
    Smart Life - Expert en domotique et sécurité connectée<br/>
    contact@smartlife.tn | +216 XX XXX XXX | www.smartlife.tn<br/>
    Merci pour votre confiance !
    </font>
    """
    elements.append(Paragraph(footer_text, footer_style))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def invoice_to_base64(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to base64 string for storage"""
    return base64.b64encode(pdf_bytes).decode('utf-8')


def base64_to_invoice(base64_string: str) -> bytes:
    """Convert base64 string back to PDF bytes"""
    return base64.b64decode(base64_string)


def calculate_totals(subtotal: float, discount: float = 0):
    """Calculate invoice totals with TVA and fiscal stamp"""
    total_after_discount = subtotal - discount
    tva = total_after_discount * TVA_RATE
    total_ttc = total_after_discount + tva + TIMBRE_FISCAL
    return {
        "subtotal": subtotal,
        "discount": discount,
        "total_after_discount": total_after_discount,
        "tva_rate": TVA_RATE,
        "tva_amount": tva,
        "timbre_fiscal": TIMBRE_FISCAL,
        "total_ttc": total_ttc
    }
