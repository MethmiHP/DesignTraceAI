from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class ADRReportGenerator:

    def generate_project_report(
        self,
        project_id: str,
        adrs: list,
    ) -> BytesIO:

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ADRTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            "ADRHeading",
            parent=styles["Heading2"],
            spaceBefore=10,
            spaceAfter=6,
        )

        story = []

        story.append(
            Paragraph(
                "DesignTrace AI",
                title_style,
            )
        )

        story.append(
            Paragraph(
                "Architecture Decision Records Report",
                styles["Heading1"],
            )
        )

        story.append(
            Spacer(1, 8)
        )

        story.append(
            Paragraph(
                f"<b>Project ID:</b> {project_id}",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                f"<b>Total ADRs:</b> {len(adrs)}",
                styles["BodyText"],
            )
        )

        story.append(
            Spacer(1, 14)
        )

        for adr in adrs:

            story.append(
                Paragraph(
                    f"{adr.adr_id} - {adr.title}",
                    heading_style,
                )
            )

            metadata = [
                ["Status", str(adr.status)],
                [
                    "Generation Method",
                    str(adr.generation_method),
                ],
            ]

            table = Table(
                metadata,
                colWidths=[
                    45 * mm,
                    110 * mm,
                ],
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, -1),
                            colors.whitesmoke,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "PADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                    ]
                )
            )

            story.append(table)
            story.append(Spacer(1, 8))

            self._add_section(
                story,
                styles,
                "Context",
                adr.context,
            )

            self._add_section(
                story,
                styles,
                "Decision",
                adr.decision,
            )

            self._add_section(
                story,
                styles,
                "Rationale",
                adr.rationale,
            )

            self._add_list_section(
                story,
                styles,
                "Alternatives Considered",
                adr.alternatives,
            )

            self._add_list_section(
                story,
                styles,
                "Benefits",
                adr.benefits,
            )

            self._add_list_section(
                story,
                styles,
                "Risks",
                adr.risks,
            )

            self._add_list_section(
                story,
                styles,
                "Consequences",
                adr.consequences,
            )

            self._add_list_section(
                story,
                styles,
                "Trade-offs",
                adr.trade_offs,
            )

            story.append(
                Spacer(1, 16)
            )

        document.build(story)

        buffer.seek(0)

        return buffer


    def _add_section(
        self,
        story,
        styles,
        heading,
        content,
    ):
        if not content:
            return

        story.append(
            Paragraph(
                f"<b>{heading}</b>",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                str(content),
                styles["BodyText"],
            )
        )

        story.append(
            Spacer(1, 6)
        )


    def _add_list_section(
        self,
        story,
        styles,
        heading,
        items,
    ):
        if not items:
            return

        story.append(
            Paragraph(
                f"<b>{heading}</b>",
                styles["Heading3"],
            )
        )

        for item in items:
            story.append(
                Paragraph(
                    f"• {item}",
                    styles["BodyText"],
                )
            )

        story.append(
            Spacer(1, 6)
        )