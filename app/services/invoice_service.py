from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def build_invoice_pdf(order):
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    pdf.setTitle(f"Invoice {order.invoice.invoice_number}")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, "LUMIÈRE JEWELS")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 782, f"Invoice: {order.invoice.invoice_number}")
    pdf.drawString(50, 768, f"Order: {order.order_number}")
    y = 730
    for item in order.items:
        pdf.drawString(50, y, f"{item.product_name} x {item.quantity}")
        pdf.drawRightString(540, y, f"₹{float(item.unit_price) * item.quantity:.2f}")
        y -= 20
    y -= 10
    pdf.drawString(50, y, f"Subtotal: ₹{float(order.subtotal):.2f}")
    y -= 18
    pdf.drawString(50, y, f"Making Charges: ₹{float(order.making_charges):.2f}")
    y -= 18
    pdf.drawString(50, y, f"GST: ₹{float(order.gst):.2f}")
    y -= 24
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"Grand Total: ₹{float(order.total_amount):.2f}")
    pdf.save()
    stream.seek(0)
    return stream
