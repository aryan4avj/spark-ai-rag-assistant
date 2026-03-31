from pathlib import Path
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "project_learning_guide.md"
OUTPUT = ROOT / "docs" / "project_learning_guide.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="GuideTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#16324f"),
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f3d5e"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#235789"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideBullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            leftIndent=16,
            firstLineIndent=-10,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GuideCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.8,
            leading=11,
            backColor=colors.HexColor("#f4f6f8"),
            borderPadding=6,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=6,
        )
    )
    return styles


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_story(lines, styles):
    story = []
    in_code = False
    code_buffer = []

    def flush_code():
        nonlocal code_buffer
        if not code_buffer:
            return
        code_text = "<br/>".join(escape(line) for line in code_buffer)
        story.append(Paragraph(code_text, styles["GuideCode"]))
        code_buffer = []

    title_used = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        if line.startswith("```"):
            in_code = not in_code
            if not in_code:
                flush_code()
            continue

        if in_code:
            code_buffer.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.08 * inch))
            continue

        if stripped.startswith("# "):
            if not title_used:
                story.append(Paragraph(escape(stripped[2:]), styles["GuideTitle"]))
                title_used = True
            else:
                story.append(PageBreak())
                story.append(Paragraph(escape(stripped[2:]), styles["GuideH1"]))
            continue

        if stripped.startswith("## "):
            story.append(Paragraph(escape(stripped[3:]), styles["GuideH1"]))
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(escape(stripped[4:]), styles["GuideH2"]))
            continue

        if stripped.startswith("- "):
            story.append(Paragraph(escape("• " + stripped[2:]), styles["GuideBullet"]))
            continue

        if stripped.startswith(("1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ")):
            story.append(Paragraph(escape(stripped), styles["GuideBullet"]))
            continue

        wrapped = "<br/>".join(
            escape(part)
            for part in textwrap.wrap(stripped, width=110, break_long_words=False, break_on_hyphens=False)
        ) or escape(stripped)
        story.append(Paragraph(wrapped, styles["GuideBody"]))

    flush_code()
    return story


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(doc.pagesize[0] - 40, 20, f"Page {doc.page}")
    canvas.restoreState()


def main():
    styles = build_styles()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = build_story(lines, styles)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=36,
        title="Spark AI RAG Assistant Learning Guide",
        author="OpenAI Codex",
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Created PDF: {OUTPUT}")


if __name__ == "__main__":
    main()
