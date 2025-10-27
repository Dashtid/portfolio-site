# Development Tooling Guide

This document describes the modern development tooling infrastructure implemented for the Portfolio Migration project, following 2025 best practices.

## Overview

The project uses a comprehensive tooling stack to ensure code quality, consistency, and maintainability across both frontend and backend codebases.

## Frontend Tooling

### ESLint 9.38.0

Modern JavaScript/TypeScript linter with flat configuration format (introduced in ESLint 9).

**Configuration**: `frontend/eslint.config.js`

**Features**:
- Flat config format (modern replacement for .eslintrc)
- Vue 3 support with eslint-plugin-vue
- TypeScript support with @typescript-eslint
- Prettier integration for consistent formatting
- Custom rules for project-specific needs

**Usage**:
```bash
cd frontend

# Check for linting issues
npm run lint

# Auto-fix linting issues
npm run lint:fix
```

**Key Rules**:
- Vue 3 recommended rules
- TypeScript strict mode
- Prettier formatting enforcement
- No console.log in production builds

### Prettier 3.6.2

Opinionated code formatter for consistent style.

**Configuration**: `frontend/.prettierrc.json`

**Settings**:
- No semicolons (modern JavaScript style)
- Single quotes for strings
- 100 character line width
- 2-space indentation
- LF line endings

**Usage**:
```bash
cd frontend

# Format all files
npm run format

# Check formatting without modifying files
npm run format:check
```

**Integration**:
- Runs automatically via ESLint (eslint-plugin-prettier)
- Pre-commit hook ensures all commits are formatted
- VSCode extension recommended for format-on-save

### TypeScript 5.9.3

Strict type checking for type safety.

**Configuration**: `frontend/tsconfig.json`

**Usage**:
```bash
cd frontend

# Type check without emitting files
npm run type-check
```

**Features**:
- Strict mode enabled
- Path aliases (@/ for src/)
- Vue 3 type support
- Composition API types

### Vite 7.1.7

Modern build tool and dev server.

**Configuration**: `frontend/vite.config.ts`

**Features**:
- TypeScript configuration file
- Advanced chunk splitting for optimal caching
- Bundle analysis support (run with ANALYZE=true)
- Production optimizations (Terser, minification)
- Manual vendor chunks (Vue, VueUse, Axios)

**Usage**:
```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build

# Build with bundle analysis
ANALYZE=true npm run build
```

### Vitest 2.1.9

Unit testing framework built on Vite.

**Configuration**: `frontend/vitest.config.ts`

**Features**:
- v8 coverage provider
- Happy-DOM environment (faster than jsdom)
- 80% coverage thresholds
- HTML and LCOV coverage reports

**Usage**:
```bash
cd frontend

# Run tests in watch mode
npm run test

# Run tests once with coverage
npm run coverage
```

## Backend Tooling

### Ruff 0.14.2

All-in-one Python linter and formatter (replaces Black, isort, Flake8, autoflake).

**Configuration**: `backend/pyproject.toml`

**Features**:
- 10-100x faster than traditional tools
- Comprehensive rule sets:
  - E/W: pycodestyle errors and warnings
  - F: pyflakes
  - I: isort (import sorting)
  - UP: pyupgrade (modern Python syntax)
  - B: flake8-bugbear
  - C4: flake8-comprehensions
  - SIM: flake8-simplify
  - PL: pylint
  - PERF: perflint (performance)
- Auto-fix capabilities
- Compatible with Black's formatting style

**Usage**:
```bash
cd backend

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Lint and format together
ruff check --fix . && ruff format .
```

**Results**:
- Auto-fixed 401 linting issues
- Reformatted 62 Python files
- 101 remaining issues (mostly FastAPI dependency injection patterns)

### mypy 1.18.2

Static type checker for Python.

**Configuration**: `backend/pyproject.toml`

**Features**:
- Strict mode enabled
- Python 3.11 target version
- Type stub packages (types-passlib, types-python-jose)
- Untyped definitions checking
- Error code display

