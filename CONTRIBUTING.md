# Contributing to CEF Upgrade Agent

Thank you for your interest in contributing to the CEF Upgrade Agent! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/CEF-Upgrade-Agent.git
   cd CEF-Upgrade-Agent
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

There are many ways to contribute:

- **Report bugs** and issues
- **Suggest new features** or enhancements
- **Improve documentation**
- **Write code** to fix bugs or add features
- **Review pull requests**
- **Test** the agent on different platforms
- **Share** your experience using the agent

## Development Setup

### Prerequisites

- Python 3.6 or higher
- Git
- A text editor or IDE (VS Code, PyCharm, etc.)

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install development dependencies:
   ```bash
   pip install pytest pytest-cov pylint black mypy
   ```

### Running the Agent

Test your changes with a dry run:
```bash
python cef_upgrade_agent.py --target-version "120.1.10+g3ce3184+chromium-120.0.6099.129" --dry-run
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: Maximum 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings (except when single quotes avoid escaping)
- **Imports**: Group in order: standard library, third-party, local
- **Docstrings**: Use Google-style docstrings

### Code Formatting

We use `black` for automatic code formatting:

```bash
black cef_upgrade_agent.py
```

### Type Hints

Use type hints for function parameters and return values:

```python
def download_cef(self, version: str, download_dir: Path, dry_run: bool = False) -> Optional[Path]:
    """Download CEF binary distribution."""
    pass
```

### Documentation

- **All classes** should have docstrings explaining their purpose
- **All public methods** should have docstrings with:
  - Brief description
  - Args section (if applicable)
  - Returns section (if applicable)
  - Raises section (if applicable)
  - Example usage (for complex methods)

Example:
```python
def check_version(self, version: str) -> Tuple[bool, List[Dict]]:
    """
    Check if a CEF version has known vulnerabilities.
    
    Args:
        version: CEF version string to check
        
    Returns:
        Tuple of (has_critical_vulns, vulnerabilities_list)
        
    Raises:
        RequestException: If API call fails
        
    Example:
        >>> checker = VulnerabilityChecker(logger)
        >>> has_critical, vulns = checker.check_version("120.1.10")
    """
    pass
```

## Testing

### Writing Tests

Create test files in a `tests/` directory:

```
tests/
  test_detector.py
  test_downloader.py
  test_installer.py
  test_verifier.py
```

Example test:
```python
import pytest
from pathlib import Path
from cef_upgrade_agent import CEFDetector, Logger

def test_detector_finds_cef():
    """Test that detector can find CEF installations."""
    logger = Logger(Path("temp/test-logs"))
    detector = CEFDetector(logger)
    
    # Test detection logic
    result = detector.detect_cef_in_path("test/fixtures/app-with-cef")
    
    assert result["found"] == True
    assert result["version"] is not None
```

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=cef_upgrade_agent --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_detector.py
```

### Test Coverage

Aim for at least 80% code coverage for new features.

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

- **Format**: `<type>: <subject>`
- **Types**: 
  - `feat`: New feature
  - `fix`: Bug fix
  - `docs`: Documentation changes
  - `style`: Code style changes (formatting, etc.)
  - `refactor`: Code refactoring
  - `test`: Adding or updating tests
  - `chore`: Maintenance tasks

Examples:
```
feat: Add support for ARM64 architecture
fix: Correct version detection for macOS
docs: Update installation instructions
test: Add tests for vulnerability checker
```

### Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Run tests** and ensure they pass
4. **Update CHANGELOG.md** with your changes
5. **Create a pull request** with a clear description:
   - What changes you made
   - Why you made them
   - How to test them
   - Any breaking changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How to test these changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] All tests pass
```

## Reporting Bugs

### Before Reporting

1. **Check existing issues** to avoid duplicates
2. **Test with the latest version**
3. **Gather information**:
   - Operating system and version
   - Python version
   - CEF version you're trying to install
   - Full error message and stack trace
   - Steps to reproduce

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Run command: `python cef_upgrade_agent.py ...`
2. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Python: 3.11.0
- CEF Version: 120.1.10+g3ce3184+chromium-120.0.6099.129

## Error Output
```
Paste full error message here
```

## Additional Context
Any other relevant information
```

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches did you consider?

## Additional Context
Mockups, examples, or references
```

## Platform-Specific Contributions

If you're contributing platform-specific code:

- **Test on the target platform** before submitting
- **Document platform-specific behavior** in code comments
- **Update platform-specific notes** in README.md
- **Consider edge cases** for that platform

## Documentation Contributions

Documentation improvements are always welcome:

- Fix typos and grammar
- Improve clarity and examples
- Add missing information
- Update outdated content
- Translate to other languages

## Questions?

If you have questions about contributing:

- Open an issue with the `question` label
- Check existing discussions
- Review closed issues for similar questions

## Recognition

Contributors will be recognized in:

- The project README
- Release notes
- The CONTRIBUTORS.md file (if we create one)

Thank you for contributing to CEF Upgrade Agent! 🎉
