## Run tests whenever a change to runnable code was made

Always run tests after making changes to the codebase:

```bash
uv run pytest tests/ -v
```

## Deployment

**Before making any deployment-related changes**, read `deployment.md` for the current production setup.

**After changing the codebase**, check if `deployment.md` needs to be updated. Changes that may require documentation updates:

- New environment variables
- Changes to the build process
- New services or dependencies
- Modified nginx or systemd configuration
- Database schema changes
- New API endpoints that affect the frontend

## Scientific Code Guidelines

This is a scientific codebase. Errors should never be silently caught or suppressed. Any error should crash the program rather than be handled silently. This ensures:

- Bugs are discovered immediately rather than producing incorrect results
- Debugging is straightforward with clear stack traces
- Results are trustworthy and reproducible

Do not use broad `try/except` blocks that swallow exceptions. If error handling is necessary, be explicit about which specific exceptions are expected and why.