**Usage**:
```bash
cd backend

# Type check all files
mypy .

# Type check specific file
mypy app/api/v1/auth.py
```

**Coverage**:
- All FastAPI routes are type-hinted
- Pydantic models provide automatic type validation
- SQLAlchemy models use declarative syntax with types

### pytest 8.3.4

Python testing framework.

**Configuration**: `backend/pyproject.toml`

**Features**:
- Async test support (asyncio mode)
- Coverage reporting (pytest-cov)
- HTML and terminal coverage reports
- 55% current coverage (baseline established)

**Usage**:
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### pyproject.toml

Modern Python packaging standard (PEP 518, 621).

**Features**:
- Centralized configuration for all tools
- Dependency management
- Project metadata
- Tool-specific configurations (Ruff, mypy, pytest, coverage)

**Benefits over requirements.txt**:
- Single source of truth
- Tool configuration co-located
- Standard format across Python ecosystem
- Better dependency resolution

## Cross-Project Tooling

### EditorConfig

Maintains consistent coding styles across different editors and IDEs.

**Configuration**: `.editorconfig`

**Settings**:
- LF line endings (all files)
- UTF-8 charset
- Trim trailing whitespace
- Final newline enforcement
- Python: 4 spaces, 100 char line length
- JS/TS/Vue: 2 spaces, 100 char line length
- YAML: 2 spaces

**Supported Editors**:
- VSCode (built-in)
- JetBrains IDEs (built-in)
- Sublime Text (plugin)
- Atom (plugin)
- Vim/Neovim (plugin)

### Pre-commit Hooks

Automated quality checks on every commit.

**Configuration**: `.pre-commit-config.yaml`

**Hooks**:
1. **General File Checks**:
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML validation
   - JSON validation
   - Large file detection (max 1MB)
   - Merge conflict detection
   - Line ending normalization (LF)

2. **Frontend Hooks**:
   - Prettier (auto-format)
   - ESLint (lint and fix)

3. **Backend Hooks**:
   - Ruff linter (auto-fix)
   - Ruff formatter
   - mypy type checking

