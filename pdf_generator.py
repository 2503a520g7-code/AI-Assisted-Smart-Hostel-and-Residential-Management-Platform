"""
pdf_generator.py - Generates official PDF documents using ReportLab for AIAC.
Produces:
1. Student Digital Outpass PDF
2. Hostel / Dhobi Fee Payment Receipt PDF
"""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_outpass_pdf(outpass_data: dict, student_data: dict) -> io.BytesIO:
    """Generate a high-resolution, professional Outpass PDF document."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#4F46E5')     # Indigo
    dark_color = colors.HexColor('#1E1B4B')        # Deep purple/navy
    accent_green = colors.HexColor('#059669')      # Emerald green
    light_bg = colors.HexColor('#F5F3FF')          # Light purple-gray

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=dark_color,
        alignment=TA_CENTER
    )

    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_green,
        alignment=TA_CENTER
    )

    label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4B5563')
    )

    val_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#111827')
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("AIAC RESIDENTIAL MANAGEMENT PLATFORM", sub_style))
    elements.append(Paragraph("OFFICIAL STUDENT OUTPASS PERMIT", title_style))
    elements.append(Paragraph("Gate Pass & Electronic Movement Authorization", sub_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=4, spaceAfter=14))

    # 2. Reference & Status Bar
    outpass_ref = outpass_data.get('outpass_ref', 'OUT-UNKNOWN')
    verify_code = outpass_data.get('verification_code', 'VERIF-000')
    issued_at = outpass_data.get('issued_datetime', 'N/A')

    ref_table_data = [
        [
            Paragraph(f"<b>Outpass Reference:</b> {outpass_ref}", val_style),
            Paragraph("STATUS: <b>AUTHORIZED & APPROVED</b>", badge_style),
            Paragraph(f"<b>Issued Date:</b> {issued_at[:16] if issued_at else 'N/A'}", val_style)
        ]
    ]
    ref_table = Table(ref_table_data, colWidths=[2.5 * inch, 2.8 * inch, 2.2 * inch])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, primary_color),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    elements.append(ref_table)
    elements.append(Spacer(1, 14))

    # 3. Student Details Table
    student_name = student_data.get('name', 'Student')
    student_email = student_data.get('email', 'N/A')
    block = student_data.get('hostel_block', 'Hostel Block')
    room_num = student_data.get('room_number') or 'Unassigned'
    academic_yr = student_data.get('academic_year', 'N/A')

    student_details = [
        [Paragraph("<b>Student Name</b>", label_style), Paragraph(str(student_name), val_style),
         Paragraph("<b>Hostel Block</b>", label_style), Paragraph(str(block), val_style)],
        [Paragraph("<b>College Email</b>", label_style), Paragraph(str(student_email), val_style),
         Paragraph("<b>Room Number</b>", label_style), Paragraph(str(room_num), val_style)],
        [Paragraph("<b>Academic Year</b>", label_style), Paragraph(str(academic_yr), val_style),
         Paragraph("<b>Verification Token</b>", label_style), Paragraph(f"<code>{verify_code}</code>", val_style)],
    ]
    st_table = Table(student_details, colWidths=[1.8 * inch, 2.2 * inch, 1.8 * inch, 1.7 * inch])
    st_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F9FAFB')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(st_table)
    elements.append(Spacer(1, 14))

    # 4. Movement & Leave Details
    leave_type = outpass_data.get('leave_type', 'One-day outing')
    dept_time = outpass_data.get('departure_datetime', 'N/A')
    ret_time = outpass_data.get('expected_return_datetime', 'N/A')
    destination = outpass_data.get('destination', 'N/A')
    reason = outpass_data.get('reason', 'N/A')
    contact = outpass_data.get('emergency_contact', 'N/A')
    warden_name = outpass_data.get('warden_name', 'Hostel Authority')
    decision_note = outpass_data.get('decision_note', 'Approved in accordance with hostel regulations.')

    leave_details = [
        [Paragraph("<b>Leave Category</b>", label_style), Paragraph(str(leave_type), val_style)],
        [Paragraph("<b>Scheduled Departure</b>", label_style), Paragraph(str(dept_time), val_style)],
        [Paragraph("<b>Expected Return Time</b>", label_style), Paragraph(f"<b>{ret_time}</b> (Strict Curfew Applies)", val_style)],
        [Paragraph("<b>Destination</b>", label_style), Paragraph(str(destination), val_style)],
        [Paragraph("<b>Reason / Purpose</b>", label_style), Paragraph(str(reason), val_style)],
        [Paragraph("<b>Emergency Contact</b>", label_style), Paragraph(str(contact), val_style)],
        [Paragraph("<b>Approving Warden</b>", label_style), Paragraph(str(warden_name), val_style)],
        [Paragraph("<b>Warden Remark / Note</b>", label_style), Paragraph(str(decision_note), val_style)],
    ]
    lv_table = Table(leave_details, colWidths=[2.2 * inch, 5.3 * inch])
    lv_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(lv_table)
    elements.append(Spacer(1, 20))

    # 5. Security Checkpoint Signatures Table
    sig_data = [
        [
            Paragraph("<b>Security Departure Stamp</b><br/><br/><br/>Sign & Time: _________________", sub_style),
            Paragraph("<b>Security Return Stamp</b><br/><br/><br/>Sign & Time: _________________", sub_style),
            Paragraph(f"<b>Authorized Digital Seal</b><br/><br/>AIAC System Verified<br/>{warden_name}", sub_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#9CA3AF')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 14))

    # 6. Important Notice
    notice_text = (
        "<b>Important Hostel Regulation:</b> This digital outpass is valid only for the specified date and timeframe. "
        "Residents must present this pass upon exit and re-entry at the main hostel security gate. "
        "Any delay beyond the approved return time is subject to disciplinary hostel protocol."
    )
    elements.append(Paragraph(notice_text, sub_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_receipt_pdf(payment_data: dict, student_data: dict, fee_record: dict, fee_type: str = 'hostel') -> io.BytesIO:
    """Generate an official Payment Receipt PDF for Hostel or Dhobi Fee."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#4F46E5')     # Indigo
    dark_color = colors.HexColor('#1E1B4B')        # Deep purple/navy
    accent_green = colors.HexColor('#059669')      # Emerald
    border_color = colors.HexColor('#E5E7EB')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=dark_color,
        alignment=TA_CENTER
    )

    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER
    )

    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4B5563')
    )

    val_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#111827')
    )

    right_val = ParagraphStyle(
        'RightVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#111827'),
        alignment=TA_RIGHT
    )

    elements = []

    # 1. Header
    fee_title = "HOSTEL ACCOMMODATION FEE" if fee_type == 'hostel' else "DHOBI & LAUNDRY SERVICE FEE"
    elements.append(Paragraph("AIAC RESIDENTIAL MANAGEMENT PLATFORM", sub_style))
    elements.append(Paragraph(f"OFFICIAL {fee_title} RECEIPT", title_style))
    elements.append(Paragraph("Electronic Payment Acknowledgment & Verified Transaction Voucher", sub_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=4, spaceAfter=14))

    # 2. Transaction Summary Header
    txn_ref = payment_data.get('transaction_ref', 'TXN-UNKNOWN')
    txn_date = payment_data.get('created_at', 'N/A')
    pay_method = payment_data.get('payment_method', 'Demo Online Payment')

    banner_data = [
        [
            Paragraph(f"<b>Transaction Reference:</b><br/>{txn_ref}", val_style),
            Paragraph(f"<b>Date & Time:</b><br/>{txn_date[:19] if txn_date else 'N/A'}", val_style),
            Paragraph("<b>Status:</b><br/><font color='#059669'><b>PAID & CONFIRMED</b></font>", val_style),
            Paragraph(f"<b>Payment Mode:</b><br/>{pay_method}", val_style)
        ]
    ]
    banner_table = Table(banner_data, colWidths=[2.1 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F3FF')),
        ('BOX', (0, 0), (-1, -1), 1, primary_color),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 14))

    # 3. Student / Billed To Section
    student_name = student_data.get('name', 'Student')
    student_email = student_data.get('email', 'N/A')
    block = student_data.get('hostel_block', 'N/A')
    room_num = student_data.get('room_number') or 'Unassigned'
    academic_term = fee_record.get('academic_term') or fee_record.get('month_year') or 'Current Term'

    student_data_matrix = [
        [Paragraph("<b>Billed Student Name</b>", label_style), Paragraph(str(student_name), val_style),
         Paragraph("<b>Billing Cycle / Term</b>", label_style), Paragraph(str(academic_term), val_style)],
        [Paragraph("<b>Student College Email</b>", label_style), Paragraph(str(student_email), val_style),
         Paragraph("<b>Hostel Block & Room</b>", label_style), Paragraph(f"{block} / Room {room_num}", val_style)],
    ]
    st_table = Table(student_data_matrix, colWidths=[1.8 * inch, 2.2 * inch, 1.8 * inch, 1.7 * inch])
    st_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F9FAFB')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(st_table)
    elements.append(Spacer(1, 18))

    # 4. Itemized Ledger Table
    amount_paid_now = payment_data.get('amount', 0.0)
    total_fee = fee_record.get('total_amount', amount_paid_now)
    total_paid_cum = fee_record.get('amount_paid', amount_paid_now)
    balance_due = max(0.0, total_fee - total_paid_cum)

    item_desc = "Hostel Accommodation, Electricity & Maintenance Charges" if fee_type == 'hostel' else "Dhobi & Laundry Monthly Service Subscription"

    items_data = [
        [Paragraph("<b>Description / Particulars</b>", label_style), Paragraph("<b>Term / Cycle</b>", label_style), Paragraph("<b>Amount (INR)</b>", right_val)],
        [Paragraph(item_desc, val_style), Paragraph(str(academic_term), val_style), Paragraph(f"₹ {total_fee:,.2f}", right_val)],
        [Paragraph("<b>Amount Paid in this Transaction</b>", label_style), Paragraph("", val_style), Paragraph(f"<font color='#059669'>₹ {amount_paid_now:,.2f}</font>", right_val)],
        [Paragraph("Total Cumulative Amount Paid", label_style), Paragraph("", val_style), Paragraph(f"₹ {total_paid_cum:,.2f}", right_val)],
        [Paragraph("<b>Outstanding Balance Due</b>", label_style), Paragraph("", val_style), Paragraph(f"<b>₹ {balance_due:,.2f}</b>", right_val)],
    ]
    it_table = Table(items_data, colWidths=[4.2 * inch, 1.8 * inch, 1.5 * inch])
    it_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2F6')),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#ECFDF5')),  # Light green highlight for paid amount
    ]))
    elements.append(it_table)
    elements.append(Spacer(1, 24))

    # 5. Signatures and Verification
    audit_data = [
        [
            Paragraph("<b>Automated System Verification</b><br/><br/>This is a digitally generated receipt issued by the AIAC Residential Accounting System.<br/>No manual signature required.", sub_style),
            Paragraph("<b>Hostel Accounts Desk</b><br/><br/><br/>Authorized Accounts Officer<br/>AIAC Residential Office", sub_style)
        ]
    ]
    audit_table = Table(audit_data, colWidths=[4.8 * inch, 2.7 * inch])
    audit_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(audit_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph(
        "<i>For any discrepancies regarding fee records or payments, contact the Hostel Accounts Office or submit an inquiry through the Complaints section.</i>",
        sub_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
