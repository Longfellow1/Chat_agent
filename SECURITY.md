# Security Guidelines

## API Keys & Secrets Management

### Never Commit Secrets

- Never commit `.env.agent`, `.env.local`, or any files containing API keys
- These files are in `.gitignore` - respect it
- Use `.env.agent.example` as a template

### Setup Instructions

1. Copy the example file:
```bash
cp .env.agent.example .env.agent
```

2. Fill in your actual API keys:
```bash
# Edit .env.agent with your real credentials
ALPHA_VANTAGE_API_KEY=your_actual_key
TAVILY_API_KEY=your_actual_key
# ... etc
```

3. Never commit `.env.agent`:
```bash
# Verify it's in .gitignore
cat .gitignore | grep ".env.agent"
```

### Required API Keys

| Service | Key | Source |
|---------|-----|--------|
| Alpha Vantage | ALPHA_VANTAGE_API_KEY | https://www.alphavantage.co |
| Tavily | TAVILY_API_KEY | https://tavily.com |
| Baidu Qianfan | BAIDU_QIANFAN_API_KEY | https://cloud.baidu.com |
| QWeather | QWEATHER_API_KEY | https://www.qweather.com |
| Amap | AMAP_API_KEY | https://lbs.amap.com |
| Baidu Maps | BAIDU_MAP_API_KEY | https://lbsyun.baidu.com |

## Environment Variables

Load from `.env.agent` at runtime:

```python
import os
from dotenv import load_dotenv

load_dotenv('.env.agent')
api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
```

## Code Review Checklist

Before committing:
- [ ] No hardcoded API keys in code
- [ ] No credentials in strings or comments
- [ ] All secrets use environment variables
- [ ] `.env.agent` is in `.gitignore`
- [ ] Example files use placeholder values

## If You Accidentally Commit Secrets

1. **Immediately revoke the compromised key** in the service's dashboard
2. **Generate a new key**
3. **Update `.env.agent` locally** with the new key
4. **Contact maintainers** to remove from git history

## GitHub Security

- Repository is private
- Only authorized collaborators have access
- Branch protection rules enforce code review
- Secrets scanning is enabled

## Deployment Security

- Use GitHub Secrets for CI/CD
- Never log sensitive data
- Rotate keys regularly
- Monitor API usage for anomalies

## Questions?

Contact the security team or maintainers for guidance.
