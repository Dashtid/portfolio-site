"""
Tests for init_db module
"""


class TestInitDbModule:
    """Tests for init_db module imports and structure."""

    def test_init_db_function_exists(self):
        """Test that init_db function exists."""
        from app.init_db import init_db

        assert init_db is not None
        assert callable(init_db)

    def test_seed_data_function_exists(self):
        """Test that seed_data function exists."""
        from app.init_db import seed_data

        assert seed_data is not None
        assert callable(seed_data)

    def test_main_function_exists(self):
        """Test that main function exists."""
        from app.init_db import main

        assert main is not None
        assert callable(main)

    def test_imports_company_model(self):
        """Test that init_db imports Company model."""
        from app.init_db import Company

        assert Company is not None

    def test_imports_project_model(self):
        """Test that init_db imports Project model."""
        from app.init_db import Project

        assert Project is not None

    def test_imports_skill_model(self):
        """Test that init_db imports Skill model."""
        from app.init_db import Skill

        assert Skill is not None

    def test_imports_base(self):
        """Test that init_db imports Base."""
        from app.init_db import Base

        assert Base is not None

    def test_imports_engine(self):
        """Test that init_db imports engine."""
        from app.init_db import engine

        assert engine is not None


class TestSeedDataModule:
    """Tests for seed_data module imports and structure."""

    def test_seed_data_module_exists(self):
        """Test that seed_data module is importable."""
        import app.seed_data

        assert app.seed_data is not None

    def test_clear_existing_data_exists(self):
        """Test that clear_existing_data function exists."""
        from app.seed_data import clear_existing_data

        assert clear_existing_data is not None
        assert callable(clear_existing_data)

    def test_seed_companies_exists(self):
        """Test that seed_companies function exists."""
        from app.seed_data import seed_companies

        assert seed_companies is not None
        assert callable(seed_companies)

    def test_seed_projects_exists(self):
        """Test that seed_projects function exists."""
        from app.seed_data import seed_projects

        assert seed_projects is not None
        assert callable(seed_projects)

    def test_seed_skills_exists(self):
        """Test that seed_skills function exists."""
        from app.seed_data import seed_skills

        assert seed_skills is not None
        assert callable(seed_skills)

    def test_seed_education_exists(self):
        """Test that seed_education function exists."""
        from app.seed_data import seed_education

        assert seed_education is not None
        assert callable(seed_education)

    def test_main_exists(self):
        """Test that main function exists."""
        from app.seed_data import main

        assert main is not None
        assert callable(main)

    def test_imports_models(self):
        """Test that seed_data imports required models."""
        from app.seed_data import Company, Education, Project, Skill

        assert Company is not None
        assert Education is not None
        assert Project is not None
        assert Skill is not None
