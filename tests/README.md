# Testing Guide

This directory contains comprehensive tests for the auto-commit project.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and fixtures
├── test_config.py           # Configuration module tests
├── test_config_manager.py   # Configuration manager tests
├── test_git_ops.py          # Git operations tests
├── test_review_queue.py     # Review queue tests
├── test_integration.py      # Integration tests
└── README.md               # This file
```

## Test Categories

### Unit Tests
Test individual components in isolation:
- Configuration loading and validation
- File filtering logic
- Git operations
- Review queue functionality
- LLM communication
- UI backend endpoints

### Integration Tests
Test how components work together:
- File watching to commit flow
- Configuration hierarchy resolution
- Worker pool processing
- Error handling across components
- Performance under load

## Running Tests

### Prerequisites
```bash
pip install -r requirements.txt
```

### Quick Test Run
```bash
# Run all tests
pytest

# Run only unit tests
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html
```

### Using the Test Runner
```bash
# Run all test categories
python run_tests.py

# Run specific category
python run_tests.py --category unit
python run_tests.py --category integration
python run_tests.py --category coverage
```

### Using Make Commands
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run with coverage
make coverage

# Run all quality checks
make quality
```

## Test Configuration

### Pytest Configuration
- Configuration in `pytest.ini`
- Custom markers for test categorization
- Coverage settings and thresholds
- Output formatting options

### Fixtures
Common fixtures available in `conftest.py`:
- `temp_dir`: Temporary directory for testing
- `temp_git_repo`: Temporary git repository
- `sample_config`: Sample application configuration
- `config_manager`: ConfigurationManager instance
- `review_queue`: ReviewQueue instance
- `mock_git_repo`: Mocked GitRepo for testing
- `sample_files`: Sample test files
- `mock_llm_response`: Mocked LLM API response
- `mock_linear_api`: Mocked Linear API calls

## Writing Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>_<scenario>`

### Example Test Structure
```python
class TestMyComponent:
    """Test cases for MyComponent class."""
    
    def test_basic_functionality(self, fixture_name):
        """Test basic functionality works correctly."""
        # Arrange
        component = MyComponent()
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result is not None
    
    def test_error_handling(self, fixture_name):
        """Test error handling scenarios."""
        component = MyComponent()
        
        with pytest.raises(ValueError):
            component.do_invalid_operation()
```

### Mocking Guidelines
- Use `unittest.mock` for external dependencies
- Mock at the boundary of your system
- Prefer dependency injection for testability
- Use fixtures for complex mock setups

### Integration Test Guidelines
- Mark with `@pytest.mark.integration`
- Test realistic scenarios
- Use temporary directories/databases
- Clean up resources after tests

## Code Coverage

### Coverage Requirements
- Minimum 80% code coverage required
- All new code should have tests
- Critical paths must be fully covered

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Coverage Configuration
- Configuration in `setup.cfg`
- Excludes test files and __init__.py
- Excludes standard exception patterns

## Continuous Integration

### GitHub Actions
- Automated testing on push/PR
- Multiple Python versions tested
- Code quality checks included
- Coverage reporting to Codecov

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Quality Checks

### Linting
```bash
flake8 src/ tests/
```

### Type Checking
```bash
mypy src/
```

### Code Formatting
```bash
# Check formatting
black --check src/ tests/
isort --check-only src/ tests/

# Apply formatting
black src/ tests/
isort src/ tests/
```

### Security Checks
```bash
bandit -r src/
safety check
```

## Performance Testing

### Benchmark Tests
```bash
# Run performance benchmarks
pytest --benchmark-only
```

### Load Testing
- Test with large numbers of files
- Test concurrent access scenarios
- Monitor memory usage and performance

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Database Locks**: Tests may fail if database files are locked
3. **Git Configuration**: Integration tests need git user configuration
4. **Temporary Files**: Clean up temp files between test runs

### Debug Mode
```bash
# Run tests with verbose output
pytest -v -s

# Run specific test with debugging
pytest -v -s tests/test_module.py::TestClass::test_method

# Drop into debugger on failure
pytest --pdb
```

### Test Data
- Use fixtures for consistent test data
- Avoid hardcoded paths or values
- Clean up test artifacts after runs

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Test names should describe what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Edge Cases**: Test boundary conditions and error cases
5. **Documentation**: Document complex test scenarios
6. **Performance**: Keep tests fast and focused
7. **Maintenance**: Update tests when code changes

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Add integration tests for new workflows
4. Update documentation as needed
5. Check code coverage remains above threshold

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Mock Library Guide](https://docs.python.org/3/library/unittest.mock.html) 