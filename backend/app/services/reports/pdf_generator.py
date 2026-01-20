"""
PDF Generator for clinical reports using ReportLab.
"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus.flowables import Flowable


class LogoPlaceholder(Flowable):
    """Placeholder for logo - renders a rectangle with text."""

    def __init__(self, width=60 * mm, height=20 * mm):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setStrokeColor(HexColor("#CBD5E1"))
        self.canv.setFillColor(HexColor("#F1F5F9"))
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=1)
        self.canv.setFillColor(HexColor("#64748B"))
        self.canv.setFont("Helvetica", 10)
        text_width = self.canv.stringWidth("[LOGO]", "Helvetica", 10)
        self.canv.drawString((self.width - text_width) / 2, self.height / 2 - 3, "[LOGO]")


class PDFGenerator:
    """
    PDF Generator using ReportLab.
    Generates professional clinical reports with consistent styling.
    """

    # Color palette
    COLOR_PRIMARY = HexColor("#2563EB")  # Blue
    COLOR_DANGER = HexColor("#DC2626")  # Red
    COLOR_WARNING = HexColor("#F59E0B")  # Orange/Amber
    COLOR_SUCCESS = HexColor("#16A34A")  # Green
    COLOR_TEXT = HexColor("#1F2937")  # Dark gray
    COLOR_MUTED = HexColor("#6B7280")  # Medium gray
    COLOR_LIGHT = HexColor("#F3F4F6")  # Light gray background
    COLOR_BORDER = HexColor("#E5E7EB")  # Border gray

    # Risk level colors
    RISK_COLORS = {
        "CRITICAL": HexColor("#7F1D1D"),  # Dark red
        "HIGH": HexColor("#DC2626"),  # Red
        "MEDIUM": HexColor("#F59E0B"),  # Amber
        "LOW": HexColor("#16A34A"),  # Green
    }

    # Severity display names
    SEVERITY_DISPLAY = {
        "MINIMAL": "Minimal",
        "MILD": "Mild",
        "MODERATE": "Moderate",
        "MODERATELY_SEVERE": "Moderately Severe",
        "SEVERE": "Severe",
    }

    # Assessment display names
    ASSESSMENT_DISPLAY = {
        "PHQ9": "PHQ-9 (Depression)",
        "GAD7": "GAD-7 (Anxiety)",
        "PCL5": "PCL-5 (PTSD)",
        "PSS": "PSS (Stress)",
        "ISI": "ISI (Insomnia)",
    }

    # Risk type display names
    RISK_TYPE_DISPLAY = {
        "SUICIDAL": "Suicidal Ideation",
        "SELF_HARM": "Self-Harm",
        "VIOLENCE": "Violence Risk",
        "PERSECUTION_FEAR": "Persecution Fear",
        "OTHER": "Other Risk",
    }

    def __init__(self):
        self.styles = self._create_styles()

    def _create_styles(self) -> dict:
        """Create custom paragraph styles."""
        styles = getSampleStyleSheet()

        # Title style
        styles.add(
            ParagraphStyle(
                "ReportTitle",
                fontName="Helvetica-Bold",
                fontSize=18,
                textColor=self.COLOR_PRIMARY,
                alignment=TA_CENTER,
                spaceAfter=6,
            )
        )

        # Subtitle style
        styles.add(
            ParagraphStyle(
                "ReportSubtitle",
                fontName="Helvetica",
                fontSize=10,
                textColor=self.COLOR_MUTED,
                alignment=TA_CENTER,
                spaceAfter=20,
            )
        )

        # Section heading style
        styles.add(
            ParagraphStyle(
                "SectionHeading",
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=self.COLOR_TEXT,
                spaceBefore=16,
                spaceAfter=8,
                borderPadding=4,
            )
        )

        # Body text style (using custom name to avoid conflict with built-in)
        styles.add(
            ParagraphStyle(
                "ReportBodyText",
                fontName="Helvetica",
                fontSize=10,
                textColor=self.COLOR_TEXT,
                leading=14,
                spaceAfter=6,
            )
        )

        # Muted text style
        styles.add(
            ParagraphStyle(
                "MutedText",
                fontName="Helvetica",
                fontSize=9,
                textColor=self.COLOR_MUTED,
                leading=12,
            )
        )

        # Risk alert styles
        styles.add(
            ParagraphStyle(
                "RiskHigh",
                fontName="Helvetica-Bold",
                fontSize=10,
                textColor=self.COLOR_DANGER,
                spaceBefore=4,
                spaceAfter=4,
            )
        )

        styles.add(
            ParagraphStyle(
                "RiskMedium",
                fontName="Helvetica-Bold",
                fontSize=10,
                textColor=self.COLOR_WARNING,
                spaceBefore=4,
                spaceAfter=4,
            )
        )

        # Footer style
        styles.add(
            ParagraphStyle(
                "Footer",
                fontName="Helvetica",
                fontSize=8,
                textColor=self.COLOR_MUTED,
                alignment=TA_CENTER,
            )
        )

        # Disclaimer style
        styles.add(
            ParagraphStyle(
                "Disclaimer",
                fontName="Helvetica-Oblique",
                fontSize=8,
                textColor=self.COLOR_MUTED,
                alignment=TA_CENTER,
                spaceBefore=20,
            )
        )

        return styles

    def generate_pre_visit_report(self, content: Dict[str, Any]) -> bytes:
        """
        Generate a Pre-Visit Clinical Summary PDF.

        Args:
            content: Dictionary containing report data:
                - report_id: str
                - generated_at: datetime
                - patient: dict (name, gender, age, scheduled_visit)
                - chief_complaint: str
                - assessments: list of dicts
                - risk_events: list of dicts
                - checkin_trend: dict (avg_mood, avg_sleep, avg_sleep_quality, days)
                - conversation_summary: str

        Returns:
            PDF bytes
        """
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        elements = []

        # Header section
        elements.extend(self._build_header(content))

        # Patient information
        elements.extend(self._build_patient_info(content.get("patient", {})))

        # Chief complaint
        if content.get("chief_complaint"):
            elements.extend(self._build_chief_complaint(content["chief_complaint"]))

        # Assessment results
        if content.get("assessments"):
            elements.extend(self._build_assessments(content["assessments"]))

        # Risk alerts
        if content.get("risk_events"):
            elements.extend(self._build_risk_alerts(content["risk_events"]))

        # Check-in trends
        if content.get("checkin_trend"):
            elements.extend(self._build_checkin_trend(content["checkin_trend"]))

        # Conversation summary
        if content.get("conversation_summary"):
            elements.extend(self._build_conversation_summary(content["conversation_summary"]))

        # Footer/Disclaimer
        elements.extend(self._build_footer())

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(self, content: Dict[str, Any]) -> List:
        """Build report header with logo placeholder and title."""
        elements = []

        # Logo placeholder
        elements.append(LogoPlaceholder())
        elements.append(Spacer(1, 10))

        # Title
        elements.append(Paragraph("Pre-Visit Clinical Summary", self.styles["ReportTitle"]))

        # Metadata
        report_id = content.get("report_id", "N/A")
        generated_at = content.get("generated_at", datetime.utcnow())
        if isinstance(generated_at, datetime):
            generated_str = generated_at.strftime("%Y-%m-%d %H:%M UTC")
        else:
            generated_str = str(generated_at)

        elements.append(
            Paragraph(
                f"Report ID: {report_id} | Generated: {generated_str}",
                self.styles["ReportSubtitle"],
            )
        )

        # Divider
        elements.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=self.COLOR_BORDER,
                spaceBefore=5,
                spaceAfter=15,
            )
        )

        return elements

    def _build_patient_info(self, patient: Dict[str, Any]) -> List:
        """Build patient information section."""
        elements = []

        elements.append(Paragraph("1. Patient Information", self.styles["SectionHeading"]))

        # Create info table
        data = [
            [
                "Name:",
                patient.get("name", "N/A"),
                "Gender:",
                patient.get("gender", "N/A"),
            ],
            [
                "Age:",
                str(patient.get("age", "N/A")),
                "Scheduled Visit:",
                patient.get("scheduled_visit", "N/A"),
            ],
        ]

        table = Table(data, colWidths=[70, 150, 80, 150])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTNAME", (3, 0), (3, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLOR_TEXT),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 10))

        return elements

    def _build_chief_complaint(self, chief_complaint: str) -> List:
        """Build chief complaint section."""
        elements = []

        elements.append(Paragraph("2. Chief Complaint", self.styles["SectionHeading"]))
        elements.append(Paragraph(chief_complaint, self.styles["ReportBodyText"]))
        elements.append(Spacer(1, 10))

        return elements

    def _build_assessments(self, assessments: List[Dict[str, Any]]) -> List:
        """Build mental health assessments section."""
        elements = []

        elements.append(Paragraph("3. Mental Health Assessment Results", self.styles["SectionHeading"]))

        if not assessments:
            elements.append(Paragraph("No assessments available.", self.styles["MutedText"]))
            return elements

        # Header row
        data = [["Assessment", "Score", "Severity", "Date"]]

        # Data rows
        for assessment in assessments:
            assessment_type = assessment.get("type", "Unknown")
            display_name = self.ASSESSMENT_DISPLAY.get(assessment_type, assessment_type)
            score = str(assessment.get("score", "N/A"))
            severity = assessment.get("severity", "N/A")
            severity_display = self.SEVERITY_DISPLAY.get(severity, severity)

            date_val = assessment.get("date")
            if isinstance(date_val, datetime):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val) if date_val else "N/A"

            data.append([display_name, score, severity_display, date_str])

        table = Table(data, colWidths=[160, 60, 120, 80])
        table.setStyle(
            TableStyle(
                [
                    # Header style
                    ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_PRIMARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    # Body style
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 1), (-1, -1), self.COLOR_TEXT),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),  # Score column centered
                    ("ALIGN", (3, 1), (3, -1), "CENTER"),  # Date column centered
                    # Grid
                    ("GRID", (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    # Alternate row colors
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, self.COLOR_LIGHT]),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 10))

        return elements

    def _build_risk_alerts(self, risk_events: List[Dict[str, Any]]) -> List:
        """Build risk alerts section."""
        elements = []

        elements.append(Paragraph("4. Risk Alerts", self.styles["SectionHeading"]))

        if not risk_events:
            elements.append(Paragraph("No active risk alerts.", self.styles["MutedText"]))
            return elements

        for event in risk_events:
            risk_level = event.get("level", "MEDIUM")
            risk_type = event.get("type", "OTHER")
            trigger_text = event.get("trigger_text", "")

            level_display = risk_level.upper()
            type_display = self.RISK_TYPE_DISPLAY.get(risk_type, risk_type)

            # Choose style based on risk level
            if risk_level in ["HIGH", "CRITICAL"]:
                style = self.styles["RiskHigh"]
                bullet = "\u2022"  # Bullet point
            else:
                style = self.styles["RiskMedium"]
                bullet = "\u2022"

            # Build alert text
            alert_text = f"{bullet} [{level_display}] {type_display}"
            if trigger_text:
                # Truncate long trigger text
                if len(trigger_text) > 100:
                    trigger_text = trigger_text[:100] + "..."
                alert_text += f' - "{trigger_text}"'

            elements.append(Paragraph(alert_text, style))

        elements.append(Spacer(1, 10))

        return elements

    def _build_checkin_trend(self, trend: Dict[str, Any]) -> List:
        """Build check-in trend section."""
        elements = []

        days = trend.get("days", 7)
        elements.append(
            Paragraph(
                f"5. Recent Status Trend (Past {days} Days)",
                self.styles["SectionHeading"],
            )
        )

        avg_mood = trend.get("avg_mood")
        avg_sleep = trend.get("avg_sleep")
        avg_sleep_quality = trend.get("avg_sleep_quality")
        checkin_count = trend.get("checkin_count", 0)

        if checkin_count == 0:
            elements.append(
                Paragraph(
                    "No check-in data available for this period.",
                    self.styles["MutedText"],
                )
            )
            return elements

        # Format values
        mood_str = f"{avg_mood:.1f}/10" if avg_mood is not None else "N/A"
        sleep_str = f"{avg_sleep:.1f}h" if avg_sleep is not None else "N/A"
        quality_str = f"{avg_sleep_quality:.1f}/5" if avg_sleep_quality is not None else "N/A"

        # Create trend display
        data = [
            [
                f"Avg Mood: {mood_str}",
                f"Avg Sleep: {sleep_str}",
                f"Sleep Quality: {quality_str}",
                f"Check-ins: {checkin_count}",
            ]
        ]

        table = Table(data, colWidths=[110, 100, 110, 100])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.COLOR_LIGHT),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLOR_TEXT),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOX", (0, 0), (-1, -1), 0.5, self.COLOR_BORDER),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 10))

        return elements

    def _build_conversation_summary(self, summary: str) -> List:
        """Build conversation summary section."""
        elements = []

        elements.append(Paragraph("6. Conversation Summary", self.styles["SectionHeading"]))
        elements.append(Paragraph(summary, self.styles["ReportBodyText"]))
        elements.append(Spacer(1, 10))

        return elements

    def _build_footer(self) -> List:
        """Build report footer with disclaimer."""
        elements = []

        elements.append(Spacer(1, 20))

        # Disclaimer
        disclaimer = (
            "DISCLAIMER: This report is generated by AI for triage purposes only. "
            "It does not constitute a clinical diagnosis. All clinical decisions "
            "should be made by qualified healthcare professionals."
        )
        elements.append(Paragraph(disclaimer, self.styles["Disclaimer"]))

        elements.append(Spacer(1, 10))

        # Confidential marker
        elements.append(Paragraph("CONFIDENTIAL - For authorized use only", self.styles["Footer"]))

        return elements


# Singleton instance
pdf_generator = PDFGenerator()
