# 📚 Complete Guide: Managing and Updating the Graphiti Plugin

This guide explains how to manage, update, and maintain the Graphiti plugin for Hermes Agent.

---

## 📋 Table of Contents

1. [Repository Structure](#repository-structure)
2. [Update Workflow](#update-workflow)
3. [Versioning and Releases](#versioning-and-releases)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

---

## 📁 Repository Structure

```
hermes-graphiti-plugin/
├── graphiti/
│   ├── __init__.py          # Main plugin implementation
│   ├── cli.py               # Command-line interface
│   ├── plugin.yaml          # Plugin metadata (version, dependencies)
│   ├── README.md            # Documentation
│   ├── LICENSE              # MIT License
│   └── .gitignore           # Files to exclude from Git
├── docs/                    # Additional documentation (optional)
├── tests/                   # Automated tests (optional)
└── CHANGELOG.md             # Change history
```

---

## 🔄 Update Workflow

### Step 1: Prepare Changes

```bash
# Navigate to plugin directory
cd /home/ubuntu/ai-stack/data/ugugla/config_tools/hermes-graphiti/graphiti

# Check current status
git status

# Make sure you're on main branch
git checkout main

# Update from remote (if working in a team)
git pull origin main
```

### Step 2: Make Changes

Edit necessary files:

```bash
# Example: modify main plugin
nano __init__.py

# Example: update documentation
nano README.md

# Example: update version and metadata
nano plugin.yaml
```

### Step 3: Test Changes

```bash
# Restart Hermes to test
hermes gateway restart

# Check logs for errors
hermes logs | grep GRAPHITI

# Test functionality
# - Start a conversation
# - Verify memory works
# - Test graphiti_search and graphiti_delete_entity tools
```

### Step 4: Commit Changes

```bash
# Add modified files
git add .

# Review what you're about to commit
git status
git diff --cached

# Create descriptive commit
git commit -m "feat: add support for new embedding model

- Added support for 'text-embedding-3-large' embedding model
- Updated default configuration to 1536 dimensions
- Improved Neo4j connection error handling

Fixes: #12"
```

### Step 5: Push to GitHub

```bash
# Upload changes
git push origin main

# If first time or if you changed branch
git push -u origin main
```

---

## 🏷️ Versioning and Releases

### Semantic Versioning (SemVer)

Use `MAJOR.MINOR.PATCH` format:

- **MAJOR**: Breaking changes (e.g., API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version Examples

```yaml
# plugin.yaml
version: 1.0.0  # First stable release
version: 1.0.1  # Bug fix
version: 1.1.0  # New feature
version: 2.0.0  # Breaking change
```

### Creating a Release

```bash
# 1. Update version in plugin.yaml
nano plugin.yaml
# Change: version: 1.0.0 → version: 1.1.0

# 2. Update CHANGELOG.md
nano CHANGELOG.md
# Add changes for this version

# 3. Commit and push
git add plugin.yaml CHANGELOG.md
git commit -m "release: v1.1.0"
git push origin main

# 4. Create a tag
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 5. Create release on GitHub
# Go to: https://github.com/p1s4/hermes-graphiti-plugin/releases
# Click "Draft a new release"
# Tag: v1.1.0
# Title: Release v1.1.0
# Description: Copy from CHANGELOG.md
# Click "Publish release"
```

### CHANGELOG.md Template

Create a `CHANGELOG.md` file in the repository root:

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-27

### Added
- Support for new embedding model 'text-embedding-3-large'
- New parameter `max_search_message_length` to limit search queries

### Changed
- Improved Neo4j connection error handling
- Updated documentation with Docker installation examples

### Fixed
- Fixed bug causing entity duplication during prefetch
- Corrected encoding issue in logs

## [1.0.0] - 2026-05-20

### Added
- Initial Graphiti plugin implementation
- Automatic memory recall (prefetch) support
- Background persistence (sync_turn) support
- `graphiti_search` and `graphiti_delete_entity` tools
- Configuration via `graphiti.json` and `.env`
```

---

## ✨ Best Practices

### 1. Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
style: formatting, semicolons, etc.
refactor: code refactoring
test: add tests
chore: updates to build, dependencies, etc.
```

**Examples:**
```bash
git commit -m "feat: implement Cross-Encoder reranking support"
git commit -m "fix: resolve memory leak in sync_turn"
git commit -m "docs: update README with Docker installation examples"
```

### 2. Branch Strategy

For complex features, use separate branches:

```bash
# Create branch for new feature
git checkout -b feature/cross-encoder-support

# Work on branch
# ... changes ...

# Commit and push
git add .
git commit -m "feat: implement Cross-Encoder reranking"
git push origin feature/cross-encoder-support

# Create Pull Request on GitHub
# After approval, merge to main
```

### 3. Configuration Backup

Before updating, backup user configuration:

```bash
# Backup user configuration
cp $HERMES_HOME/graphiti.json $HERMES_HOME/graphiti.json.backup
cp $HERMES_HOME/.env $HERMES_HOME/.env.backup

# After update, verify configuration is compatible
```

### 4. Test in Development Environment

Before deploying to production:

```bash
# 1. Clone to test directory
git clone https://github.com/p1s4/hermes-graphiti-plugin.git /tmp/test-graphiti

# 2. Install in isolated environment
cd /tmp/test-graphiti/graphiti

# 3. Test with Hermes in debug mode
hermes gateway run --debug

# 4. Check logs
tail -f /var/log/hermes/debug.log | grep GRAPHITI
```

### 5. Documentation

- **Keep README.md updated** with every new feature
- **Add examples** for complex configurations
- **Document breaking changes** prominently
- **Include troubleshooting** for common errors

---

## 🐛 Troubleshooting

### Issue: Git asks for credentials on every push

**Solution: Configure credential caching**

```bash
# Cache for 1 hour
git config --global credential.helper 'cache --timeout=3600'

# Or use SSH (recommended)
git remote set-url origin git@github.com:p1s4/hermes-graphiti-plugin.git
```

### Issue: Merge Conflicts

```bash
# If git pull creates conflicts
git status  # See conflicting files

# Open files and resolve conflicts (look for <<<<<<<, =======, >>>>>>>)
nano conflicting_file.py

# After resolving
git add conflicting_file.py
git commit -m "merge: resolve conflicts"
git push origin main
```

### Issue: Plugin doesn't update after push

**Solution: Force reinstall**

```bash
# Remove plugin
hermes plugin uninstall graphiti

# Reinstall
hermes plugin install https://github.com/p1s4/hermes-graphiti-plugin.git

# Restart Hermes
hermes gateway restart
```

### Issue: Version not updated in plugin.yaml

**Solution: Verify file**

```bash
# Check current version
cat plugin.yaml | grep version

# If not updated, modify it
nano plugin.yaml

# Commit and push
git add plugin.yaml
git commit -m "chore: update version to 1.1.0"
git push origin main
```

---

## 📞 Support and Resources

- **Official Documentation**: [GitHub Wiki](https://github.com/p1s4/hermes-graphiti-plugin/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/p1s4/hermes-graphiti-plugin/issues)
- **Discussions**: [GitHub Discussions](https://github.com/p1s4/hermes-graphiti-plugin/discussions)

---

## 🎯 Release Checklist

- [ ] Tested in development environment
- [ ] Updated version in `plugin.yaml`
- [ ] Updated `CHANGELOG.md`
- [ ] Updated `README.md` (if needed)
- [ ] Commit with descriptive message
- [ ] Push to GitHub
- [ ] Created version tag
- [ ] Published release on GitHub
- [ ] Verified installation from GitHub
- [ ] Tested in production
- [ ] Communicated to users (if needed)

---

**Last updated:** May 27, 2026  
**Document version:** 1.0.0
