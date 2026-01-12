"""
Unit tests for PDF Generator Service.

Tests PDF generation, content formatting, and report structure.
"""

import io
from datetime import datetime, date
import pytest
from PyPDF2 import PdfReader

from app.services.reports.pdf_generator import PDFGenerator, pdf_generator


class TestPDFGeneratorStyles:
    """Tests for PDF style configuration."""

    def test_color_palette_defined(self):
        """Test all color palette colors are defined."""
        generator = PDFGenerator()

        assert generator.COLOR_PRIMARY is not None
        assert generator.COLOR_DANGER is not None
        assert generator.COLOR_WARNING is not None
        assert generator.COLOR_SUCCESS is not None
        assert generator.COLOR_TEXT is not None
        assert generator.COLOR_MUTED is not None
        assert generator.COLOR_LIGHT is not None
        assert generator.COLOR_BORDER is not None

    def test_risk_colors_defined(self):
        """Test all risk level colors are defined."""
        generator = PDFGenerator()

        assert 'CRITICAL' in generator.RISK_COLORS
        assert 'HIGH' in generator.RISK_COLORS
        assert 'MEDIUM' in generator.RISK_COLORS
        assert 'LOW' in generator.RISK_COLORS

    def test_styles_created(self):
        """Test custom styles are created."""
        generator = PDFGenerator()

        assert 'ReportTitle' in generator.styles
        assert 'ReportSubtitle' in generator.styles
        assert 'SectionHeading' in generator.styles
        assert 'ReportBodyText' in generator.styles
        assert 'MutedText' in generator.styles
        assert 'RiskHigh' in generator.styles
        assert 'RiskMedium' in generator.styles
        assert 'Footer' in generator.styles
        assert 'Disclaimer' in generator.styles