**Installation**:
```bash
# Install pre-commit hooks (already done)
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

**Workflow**:
1. Developer makes changes
2. git commit triggers pre-commit
3. All hooks run automatically
4. If any hook fails:
   - Auto-fixable issues are fixed automatically
   - Developer must stage fixed files
   - Commit again
5. If all hooks pass, commit succeeds

## IDE Setup Recommendations

### VSCode Extensions

Recommended extensions for optimal development experience:

**Essential**:
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- Vue - Official (Vue.volar)
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)

**Optional**:
- EditorConfig for VS Code (editorconfig.editorconfig)
- GitLens (eamodio.gitlens)
- Error Lens (usernamehw.errorlens)

**VSCode Settings** (add to `.vscode/settings.json`):
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "[javascript][typescript][vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## CI/CD Integration (Future)

Planned GitHub Actions workflows:

**Frontend Pipeline**:
```yaml
- Checkout code
- Setup Node.js
- Install dependencies
- Run ESLint
- Run Prettier check
- Run type check (vue-tsc)
- Run tests with coverage
- Build production bundle
- Upload coverage to Codecov
```

**Backend Pipeline**:
```yaml
- Checkout code
- Setup Python
- Install dependencies
- Run Ruff check
- Run Ruff format check
- Run mypy
- Run pytest with coverage
- Upload coverage to Codecov
```

**Pre-commit CI**:
```yaml
- Run all pre-commit hooks on CI
- Ensures no commits bypass local checks
```

## Troubleshooting

### ESLint Issues

**Problem**: "Cannot find eslint.config.js"
**Solution**: Ensure you're in the frontend directory and the file exists

**Problem**: ESLint errors on Vue files
**Solution**: Make sure vue-eslint-parser is installed: `npm install --save-dev vue-eslint-parser`

### Ruff Issues

**Problem**: "Command not found: ruff"
**Solution**: Install Ruff: `pip install ruff` or use the venv: `.venv/Scripts/python.exe -m ruff`

**Problem**: Ruff conflicts with existing Black/isort configs
**Solution**: Remove Black and isort configs, Ruff replaces both

### Pre-commit Issues

**Problem**: Pre-commit hooks not running
**Solution**: Reinstall hooks: `pre-commit install`

**Problem**: Pre-commit hooks failing on Windows line endings
**Solution**: The mixed-line-ending hook will auto-fix this

**Problem**: Pre-commit hooks taking too long
**Solution**: Hooks cache environments after first run, subsequent runs are much faster

## Best Practices

### Development Workflow

1. **Before starting work**:
   ```bash
   git pull
   pre-commit run --all-files  # Ensure everything is clean
   ```

2. **During development**:
   - Let IDE auto-format on save (Prettier/Ruff)
   - Run linters frequently: `npm run lint` or `ruff check .`
   - Run tests: `npm test` or `pytest`

3. **Before committing**:
   ```bash
   # Frontend
   npm run lint:fix
   npm run format
   npm run type-check
   npm test

   # Backend
   ruff check --fix .
   ruff format .
   mypy .
   pytest
   ```

4. **Commit**:
   - Pre-commit hooks run automatically
   - If hooks fail, fix issues and commit again
   - Use conventional commit messages (future: commitlint)

### Code Quality Standards

**Frontend**:
- All new code must pass ESLint with zero warnings
- All code must be Prettier-formatted
- TypeScript strict mode must not be violated
- New features require tests (maintain 80% coverage)

**Backend**:
- All new code must pass Ruff linting
- All code must be Ruff-formatted
- Type hints required for all functions (mypy compliance)
- New endpoints require tests (target 80% coverage)

**Both**:
- No commits allowed without passing pre-commit hooks
- EditorConfig settings must be respected
- Line endings must be LF (enforced by pre-commit)

## Maintenance

### Updating Tools

**Frontend**:
```bash
cd frontend
npm update eslint prettier @typescript-eslint/parser  # etc.
npm audit fix  # Security updates
```

**Backend**:
```bash
cd backend
pip install --upgrade ruff mypy pytest
```

**Pre-commit**:
```bash
pre-commit autoupdate  # Updates hook versions in config
```

### Monitoring Tool Performance

**ESLint**:
- Check with TIMING=1: `TIMING=1 npm run lint`

**Ruff**:
- Ruff is extremely fast (no performance monitoring needed)
- Typical run time: <100ms for entire backend

**Pre-commit**:
- First run: ~2-5 minutes (installs environments)
- Subsequent runs: ~10-30 seconds

## Migration Notes

### From Legacy Tools

This project migrated from:
- **No linting** → ESLint 9 (frontend), Ruff (backend)
- **No formatting** → Prettier (frontend), Ruff format (backend)
- **No type checking** → TypeScript strict (frontend), mypy strict (backend)
- **Manual quality checks** → Automated pre-commit hooks

### Results

**Frontend**:
- Auto-fixed all Prettier formatting issues
- Auto-fixed all ESLint issues
- Migrated configs to TypeScript (vite.config.ts, vitest.config.ts)

**Backend**:
- Auto-fixed 401 Ruff linting issues
- Reformatted 62 Python files
- Standardized line endings (LF)
- Established baseline for type coverage

**Benefits**:
- Consistent code style across team
- Automated quality enforcement
- Faster code reviews (no style discussions)
- Reduced bugs through static analysis
- Modern tooling (2025 best practices)

## References

- [ESLint Flat Config Docs](https://eslint.org/docs/latest/use/configure/configuration-files-new)
- [Prettier Documentation](https://prettier.io/docs/en/index.html)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [EditorConfig Specification](https://editorconfig.org/)

---

**Last Updated**: 2025-10-27
**Tooling Version**: 1.0.0
