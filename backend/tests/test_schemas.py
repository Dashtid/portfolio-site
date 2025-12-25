"""
Tests for Pydantic schemas
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.analytics import (
    AnalyticsStats,
    DailyView,
    PageViewCreate,
    PageViewResponse,
    TopPage,
    VisitorInfo,
)
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


class TestAnalyticsSchemas:
    """Tests for analytics schemas."""

    def test_page_view_create_minimal(self):
        """Test PageViewCreate with minimal data."""
        data = PageViewCreate(page_path="/home")
        assert data.page_path == "/home"
        assert data.page_title is None
        assert data.referrer is None

    def test_page_view_create_full(self):
        """Test PageViewCreate with all fields."""
        data = PageViewCreate(
            page_path="/about",
            page_title="About Me",
            referrer="https://google.com",
        )
        assert data.page_path == "/about"
        assert data.page_title == "About Me"
        assert data.referrer == "https://google.com"

    def test_page_view_response(self):
        """Test PageViewResponse schema."""
        data = PageViewResponse(
            id="abc123-uuid",
            visitor_id="visitor123",
            page_path="/contact",
            page_title="Contact",
            referrer="https://linkedin.com",
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
        )
        assert data.id == "abc123-uuid"
        assert data.visitor_id == "visitor123"
        assert data.page_path == "/contact"

    def test_top_page_schema(self):
        """Test TopPage schema."""
        data = TopPage(path="/projects", title="Projects", views=100)
        assert data.path == "/projects"
        assert data.title == "Projects"
        assert data.views == 100

    def test_daily_view_schema(self):
        """Test DailyView schema."""
        data = DailyView(date="2025-01-15", views=50)
        assert data.date == "2025-01-15"
        assert data.views == 50

    def test_analytics_stats_schema(self):
        """Test AnalyticsStats schema."""
        data = AnalyticsStats(
            total_views=1000,
            unique_visitors=500,
            avg_session_duration=180,
            top_pages=[TopPage(path="/home", title="Home", views=300)],
            daily_views=[DailyView(date="2025-01-15", views=50)],
            period_days=30,
        )
        assert data.total_views == 1000
        assert data.unique_visitors == 500
        assert len(data.top_pages) == 1
        assert len(data.daily_views) == 1
        assert data.period_days == 30

    def test_visitor_info_schema(self):
        """Test VisitorInfo schema."""
        data = VisitorInfo(
            visitor_id="visitor456",
            first_visit=datetime(2025, 1, 1),
            last_visit=datetime(2025, 1, 15),
            page_views=25,
        )
        assert data.visitor_id == "visitor456"
        assert data.page_views == 25


class TestCompanySchemas:
    """Tests for company schemas."""

    def test_company_create_minimal(self):
        """Test CompanyCreate with minimal required fields."""
        data = CompanyCreate(name="Test Company")
        assert data.name == "Test Company"

    def test_company_create_full(self):
        """Test CompanyCreate with all fields."""
        data = CompanyCreate(
            name="Tech Corp",
            title="Senior Developer",
            description="Building great software",
            location="Stockholm, Sweden",
            website="https://techcorp.com",
            logo_url="https://techcorp.com/logo.png",
            start_date="2020-01-01",
            end_date="2025-01-01",
            order_index=1,
        )
        assert data.name == "Tech Corp"
        assert data.location == "Stockholm, Sweden"

    def test_company_update_partial(self):
        """Test CompanyUpdate with partial data."""
        data = CompanyUpdate(name="Updated Company")
        assert data.name == "Updated Company"
        assert data.title is None

    def test_company_response(self):
        """Test CompanyResponse schema."""
        data = CompanyResponse(
            id="company-123",
            name="Company ABC",
            title="Engineer",
            description="Description",
            order_index=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert data.id == "company-123"
        assert data.name == "Company ABC"


class TestDocumentSchemas:
    """Tests for document schemas."""

    def test_document_create(self):
        """Test DocumentCreate schema."""
        data = DocumentCreate(
            id="doc-123",
            title="Resume",
            description="My professional resume",
            file_path="/documents/resume.pdf",
            document_type="resume",
            file_size=1024000,
            file_url="https://example.com/resume.pdf",
        )
        assert data.title == "Resume"
        assert data.document_type == "resume"
        assert data.file_size == 1024000

    def test_document_update_partial(self):
        """Test DocumentUpdate with partial fields."""
        data = DocumentUpdate(title="Updated Resume")
        assert data.title == "Updated Resume"
        assert data.description is None

    def test_document_response(self):
        """Test DocumentResponse schema."""
        data = DocumentResponse(
            id="doc-123",
            title="CV",
            description="Curriculum Vitae",
            file_path="/docs/cv.pdf",
            document_type="cv",
            file_size=512000,
            file_url="https://example.com/cv.pdf",
            created_at=datetime.now(),
        )
        assert data.id == "doc-123"
        assert data.document_type == "cv"


class TestProjectSchemas:
    """Tests for project schemas."""

    def test_project_create_minimal(self):
        """Test ProjectCreate with minimal data."""
        data = ProjectCreate(name="My Project")
        assert data.name == "My Project"
        assert data.featured is False

    def test_project_create_full(self):
        """Test ProjectCreate with all fields."""
        data = ProjectCreate(
            name="Portfolio Site",
            description="Personal portfolio website",
            detailed_description="A comprehensive personal portfolio",
            technologies=["Vue.js", "FastAPI", "PostgreSQL"],
            github_url="https://github.com/user/portfolio",
            live_url="https://portfolio.example.com",
            image_url="/images/portfolio.png",
            featured=True,
            order_index=1,
        )
        assert data.name == "Portfolio Site"
        assert data.featured is True
        assert "Vue.js" in data.technologies

    def test_project_update_partial(self):
        """Test ProjectUpdate with partial data."""
        data = ProjectUpdate(name="New Name", featured=True)
        assert data.name == "New Name"
        assert data.featured is True
        assert data.description is None

    def test_project_response(self):
        """Test ProjectResponse schema."""
        data = ProjectResponse(
            id="project-123",
            name="Test Project",
            description="Description",
            order_index=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert data.id == "project-123"
        assert data.name == "Test Project"

    def test_project_response_technologies_validation(self):
        """Test ProjectResponse technologies validation."""
        # Test with None technologies
        data = ProjectResponse(
            id="project-123",
            name="Test Project",
            technologies=None,
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.technologies == []

        # Test with comma-separated string
        data = ProjectResponse(
            id="project-456",
            name="Test Project 2",
            technologies="Python, FastAPI, Vue.js",
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.technologies == ["Python", "FastAPI", "Vue.js"]

    def test_project_response_responsibilities_validation(self):
        """Test ProjectResponse responsibilities validation."""
        # Test with None responsibilities
        data = ProjectResponse(
            id="project-123",
            name="Test Project",
            responsibilities=None,
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.responsibilities is None

        # Test with comma-separated string
        data = ProjectResponse(
            id="project-456",
            name="Test Project 2",
            responsibilities="Lead development, Code reviews, Architecture",
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.responsibilities == ["Lead development", "Code reviews", "Architecture"]

        # Test with list
        data = ProjectResponse(
            id="project-789",
            name="Test Project 3",
            responsibilities=["Task 1", "Task 2"],
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.responsibilities == ["Task 1", "Task 2"]

    def test_project_response_empty_string_parsing(self):
        """Test empty string handling in validators."""
        # Test empty technologies string
        data = ProjectResponse(
            id="project-123",
            name="Test Project",
            technologies="",
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.technologies == []

        # Test empty responsibilities string
        data = ProjectResponse(
            id="project-456",
            name="Test Project 2",
            responsibilities="",
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.responsibilities == []

    def test_project_technologies_already_list(self):
        """Test that list technologies pass through unchanged."""
        data = ProjectResponse(
            id="project-123",
            name="Test Project",
            technologies=["Python", "FastAPI"],
            order_index=1,
            created_at=datetime.now(),
        )
        assert data.technologies == ["Python", "FastAPI"]


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_page_view_requires_path(self):
        """Test that PageViewCreate requires page_path."""
        with pytest.raises(ValidationError):
            PageViewCreate()

    def test_document_create_requires_fields(self):
        """Test DocumentCreate validation for required fields."""
        with pytest.raises(ValidationError):
            DocumentCreate(title="Only Title")  # Missing required fields

    def test_project_create_requires_name(self):
        """Test ProjectCreate validation for required name field."""
        with pytest.raises(ValidationError):
            ProjectCreate()  # Missing name field

    def test_document_file_size_validation(self):
        """Test that file_size must be positive."""
        with pytest.raises(ValidationError):
            DocumentCreate(
                id="doc-123",
                title="Test",
                file_path="/test.pdf",
                document_type="test",
                file_size=0,  # Must be > 0
                file_url="https://example.com/test.pdf",
            )
