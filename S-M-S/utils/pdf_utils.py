import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


def generate_tc_pdf(student_row, completion_date: str, base_dir: str) -> str:
    """Generate TC PDF and return relative path from base_dir."""
    tc_dir = os.path.join(base_dir, 'static', 'tc')
    os.makedirs(tc_dir, exist_ok=True)

    safe_name = f"TC_{student_row['id']}_{student_row['full_name'].replace(' ', '_')}.pdf"
    out_path = os.path.join(tc_dir, safe_name)

    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4

    margin = 36
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(margin, margin, width - 2*margin, height - 2*margin)

    c.setFont("Helvetica-Bold", 16)
    title = "GOVERNMENT POLYTECHNIC PILLARIPATTU"
    c.drawCentredString(width/2, height - margin - 20, title)

    if student_row["photo_path"]:
        try:
            photo_abs = (
                student_row["photo_path"] if os.path.isabs(student_row["photo_path"]) else
                os.path.join(base_dir, student_row["photo_path"]))
            img_reader = ImageReader(photo_abs)
            img_w, img_h = img_reader.getSize()
            max_w, max_h = 110, 130
            scale = min(max_w/img_w, max_h/img_h)
            draw_w, draw_h = img_w*scale, img_h*scale
            x = width - margin - draw_w - 10
            y = height - margin - 20 - draw_h - 10
            c.rect(x-5, y-5, draw_w+10, draw_h+10)
            c.drawImage(img_reader, x, y, draw_w, draw_h)
        except Exception:
            pass

    c.setFont("Helvetica", 11)
    y = height - margin - 70
    line_gap = 18

    def dmy(s):
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d-%m-%Y")

    lines = [
        ("Full Name", student_row["full_name"]),
        ("Branch", student_row["branch"]),
        ("Year of Joining", str(student_row["year_of_joining"])),
        ("Completion Date", dmy(completion_date)),
        ("Date of Birth", dmy(student_row["dob"])),
        ("POLYCET Rank", student_row["polycet_rank"] or "—"),
        ("Admission Based On", student_row["admission_based_on"]),
        ("Aadhaar (Student)", student_row["aadhar_student"] or "—"),
        ("Aadhaar (Parent)", student_row["aadhar_parent"] or "—"),
        ("Mobile (Student)", student_row["mobile_student"] or "—"),
        ("Mobile (Parent)", student_row["mobile_parent"] or "—"),
        ("Declaration", "This is to certify that the above particulars are true to the best of our records."),
    ]

    left_x = margin + 25
    for label, value in lines:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_x, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(left_x + 160, y, str(value))
        y -= line_gap

    c.setStrokeColor(colors.green)
    c.setFillColor(colors.green)
    tick_x, tick_y = left_x, y - 10
    c.setLineWidth(3)
    c.line(tick_x, tick_y, tick_x + 8, tick_y - 8)
    c.line(tick_x + 8, tick_y - 8, tick_x + 22, tick_y + 6)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(tick_x + 30, tick_y - 2, "Verified")

    c.setFont("Helvetica", 10)
    c.drawRightString(width - margin - 10, margin + 40, "(Authorized Signatory)")
    c.line(width - margin - 150, margin + 55, width - margin - 10, margin + 55)

    c.showPage()
    c.save()

    return os.path.relpath(out_path, base_dir).replace("\\", "/")
