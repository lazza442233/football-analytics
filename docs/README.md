# Documentation Index

Welcome to the Football Analytics Platform documentation! This index follows the [Diátaxis](https://diataxis.fr/) framework, organizing content by purpose and user need.

---

## 🚀 Getting Started (Learning-Oriented)

*Hands-on tutorials for beginners who want to learn by doing.*

| Document | Purpose | Time |
|----------|---------|------|
| [Quick Start Guide](quickstart.md) | Get up and running in 10 minutes | 10 min |
| [Setup & Installation](setup_guide.md) | Complete environment setup for development | 20 min |
| [Data Ingestion Tutorial](data_ingestion.md) | Learn how to load StatsBomb data | 15 min |

**Start here if:** You're new to the project and want to see it in action quickly.

---

## 📖 Understanding the System (Explanation-Oriented)

*Conceptual guides that explain how and why things work.*

| Document | Purpose |
|----------|---------|
| [Doppelgänger Architecture](dev/arch_doppelganger.md) | How the player similarity engine works |
| [Frontend Dashboard Architecture](dev/arch_frontend_dashboard.md) | React app design and component structure |
| [Project Structure](project_structure.md) | How the codebase is organized |

**Start here if:** You want to understand the system's design and architecture before contributing.

---

## 🔧 How-To Guides (Task-Oriented)

*Step-by-step instructions for accomplishing specific tasks.*

| Document | Purpose |
|----------|---------|
| [Troubleshooting Guide](troubleshooting.md) | Solve common problems and errors |
| [Contributing Guide](../CONTRIBUTING.md) | Add features, fix bugs, submit PRs |
| [Testing Guide](dev/testing.md) *(coming soon)* | Write and run tests |
| [Deployment Guide](dev/deployment.md) *(coming soon)* | Deploy to production |

**Start here if:** You have a specific problem to solve or task to complete.

---

## 📚 Reference (Information-Oriented)

*Technical descriptions and specifications for looking up details.*

| Document | Purpose |
|----------|---------|
| [API Documentation](http://localhost:8000/docs) | Interactive OpenAPI spec (requires running server) |
| [Database Schema](data_ingestion.md#current-schema-architecture) | Table definitions and relationships |
| [Configuration Reference](setup_guide.md#environment-variables-reference) | Environment variables and settings |
| [CLI Reference](data_ingestion.md#command-structure) | Ingestion script options |

**Start here if:** You need to look up specific technical details.

---

## 🗂️ Documentation by Topic

### Installation & Setup
- [Quick Start Guide](quickstart.md) - Fast setup for trying the platform
- [Setup & Installation](setup_guide.md) - Complete development environment setup
- [Troubleshooting](troubleshooting.md) - Common installation issues

### Data & Ingestion
- [Data Ingestion Tutorial](data_ingestion.md) - Load StatsBomb data
- [Database Schema Reference](data_ingestion.md#current-schema-architecture) - Table structures

### Architecture & Design
- [README Architecture Section](../README.md#-architecture) - System overview with diagrams
- [Doppelgänger Specification](dev/arch_doppelganger.md) - ML engine design
- [Frontend Architecture](dev/arch_frontend_dashboard.md) - React dashboard

### Development
- [Contributing Guide](../CONTRIBUTING.md) - Code standards and PR process
- [Project Structure](project_structure.md) - Codebase organization
- [Testing Guide](dev/testing.md) *(coming soon)* - Test patterns

### Operations
- [Troubleshooting](troubleshooting.md) - Debugging and problem solving
- [Deployment Guide](dev/deployment.md) *(coming soon)* - Production deployment

---

## 🎯 Quick Links by Role

### 👨‍💻 New Developer

1. [Quick Start Guide](quickstart.md) - See it work
2. [Setup & Installation](setup_guide.md) - Set up your environment
3. [Project Structure](project_structure.md) - Understand the codebase
4. [Contributing Guide](../CONTRIBUTING.md) - Make your first contribution

### 📊 Data Analyst

1. [Quick Start Guide](quickstart.md) - Get the system running
2. [Data Ingestion Tutorial](data_ingestion.md) - Load different competitions
3. [API Documentation](http://localhost:8000/docs) - Query player statistics
4. [Doppelgänger Guide](dev/arch_doppelganger.md) - Understand similarity metrics

### 🏗️ DevOps Engineer

1. [Setup Guide](setup_guide.md) - Understand the stack
2. [Configuration Reference](setup_guide.md#environment-variables-reference) - Environment setup
3. [Troubleshooting](troubleshooting.md) - Common infrastructure issues
4. [Deployment Guide](dev/deployment.md) *(coming soon)* - Production deployment

### 🎨 Frontend Developer

1. [Quick Start Guide](quickstart.md) - Run the full stack
2. [Frontend Architecture](dev/arch_frontend_dashboard.md) - Component design
3. [API Documentation](http://localhost:8000/docs) - Backend endpoints
4. [Contributing Guide](../CONTRIBUTING.md) - Submit UI changes

---

## 📝 Documentation Standards

Our documentation follows these principles:

- **Clarity**: Written in plain language, avoiding jargon
- **Completeness**: Every feature is documented
- **Maintainability**: Updated with every code change
- **Accessibility**: Organized by user need, not internal structure

### Contributing to Docs

Documentation lives in:
- `README.md` - Project overview and quick start
- `docs/` - Detailed guides and specifications
- `CLAUDE.md` - Claude Code integration instructions
- `CONTRIBUTING.md` - Contribution guidelines

**Improvements welcome!** If you find unclear documentation, please:

1. Open an issue describing what's confusing
2. Submit a PR with improvements
3. Ask in [GitHub Discussions](https://github.com/lazza442233/football-analytics/discussions)

---

## 🔍 Can't Find What You Need?

### Search Tips

1. **Use GitHub search**: Search across all docs with `repo:lazza442233/football-analytics <your query>`
2. **Check the README**: [README.md](../README.md) has a comprehensive overview
3. **Browse by topic**: Use the [topic index](#-documentation-by-topic) above
4. **Look at code comments**: Well-commented code in `src/`

### Still Stuck?

- 💬 **Ask a Question**: [GitHub Discussions](https://github.com/lazza442233/football-analytics/discussions)
- 🐛 **Report Missing Docs**: [Open an Issue](https://github.com/lazza442233/football-analytics/issues/new)
- 📧 **Email Maintainers**: maintainers@football-analytics.dev

---

## 📆 Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| README.md | ✅ Complete | Feb 2026 |
| Quick Start Guide | ✅ Complete | Feb 2026 |
| Setup Guide | ✅ Complete | Feb 2026 |
| Troubleshooting | ✅ Complete | Feb 2026 |
| Data Ingestion | ✅ Complete | Feb 2026 |
| Project Structure | ✅ Complete | Feb 2026 |
| Doppelgänger Spec | ✅ Complete | Feb 2026 |
| Frontend Arch | ✅ Complete | Feb 2026 |
| Contributing | ✅ Complete | Feb 2026 |
| Testing Guide | 🚧 In Progress | - |
| Deployment Guide | 📋 Planned | - |
| API Reference | ✅ Auto-generated | Always current |

---

<p align="center">
  <i>Documentation built with ❤️ for the football analytics community</i>
</p>
