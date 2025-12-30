# Contributing Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation Updates](#documentation-updates)

## Getting Started

Thank you for contributing to QuantumNest! This guide will help you get started.

### Prerequisites

- Git
- Python 3.10+
- Node.js 18+
- Docker (recommended)
- Familiarity with FastAPI, React, and Solidity

### Fork and Clone

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/abrar2030/QuantumNest.git
cd QuantumNest

# Add upstream remote
git remote add upstream https://github.com/abrar2030/QuantumNest.git
```

### Setup Development Environment

```bash
# Run setup script
./setup_quantumnest_env.sh

# Verify installation
./scripts/run_all_tests.sh
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, documented code
- Follow code style guidelines
- Add tests for new features
- Update documentation

### 3. Test Your Changes

```bash
# Run linters
./scripts/lint-all.sh

# Run tests
./scripts/run_all_tests.sh

# Test specific component
./scripts/run_all_tests.sh backend
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add portfolio risk metrics

- Add Sharpe ratio calculation
- Add max drawdown computation
- Update portfolio performance endpoint"
```

**Commit Message Format:**

```
<type>: <subject>

<body>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

## Code Standards

### Python (Backend)

**Style Guide**: PEP 8

```python
# Good
def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for given returns.

    Args:
        returns: List of portfolio returns
        risk_free_rate: Risk-free rate (default: 2%)

    Returns:
        float: Sharpe ratio
    """
    excess_returns = [r - risk_free_rate for r in returns]
    return np.mean(excess_returns) / np.std(excess_returns)
```

**Linting:**

```bash
# Format code
black code/backend/

# Check style
flake8 code/backend/

# Type checking
mypy code/backend/
```

### TypeScript (Frontend)

**Style Guide**: Airbnb TypeScript Style

```typescript
// Good
interface PortfolioProps {
    portfolioId: number;
    onUpdate: (portfolio: Portfolio) => void;
}

export const PortfolioCard: React.FC<PortfolioProps> = ({ portfolioId, onUpdate }) => {
    // Component implementation
};
```

**Linting:**

```bash
# Format code
npm run format

# Check style
npm run lint

# Type checking
npm run type-check
```

### Solidity (Smart Contracts)

**Style Guide**: Solidity Style Guide

```solidity
// Good
contract TokenizedAsset is ERC20, Ownable {
    /// @notice Update asset valuation
    /// @param newValue New asset value in cents
    function updateAssetValue(uint256 newValue) external onlyOwner {
        uint256 oldValue = assetValue;
        assetValue = newValue;

        emit AssetRevalued(oldValue, newValue, block.timestamp);
    }
}
```

## Testing Requirements

### Unit Tests

All new features must include unit tests.

**Python Example:**

```python
# tests/test_portfolio.py
def test_calculate_performance():
    portfolio = create_test_portfolio()
    performance = calculate_performance(portfolio)

    assert performance["return_percentage"] > 0
    assert "sharpe_ratio" in performance
```

**TypeScript Example:**

```typescript
// __tests__/Portfolio.test.tsx
describe('PortfolioCard', () => {
  it('renders portfolio data correctly', () => {
    render(<PortfolioCard portfolioId={1} />);
    expect(screen.getByText('Growth Portfolio')).toBeInTheDocument();
  });
});
```

### Integration Tests

Test API endpoints and component interactions.

```python
def test_portfolio_creation_flow():
    # Create user
    user = create_test_user()

    # Create portfolio
    response = client.post(
        "/portfolio/",
        headers=get_auth_headers(user),
        json={"name": "Test Portfolio"}
    )

    assert response.status_code == 201
    assert "id" in response.json()
```

### Test Coverage

Maintain minimum 80% code coverage:

```bash
# Backend
pytest --cov=app tests/

# Frontend
npm test -- --coverage
```

## Pull Request Process

### 1. Update Your Branch

```bash
# Fetch upstream changes
git fetch upstream

# Rebase on main
git rebase upstream/main

# Resolve conflicts if any
```

### 2. Push Changes

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

- Go to GitHub and create PR
- Fill out PR template
- Link related issues
- Request reviews

### PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No new warnings generated
```

### 4. Code Review

- Address review comments
- Update code as needed
- Push updates to same branch

### 5. Merge

Once approved, maintainers will merge your PR.

## Documentation Updates

When updating documentation:

### File Structure

```
docs/
├── README.md              # Update when adding new docs
├── API.md                 # Update for API changes
├── USAGE.md               # Update for usage changes
├── CONFIGURATION.md       # Update for config changes
└── examples/              # Add examples for new features
```

### Documentation Standards

- Clear, concise language
- Code examples where applicable
- Tables for structured data
- Internal links to related docs
- No broken external links

### Building Documentation

```bash
# Validate markdown
npm run validate:docs

# Check links
npm run check:links

# Preview docs
npm run docs:serve
```
