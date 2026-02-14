# Contributing to Football Analytics

First off, thank you for considering contributing to the Football Analytics Platform! It's people like you that make this project a great tool for the football analytics community.

---

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and inclusive environment. By participating, you are expected to uphold this standard.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/lazza442233/football-analytics/issues) to avoid duplicates.

**When filing a bug report, include:**

- **Clear title**: Descriptive one-liner
- **Environment**: OS, Python version, Docker version
- **Steps to reproduce**: Numbered list
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant error messages or stack traces
- **Screenshots**: If applicable

**Example:**

```markdown
### Bug: API returns 500 on player search with special characters

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.12.1
- Docker: 24.0.7

**Steps to Reproduce:**
1. Start API server
2. Navigate to http://localhost:8000/docs
3. Search for player "Müller"
4. Observe 500 error

**Expected:** Return player results
**Actual:** 500 Internal Server Error

**Logs:**
```
UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3
```
```

---

## Development Process

### 1. Fork & Clone

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/football-analytics.git
cd football-analytics

# Add upstream remote
git remote add upstream https://github.com/lazza442233/football-analytics.git
```

### 2. Create a Branch

Use conventional branch naming:

```bash
# Features
git checkout -b feat/add-expected-threat-metric

# Bug fixes
git checkout -b fix/player-search-encoding

# Documentation
git checkout -b docs/update-api-reference

# Tests
git checkout -b test/add-doppelganger-coverage
```

### 3. Set Up Development Environment

```bash
# Install dependencies
poetry install

# Setup pre-commit hooks
poetry run pre-commit install

# Start infrastructure
docker compose up -d postgres redis

# Run migrations
poetry run alembic upgrade head
```

### 4. Make Your Changes

**Code Standards:**

- **Python Version**: 3.12+
- **Line Length**: 88 characters (Black-compatible)
- **Linter**: Ruff with E, F, I rules
- **Type Hints**: Use type annotations for function signatures
- **Docstrings**: Google style for public APIs

**Before committing, ensure:**

```bash
# Linting passes
poetry run ruff check .

# Tests pass
poetry run pytest

# Type checking passes (if applicable)
poetry run mypy src/

# Coverage remains above 78%
poetry run pytest --cov=src --cov-report=term-missing
```

### 5. Write Tests

**All new features must include tests.**

- Unit tests for business logic
- Integration tests for API endpoints
- Use async fixtures from `conftest.py`

**Example Test:**

```python
# tests/analytics/test_new_feature.py
import pytest
from src.analytics.new_feature import calculate_metric

@pytest.mark.asyncio
async def test_calculate_metric(async_session):
    """Test that metric calculation is accurate."""
    result = await calculate_metric(player_id=123, season_id=27)
    assert result["metric_value"] > 0
    assert "explanation" in result
```

### 6. Commit Your Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `chore`: Build process or tooling

**Examples:**

```bash
feat(doppelganger): add expected threat (xT) to feature vector

Integrate xT calculations from StatsBomb event data into the
player similarity engine. This metric captures progressive
passing and carrying contributions.

Closes #42

---

fix(api): handle unicode characters in player search

Players with accented names (Müller, Griezmann) were causing
encoding errors. Now properly decode UTF-8 in search queries.

Fixes #58

---

docs(readme): add troubleshooting section

Users were frequently asking about Docker connection issues.
Added comprehensive troubleshooting guide covering common errors.

---

test(ingestion): increase coverage for edge cases

Added tests for:
- Empty match data
- Invalid competition IDs
- Network timeout scenarios

Coverage increased from 76% to 82%.
```

**Commit:**

```bash
git add .
git commit -m "feat(doppelganger): add expected threat (xT) to feature vector"
```

### 7. Push & Create Pull Request

```bash
# Push to your fork
git push origin feat/add-expected-threat-metric

# Create PR on GitHub
```

**Pull Request Guidelines:**

- **Title**: Match your commit message format
- **Description**: Explain what and why (not how)
- **Link Issues**: Use "Closes #123" or "Fixes #456"
- **Screenshots**: For UI changes
- **Checklist**: Ensure all items are checked

**PR Template:**

```markdown
## Description
Brief description of the change.

## Motivation
Why is this change needed? What problem does it solve?

## Changes Made
- Added xT calculation function
- Integrated xT into feature engineering pipeline
- Updated API response schema
- Added unit tests

## Testing
- [ ] Unit tests pass (`pytest`)
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Linting passes (`ruff check`)

## Screenshots
_If applicable, add screenshots of UI changes_

## Related Issues
Closes #42

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

---

## Code Review Process

### For Contributors