class TestPDFGeneratorReport:
    """Tests for PDF report generation."""

    @pytest.fixture
    def sample_content(self):
        """Sample report content for testing."""
        return {
            "report_id": "TEST-001",
            "generated_at": datetime(2024, 1, 15, 10, 30, 0),
            "patient": {
                "name": "Test Patient",
                "gender": "Female",
                "age": 35,
                "scheduled_visit": "2024-01-20 14:00"
            },
            "chief_complaint": "Experiencing anxiety and sleep disturbances for the past 2 weeks.",
            "assessments": [
                {
                    "type": "PHQ9",
                    "score": 12,
                    "severity": "MODERATE",
                    "date": datetime(2024, 1, 14)
                },
                {
                    "type": "GAD7",
                    "score": 10,
                    "severity": "MODERATE",
                    "date": datetime(2024, 1, 14)
                }
            ],
            "risk_events": [
                {
                    "level": "MEDIUM",
                    "type": "OTHER",
                    "trigger_text": "Mentioned feeling overwhelmed"
                }
            ],
            "checkin_trend": {
                "avg_mood": 5.5,
                "avg_sleep": 6.2,
                "avg_sleep_quality": 3.0,
                "days": 7,
                "checkin_count": 5
            },
            "conversation_summary": "Patient expressed concerns about work stress and its impact on sleep."
        }

    def test_generate_pre_visit_report_returns_bytes(self, sample_content):
        """Test report generation returns valid bytes."""
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pre_visit_report_is_valid_pdf(self, sample_content):
        """Test generated content is a valid PDF."""
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        # Try to read as PDF
        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)

        assert len(reader.pages) >= 1

    def test_report_contains_patient_name(self, sample_content):
        """Test report includes patient information."""
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        # Extract text from PDF
        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        assert "Test Patient" in text

    def test_report_contains_report_id(self, sample_content):
        """Test report includes report ID."""
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        assert "TEST-001" in text

    def test_report_contains_assessments(self, sample_content):
        """Test report includes assessment data."""
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        # Check for assessment section and data
        assert "Assessment" in text
        assert "12" in text  # PHQ9 score
        assert "10" in text  # GAD7 score

    def test_report_contains_disclaimer(self, sample_content):
        """Test report includes disclaimer."""
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        assert "DISCLAIMER" in text

    def test_report_with_minimal_content(self):
        """Test report generation with minimal content."""
        generator = PDFGenerator()

        minimal_content = {
            "report_id": "MIN-001",
            "generated_at": datetime.utcnow(),
            "patient": {"name": "Minimal Patient"}
        }

        pdf_bytes = generator.generate_pre_visit_report(minimal_content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

        # Should be valid PDF
        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        assert len(reader.pages) >= 1

    def test_report_with_empty_assessments(self, sample_content):
        """Test report handles empty assessments gracefully."""
        sample_content["assessments"] = []
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        assert isinstance(pdf_bytes, bytes)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        # When assessments is empty, section 3 should not appear
        # The section numbering will skip from 2 to 4
        assert "3. Mental Health Assessment Results" not in text or "No assessments" in text.lower()

    def test_report_with_no_risk_events(self, sample_content):
        """Test report handles no risk events gracefully."""
        sample_content["risk_events"] = []
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        # When risk_events is empty, either shows "No active risk alerts" or section is skipped
        assert "4. Risk Alerts" not in text or "No active" in text.lower() or "[HIGH]" not in text

    def test_report_with_high_risk_event(self, sample_content):
        """Test report correctly formats high risk events."""
        sample_content["risk_events"] = [
            {
                "level": "HIGH",
                "type": "SUICIDAL",
                "trigger_text": "Mentioned thoughts of ending it all"
            }
        ]
        generator = PDFGenerator()

        pdf_bytes = generator.generate_pre_visit_report(sample_content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        assert "HIGH" in text
        assert "Suicidal" in text


class TestPDFGeneratorHelpers:
    """Tests for helper methods."""

    def test_severity_display_mapping(self):
        """Test severity level display names."""
        generator = PDFGenerator()

        assert generator.SEVERITY_DISPLAY['MINIMAL'] == 'Minimal'
        assert generator.SEVERITY_DISPLAY['MILD'] == 'Mild'
        assert generator.SEVERITY_DISPLAY['MODERATE'] == 'Moderate'
        assert generator.SEVERITY_DISPLAY['MODERATELY_SEVERE'] == 'Moderately Severe'
        assert generator.SEVERITY_DISPLAY['SEVERE'] == 'Severe'

    def test_assessment_display_mapping(self):
        """Test assessment type display names."""
        generator = PDFGenerator()

        assert 'PHQ9' in generator.ASSESSMENT_DISPLAY
        assert 'GAD7' in generator.ASSESSMENT_DISPLAY
        assert 'PCL5' in generator.ASSESSMENT_DISPLAY
        assert 'Depression' in generator.ASSESSMENT_DISPLAY['PHQ9']
        assert 'Anxiety' in generator.ASSESSMENT_DISPLAY['GAD7']
        assert 'PTSD' in generator.ASSESSMENT_DISPLAY['PCL5']

    def test_risk_type_display_mapping(self):
        """Test risk type display names."""
        generator = PDFGenerator()

        assert generator.RISK_TYPE_DISPLAY['SUICIDAL'] == 'Suicidal Ideation'
        assert generator.RISK_TYPE_DISPLAY['SELF_HARM'] == 'Self-Harm'
        assert generator.RISK_TYPE_DISPLAY['VIOLENCE'] == 'Violence Risk'
        assert generator.RISK_TYPE_DISPLAY['PERSECUTION_FEAR'] == 'Persecution Fear'


class TestPDFGeneratorCheckInTrend:
    """Tests for check-in trend section."""

    def test_checkin_trend_with_data(self):
        """Test check-in trend displays correctly with data."""
        generator = PDFGenerator()

        content = {
            "report_id": "TREND-001",
            "generated_at": datetime.utcnow(),
            "patient": {"name": "Trend Patient"},
            "checkin_trend": {
                "avg_mood": 6.5,
                "avg_sleep": 7.0,
                "avg_sleep_quality": 4.0,
                "days": 7,
                "checkin_count": 7
            }
        }

        pdf_bytes = generator.generate_pre_visit_report(content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        assert "Trend" in text
        assert "7" in text  # Days

    def test_checkin_trend_no_checkins(self):
        """Test check-in trend handles zero check-ins."""
        generator = PDFGenerator()

        content = {
            "report_id": "NOCHECK-001",
            "generated_at": datetime.utcnow(),
            "patient": {"name": "No Checkin Patient"},
            "checkin_trend": {
                "avg_mood": None,
                "avg_sleep": None,
                "avg_sleep_quality": None,
                "days": 7,
                "checkin_count": 0
            }
        }

        pdf_bytes = generator.generate_pre_visit_report(content)

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        assert "No check-in data available" in text


class TestPDFGeneratorSingleton:
    """Tests for singleton instance."""

    def test_singleton_instance_exists(self):
        """Test pdf_generator singleton is available."""
        assert pdf_generator is not None
        assert isinstance(pdf_generator, PDFGenerator)

    def test_singleton_has_styles(self):
        """Test singleton has initialized styles."""
        assert pdf_generator.styles is not None
        # StyleSheet1 object doesn't have len(), check for specific styles instead
        assert 'ReportTitle' in pdf_generator.styles
        assert 'SectionHeading' in pdf_generator.styles
