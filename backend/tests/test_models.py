"""
Tests for database models
"""

import pytest

from app.models.analytics import PageView
from app.models.company import Company
from app.models.contact import Contact
from app.models.document import Document
from app.models.education import Education
from app.models.project import Project
from app.models.skill import Skill
from app.models.user import User


class TestCompanyModel:
    """Tests for Company model."""

    def test_company_creation(self):
        """Test Company model creation."""
        company = Company(
            id="company-123",
            name="Tech Corp",
            title="Senior Developer",
            order_index=1,
        )
        assert company.name == "Tech Corp"
        assert company.title == "Senior Developer"
        assert company.id == "company-123"

    def test_company_to_dict(self):
        """Test Company to_dict method."""
        company = Company(
            id="company-123",
            name="Tech Corp",
            title="Senior Developer",
            description="Great company",
            location="Stockholm",
            order_index=1,
        )
        result = company.to_dict()
        assert result["id"] == "company-123"
        assert result["name"] == "Tech Corp"
        assert result["title"] == "Senior Developer"
        assert result["description"] == "Great company"
        assert result["location"] == "Stockholm"


class TestProjectModel:
    """Tests for Project model."""

    def test_project_creation(self):
        """Test Project model creation."""
        project = Project(
            id="project-123",
            name="Portfolio Site",
            description="A portfolio website",
            order_index=1,
        )
        assert project.name == "Portfolio Site"
        assert project.description == "A portfolio website"

    def test_project_to_dict(self):
        """Test Project to_dict method."""
        project = Project(
            id="project-123",
            name="Portfolio Site",
            description="A portfolio website",
            technologies=["Vue.js", "FastAPI"],
            github_url="https://github.com/user/repo",
            featured=True,
            order_index=1,
        )
        result = project.to_dict()
        assert result["id"] == "project-123"
        assert result["name"] == "Portfolio Site"
        assert result["technologies"] == ["Vue.js", "FastAPI"]
        assert result["github_url"] == "https://github.com/user/repo"
        assert result["featured"] is True

    def test_project_to_dict_empty_technologies(self):
        """Test Project to_dict with empty technologies."""
        project = Project(
            id="project-123",
            name="Test Project",
            technologies=None,
            order_index=1,
        )
        result = project.to_dict()
        assert result["technologies"] == []


class TestSkillModel:
    """Tests for Skill model."""

    def test_skill_creation(self):
        """Test Skill model creation."""
        skill = Skill(
            id="skill-123",
            name="Python",
            category="Programming Languages",
            proficiency=90,
            order_index=1,
        )
        assert skill.name == "Python"
        assert skill.category == "Programming Languages"
        assert skill.proficiency == 90

    def test_skill_to_dict(self):
        """Test Skill to_dict method."""
        skill = Skill(
            id="skill-123",
            name="Python",
            category="Programming Languages",
            proficiency=90,
            years_experience=5.0,
            order_index=1,
        )
        result = skill.to_dict()
        assert result["id"] == "skill-123"
        assert result["name"] == "Python"
        assert result["category"] == "Programming Languages"
        assert result["proficiency"] == 90
        assert result["years_experience"] == 5.0


class TestEducationModel:
    """Tests for Education model."""

    def test_education_creation(self):
        """Test Education model creation."""
        education = Education(
            id=1,
            institution="Royal Institute of Technology",
            degree="M.Sc.",
            field_of_study="Computer Science",
            order=1,
        )
        assert education.institution == "Royal Institute of Technology"
        assert education.degree == "M.Sc."
        assert education.field_of_study == "Computer Science"

    def test_education_with_certification(self):
        """Test Education model with certification flag."""
        education = Education(
            institution="Test University",
            degree="B.Sc.",
            is_certification=False,
        )
        assert education.is_certification is False


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """Test User model creation."""
        user = User(
            id="user-123",
            github_id=12345,
            username="testuser",
            email="test@example.com",
        )
        assert user.username == "testuser"
        assert user.github_id == 12345
        assert user.email == "test@example.com"


class TestDocumentModel:
    """Tests for Document model."""

    def test_document_creation(self):
        """Test Document model creation."""
        document = Document(
            id="doc-123",
            title="Resume",
            file_path="/documents/resume.pdf",
            document_type="resume",
        )
        assert document.title == "Resume"
        assert document.file_path == "/documents/resume.pdf"
        assert document.document_type == "resume"

    def test_document_repr(self):
        """Test Document __repr__ method."""
        document = Document(
            id="doc-123",
            title="Bachelor Thesis",
            file_path="/documents/thesis.pdf",
            document_type="thesis",
        )
        result = repr(document)
        assert "Bachelor Thesis" in result
        assert "thesis" in result


class TestContactModel:
    """Tests for Contact model."""

    def test_contact_creation(self):
        """Test Contact model creation."""
        contact = Contact(
            id="contact-123",
            name="John Doe",
            email="visitor@example.com",
            subject="Hello",
            message="Test message",
        )
        assert contact.email == "visitor@example.com"
        assert contact.name == "John Doe"
        assert contact.message == "Test message"

    def test_contact_to_dict(self):
        """Test Contact to_dict method."""
        contact = Contact(
            id="contact-123",
            name="John Doe",
            email="visitor@example.com",
            subject="Hello",
            message="Test message",
            status="unread",
        )
        result = contact.to_dict()
        assert result["id"] == "contact-123"
        assert result["name"] == "John Doe"
        assert result["email"] == "visitor@example.com"
        assert result["status"] == "unread"


class TestPageViewModel:
    """Tests for PageView model."""

    def test_page_view_creation(self):
        """Test PageView model creation."""
        page_view = PageView(
            id="pv-123",
            page_path="/home",
            referrer="https://google.com",
        )
        assert page_view.page_path == "/home"
        assert page_view.referrer == "https://google.com"

    def test_page_view_to_dict(self):
        """Test PageView to_dict method."""
        page_view = PageView(
            id="pv-123",
            page_path="/home",
            referrer="https://google.com",
            country="SE",
            city="Stockholm",
        )
        result = page_view.to_dict()
        assert result["id"] == "pv-123"
        assert result["page_path"] == "/home"
        assert result["country"] == "SE"
        assert result["city"] == "Stockholm"


class TestModelDefaults:
    """Tests for model default field values.

    Note: SQLAlchemy Column defaults are only applied when inserting
    into the database, not when creating objects in memory.
    These tests verify explicit values work correctly.
    """

    def test_company_with_explicit_values(self):
        """Test Company model with explicit values."""
        company = Company(name="Test", order_index=0, description=None)
        assert company.description is None
        assert company.order_index == 0

    def test_project_with_explicit_values(self):
        """Test Project model with explicit values."""
        project = Project(name="Test Project", featured=False, order_index=0)
        assert project.featured is False
        assert project.order_index == 0

    def test_skill_with_explicit_values(self):
        """Test Skill model with explicit values."""
        skill = Skill(name="Test Skill", order_index=0)
        assert skill.years_experience is None
        assert skill.order_index == 0

    def test_contact_with_status(self):
        """Test Contact with status value."""
        contact = Contact(
            name="Test",
            email="test@test.com",
            message="Test message",
            status="unread",
        )
        assert contact.status == "unread"
