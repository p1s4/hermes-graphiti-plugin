# Contributing to Hermes Graphiti Plugin

First off, thank you for considering contributing to the Hermes Graphiti Plugin! It's people like you that make this plugin such a great tool for the community.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Hermes Agent installed and running
- Neo4j database (for testing)
- Access to an LLM API (OpenAI-compatible)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/p1s4/hermes-graphiti-plugin.git
   cd hermes-graphiti-plugin/graphiti
   ```

3. **Set up the upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/hermes-graphiti-plugin.git
   git fetch upstream
   ```

---

## 💡 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what behavior you expected**
- **Include logs and error messages**
- **Include your configuration** (remove sensitive data!)

**Example bug report template:**

```markdown
**Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Configure graphiti.json with '...'
2. Send message '...'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Logs**
```
hermes | [GRAPHITI-PLUGIN] ❌ Error message here
```

**Configuration**
```json
{
  "search_strategy": "balanced",
  "model": "gemini-lite"
}
```

**Environment:**
- Hermes version: 1.0.0
- Python version: 3.12
- OS: Ubuntu 22.04
```

### Suggesting Features

Feature suggestions are tracked as GitHub issues. When creating a feature suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested feature**
- **Explain why this feature would be useful**
- **Provide examples of how it would be used**
- **List any similar features in other tools**

### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through these `good first issue` and `help wanted` issues:

- **Good first issues** - issues that should only require a few lines of code
- **Help wanted issues** - issues that are more involved but don't require deep knowledge of the codebase

---

## 🛠️ Development Setup

### 1. Install Dependencies

```bash
cd graphiti

# Install graphiti-core for development
pip install graphiti-core

# Install development dependencies (if available)
pip install -r requirements-dev.txt
```

### 2. Configure Test Environment

```bash
# Create test configuration
cat > $HERMES_HOME/graphiti.test.json << EOF
{
  "openai_api_url": "http://litellm:4000/v1",
  "model": "gemini-lite",
  "neo4j_uri": "bolt://localhost:7687",
  "search_strategy": "fast"
}
EOF

# Set test environment variables
export GRAPHITI_API_KEY=test-key
export GRAPHITI_NEO4J_PASSWORD=test-password
```

### 3. Run Tests

```bash
# Run existing tests
pytest

# Run with coverage
pytest --cov=graphiti

# Run specific test file
pytest tests/test_memory_provider.py
```

### 4. Test with Hermes

```bash
# Start Hermes in development mode
hermes gateway run --debug

# Monitor logs
tail -f /var/log/hermes/debug.log | grep GRAPHITI
```

---

## 📝 Coding Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused (max 50 lines recommended)

**Example:**

```python
def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent errors in search engine.
    
    Args:
        query: Raw search query string
        
    Returns:
        Sanitized query with special characters removed
        
    Example:
        >>> sanitize_search_query("test@query!")
        'test query'
    """
    sanitized = re.sub(r'[@:\\"()|]', ' ', query)
    return re.sub(r'\s+', ' ', sanitized).strip()
```

### Logging

- Use the provided logger instance
- Follow the log level guidelines:
  - `DEBUG`: Detailed technical information for debugging
  - `INFO`: General operational information
  - `WARNING`: Something unexpected happened, but operation continues
  - `ERROR`: Something went wrong, operation may fail
  - `CRITICAL`: Serious error, application may not continue

**Example:**

```python
logger.info("hermes | [GRAPHITI-PLUGIN] 🔍 Searching graph for query: '%s'", query)
logger.error("hermes | [GRAPHITI-PLUGIN] ❌ Failed to connect to Neo4j: %s", error)
```

### Error Handling

- Catch specific exceptions when possible
- Always log errors with context
- Provide helpful error messages to users
- Clean up resources in finally blocks

**Example:**

```python
try:
    results = await self._graphiti.search_(query, config=search_config)
    return (results.edges, results.nodes)
except Neo4jConnectionError as e:
    logger.error("hermes | [GRAPHITI-PLUGIN] ❌ Neo4j connection failed: %s", e)
    raise
except Exception as e:
    logger.error("hermes | [GRAPHITI-PLUGIN] ❌ Unexpected search error: %s", e)
    raise
```

---

## ✍️ Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning (white-space, formatting, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Examples

```bash
feat(search): add Cross-Encoder reranking support

Implemented Cross-Encoder reranking for improved search quality.
Added new 'quality' search strategy option.
Updated configuration schema to include reranker settings.

Fixes: #42
```

```bash
fix(memory): resolve entity duplication in prefetch

Fixed bug where entities were being duplicated when injected
into the system prompt during automatic memory recall.

Closes: #38
```

```bash
docs(readme): add Docker installation examples

Added comprehensive Docker Compose configuration examples.
Included troubleshooting section for common Docker issues.
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Update documentation** if you changed behavior or added features
2. **Update CHANGELOG.md** with your changes
3. **Ensure all tests pass**
4. **Check code style** with linters
5. **Squash commits** if you have multiple small commits

### Submitting

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub
   - Use a clear title following Conventional Commits
   - Fill out the PR template
   - Link related issues
   - Add screenshots if applicable

3. **Wait for review**
   - Maintainers will review your code
   - Address any feedback
   - Be patient and responsive

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added (if applicable)
- [ ] Tested with Hermes Agent
- [ ] Tested with Neo4j

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No new warnings
```

---

## 🐛 Reporting Bugs

### Before Reporting

- Check if the bug has already been reported
- Test with the latest version
- Try to reproduce in a clean environment

### How to Report

1. **Open an issue** on GitHub
2. **Use the bug report template**
3. **Include all relevant information**
4. **Be responsive to follow-up questions**

---

## 💬 Suggesting Features

### Before Suggesting

- Check if the feature already exists
- Check if it's already been suggested
- Consider if it fits the project scope

### How to Suggest

1. **Open an issue** on GitHub
2. **Use the feature request template**
3. **Provide detailed use cases**
4. **Be open to feedback and discussion**

---

## 📚 Additional Resources

- [Graphiti Core Documentation](https://github.com/getzep/graphiti-core)
- [Hermes Agent Documentation](https://github.com/hermes-agent)
- [Python Best Practices](https://docs.python-guide.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)

---

## 🙏 Thank You!

Your contributions to open source, large or small, make projects like this possible. Thank you for taking the time to contribute.

---

**Questions?** Feel free to open an issue or reach out to the maintainers.
