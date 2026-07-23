# Contributing to ideasphere

Thank you for your interest in contributing!

## Getting Started

1. Fork this repository
2. Clone your fork: `git clone https://github.com/<your-username>/ideasphere.git`
3. Install dependencies: `pip install -e ".[dev]"`
4. Create a branch: `git checkout -b feature/your-feature`

## Development

```bash
# Run tests
python -m pytest tests/ -q

# Run linter
ruff check .

# Format code
ruff format .
```

## Submitting Changes

1. Ensure all tests pass: `python -m pytest tests/ -q`
2. Ensure code passes linting: `ruff check .`
3. Commit with a clear message
4. Push and open a Pull Request

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for function signatures
- Add docstrings for public functions
- Keep functions focused and small

## Reporting Issues

Open an issue with:
- A clear title and description
- Steps to reproduce (if applicable)
- Expected vs actual behavior
