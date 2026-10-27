"""Create and publish PDF documents without coupling to other modules."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from xml.sax.saxutils import escape
from telegram import Bot


def create_pdf(text: str, title: str = "Special Education Needs") -> BytesIO:
    if not text.strip():
        raise ValueError("Document text is empty.")
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 8 * mm)]
    for block in text.strip().split("\n"):
        if block.strip():
            story.append(Paragraph(escape(block.strip()), styles["BodyText"]))
            story.append(Spacer(1, 3 * mm))
    doc.build(story)
    output.seek(0)
    output.name = "special_education_notes.pdf"
    return output


async def publish_pdf(bot: Bot, channel_id: str, text: str) -> None:
    pdf = create_pdf(text)
    await bot.send_document(
        chat_id=channel_id,
        document=pdf,
        caption="📄 Special Education Needs — PDF दस्तावेज़",
    )