- Respond to feedback within 7 days
- Make requested changes in new commits (don't force-push)
- Mark conversations as resolved when addressed

### For Reviewers

- Review within 3 business days
- Be constructive and specific
- Approve when all feedback is addressed

---

## Coding Conventions

### Python Style

```python
# Good: Clear, typed, documented
async def calculate_player_similarity(
    player_id: int,
    season_id: int,
    limit: int = 5,
    session: AsyncSession = Depends(get_session)
) -> list[SimilarityMatch]:
    """Find players with similar statistical profiles.

    Args:
        player_id: Target player's unique identifier
        season_id: Season to compare within
        limit: Maximum number of matches to return
        session: Database session

    Returns:
        List of similar players with similarity scores

    Raises:
        PlayerNotFoundError: If player_id doesn't exist
    """
    # Implementation
    pass

# Bad: No types, no docstring, unclear naming
async def get_stuff(pid, sid, lim=5):
    pass
```

### Async Patterns

```python
# Good: Proper async/await usage
async def fetch_events(match_id: int) -> list[Event]:
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Event).where(Event.match_id == match_id)
        )
        return result.scalars().all()

# Bad: Blocking call in async function
async def fetch_events(match_id: int) -> list[Event]:
    events = sb.events(match_id=match_id)  # Blocks event loop!
    return events

# Correct: Wrap blocking calls
async def fetch_events(match_id: int) -> list[Event]:
    events = await asyncio.to_thread(sb.events, match_id=match_id)
    return events
```

### Database Patterns

```python
# Good: Context manager, explicit query
async def get_player(player_id: int) -> Player | None:
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Player).where(Player.id == player_id)
        )
        return result.scalar_one_or_none()

# Bad: Session as instance variable
class PlayerService:
    def __init__(self):
        self.session = AsyncSession(engine)  # Don't do this!
```

### Testing Patterns

```python
# Good: Descriptive test name, isolated, async
@pytest.mark.asyncio
async def test_similarity_search_returns_top_k_matches(async_session):
    """Test that similarity search respects the limit parameter."""
    # Arrange
    player = await create_test_player(async_session, name="Test Player")

    # Act
    matches = await doppelganger_engine.find_similar(
        player_id=player.id,
        limit=3
    )

    # Assert
    assert len(matches) <= 3
    assert all(m["similarity_score"] > 0.7 for m in matches)

# Bad: Vague name, no async
def test_search():
    result = search(123)
    assert result
```

---

## Documentation Standards

### Docstrings (Google Style)

```python
def calculate_per_90(value: float, minutes_played: int) -> float:
    """Normalize a statistic to per-90-minute rate.

    Args:
        value: The raw count (e.g., total passes)
        minutes_played: Total minutes the player was on the pitch

    Returns:
        The per-90 rate (e.g., passes per 90 minutes)

    Raises:
        ValueError: If minutes_played is zero or negative

    Example:
        >>> calculate_per_90(value=50, minutes_played=450)
        10.0
    """
    if minutes_played <= 0:
        raise ValueError("minutes_played must be positive")
    return (value / minutes_played) * 90
```

### Inline Comments

```python
# Good: Explain why, not what
# Apply position-specific feature masking to prevent
# goalkeeper metrics from influencing outfield comparisons
features = mask_features_by_position(features, position_group)

# Bad: Comment states the obvious
# Loop through players
for player in players:
    ...
```

---

## Project-Specific Guidelines

### Adding New Metrics

When adding a new statistical metric:

1. **Define in config**: Add to `src/analytics/doppelganger/config.py`
2. **Extract in ETL**: Update `src/analytics/doppelganger/etl.py`
3. **Normalize if needed**: Add to `NORMALIZE_PER_90_COLS`
4. **Update tests**: Add test cases covering edge cases
5. **Document**: Update API docs and README

### Database Migrations

```bash
# 1. Modify models
# Edit src/models.py

# 2. Generate migration
poetry run alembic revision --autogenerate -m "add player nationality"

# 3. Review generated file
cat migrations/versions/xxx_add_player_nationality.py

# 4. Test migration
poetry run alembic upgrade head
poetry run alembic downgrade -1
poetry run alembic upgrade head

# 5. Commit both model changes and migration
git add src/models.py migrations/versions/xxx_add_player_nationality.py
git commit -m "feat(models): add nationality field to player"
```

---

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/lazza442233/football-analytics/discussions)
- **Real-time Chat**: [Discord Server](#) _(if applicable)_
- **Email**: maintainers@football-analytics.dev

---

## Recognition

Contributors will be recognized in:

- [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Release notes
- Project README

---

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers this project.

---

<p align="center">
  <i>Thank you for making Football Analytics better! ⚽</i>
</p>
