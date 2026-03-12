# Contributing Guide

## Development Setup

### Prerequisites
- Python 3.10+
- Git
- Virtual environment

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Longfellow1/Chat_agent.git
cd Chat_agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## Code Style

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use meaningful variable names

### Formatting

```bash
# Format code
black agent_service/ tests/

# Check linting
flake8 agent_service/ tests/

# Type checking
mypy agent_service/
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest --cov=agent_service tests/

# Specific test file
pytest tests/unit/test_router.py

# Specific test
pytest tests/unit/test_router.py::test_intent_classification
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names
- Include docstrings explaining test purpose
- Mock external dependencies

Example:
```python
def test_router_classification():
    """Test intent classification with known query."""
    router = UnifiedRouter()
    result = router.classify("What's the weather?")
    assert result.intent == "weather"
```

## Commit Guidelines

- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Format: `type: description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements

Example:
```
feat: add weather intent classification
fix: resolve router timeout issue
docs: update LLM configuration guide
```

## Pull Request Process

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit
3. Push to your fork
4. Create pull request with clear description
5. Ensure all tests pass
6. Request review from maintainers

## Project Structure Guidelines

### Adding New Modules

```
agent_service/domain/new_feature/
├── __init__.py
├── intent.py          # Intent detection
├── engine.py          # Core logic
├── schema.py          # Data models
└── templates.py       # Response templates
```

### Adding New Providers

```
agent_service/infra/tool_clients/providers/
├── new_provider.py    # Provider implementation
└── __init__.py        # Export provider
```

## Documentation

- Update relevant docs when adding features
- Include docstrings in all modules
- Add examples for new functionality
- Update README if adding major features

## Performance Considerations

- Profile code before optimization
- Use async/await for I/O operations
- Cache expensive computations
- Monitor memory usage in long-running processes

## Security

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Sanitize external data
- Review dependencies for vulnerabilities

## Questions?

- Check existing documentation
- Review similar implementations
- Ask in pull request comments
- Contact maintainers

Thank you for contributing!
