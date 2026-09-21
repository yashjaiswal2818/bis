import io
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportService:
    @staticmethod
    def generate_audit_pdf(audit_result: dict, filename: str = "Tender_Audit") -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], textColor=colors.HexColor("#1e3a8a"), fontSize=18, spaceAfter=12)
        h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], textColor=colors.HexColor("#1e3a8a"), fontSize=14, spaceAfter=10)
        normal_style = styles['Normal']
        
        elements.append(Paragraph(f"Procurement Standards Audit Report", title_style))
        elements.append(Paragraph(f"Document: {filename}", h2_style))
        elements.append(Spacer(1, 12))
        
        summary_msg = audit_result.get("summary_message", "No summary available")
        overall = audit_result.get("overall_verdict", "Unknown")
        elements.append(Paragraph(f"<b>Overall Verdict:</b> {overall}", normal_style))
        elements.append(Paragraph(f"<b>Summary:</b> {summary_msg}", normal_style))
        elements.append(Spacer(1, 20))
        
        items = audit_result.get("items_audited", audit_result.get("clauses_analyzed", []))
        
        if not items:
            elements.append(Paragraph("No items found or assessed in this document.", normal_style))
        else:
            table_data = [["#", "Item/Clause", "Status", "Recommended Standards", "Action/Notes"]]
            for idx, item in enumerate(items, 1):
                desc = item.get("item_description", item.get("clause_text", ""))
                cv = item.get("compliance_verdict", {})
                status = cv.get("audit_status", "UNKNOWN")
                notes = cv.get("audit_status_reason", "")
                
                recs = []
                for rec in item.get("recommended_standards", []):
                    code = rec.get("is_code", "")
                    title = rec.get("title", "")
                    recs.append(f"{code}: {title}")
                recs_str = "\n\n".join(recs) if recs else "None"
                
                table_data.append([
                    str(idx),
                    Paragraph(desc, normal_style),
                    status,
                    Paragraph(recs_str, normal_style),
                    Paragraph(notes, normal_style)
                ])
                
            t = Table(table_data, colWidths=[30, 200, 100, 200, 200], repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            elements.append(t)
            
        elements.append(Spacer(1, 30))
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"<i>Report generated securely & offline by BIS Agentic Workbench on {timestamp}</i>", normal_style))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
