# Testing Guide

## Test Suite Overview

The Dynevi test suite is designed to run **without making real API calls** by default. All tests use mock mode to ensure:
- ✅ Fast execution (no network delays)
- ✅ No API costs
- ✅ Reliable, deterministic results
- ✅ Can run offline

## Running Tests

### Standard Tests (Mock Mode)

```bash
# Run all tests (uses mock mode)
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_services.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Real API Tests (Optional)

If you want to test with **real API calls** (and see them in LangSmith):

```bash
# 1. Set your API key
export GEMINI_API_KEY=your_real_key_here

# 2. Optionally enable LangSmith tracing
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=your_langsmith_key
export LANGSMITH_PROJECT=dynevi-tests

# 3. Run real API tests
uv run pytest tests/test_real_api.py -v

# Or run all tests including real API tests
uv run pytest tests/ -v
```

**Note**: Real API tests are marked with `@pytest.mark.real_api`. To skip them:

```bash
# Skip real API tests (default behavior)
uv run pytest tests/ -m "not real_api" -v
```

## Test Structure

### Mock Tests (Default)
- **Location**: `tests/test_*.py` (except `test_real_api.py`)
- **Mode**: `MOCK_GEMINI=true`, `MOCK_TTS=true`
- **API Calls**: ❌ None (uses mock responses)
- **LangSmith Traces**: ❌ None (no real calls to trace)

### Real API Tests (Optional)
- **Location**: `tests/test_real_api.py`
- **Mode**: `MOCK_GEMINI=false` (requires real API key)
- **API Calls**: ✅ Real Gemini API calls
- **LangSmith Traces**: ✅ Yes, if `LANGSMITH_TRACING=true`

## Viewing Traces in LangSmith

### For Real API Tests

1. **Enable tracing**:
   ```bash
   export LANGSMITH_TRACING=true
   export LANGSMITH_API_KEY=your_key
   export LANGSMITH_PROJECT=dynevi-tests
   ```

2. **Run real API tests**:
   ```bash
   uv run pytest tests/test_real_api.py -v
   ```

3. **View in LangSmith**:
   - Go to [https://smith.langchain.com](https://smith.langchain.com)
   - Navigate to "dynevi-tests" project
   - See all API calls from your tests!

### What You'll See

- **Test API calls**: Each `generate_response()` call
- **Performance**: Duration, token usage
- **Inputs/Outputs**: Prompts and responses
- **Metadata**: Model, circuit breaker state
- **Errors**: Any failures with full context

## Test Fixtures

### `mock_env_vars` (Default)
Sets up mock mode for all tests. No real API calls.

### `real_api_env_vars` (Optional)
Sets up real API mode. Requires `GEMINI_API_KEY` in environment.

## Best Practices

1. **Default to Mock Tests**: Use mock tests for development and CI/CD
2. **Real API Tests Sparingly**: Only run real API tests when:
   - Testing new features that need real responses
   - Validating API integration
   - Debugging production issues
3. **Use LangSmith for Debugging**: Enable tracing when debugging real API issues
4. **Separate Projects**: Use different LangSmith projects for:
   - `dynevi-dev` - Development
   - `dynevi-tests` - Test runs
   - `dynevi-prod` - Production

## CI/CD Integration

For CI/CD pipelines, use mock tests:

```yaml
# Example GitHub Actions
- name: Run tests
  run: uv run pytest tests/ -m "not real_api" -v
  env:
    MOCK_GEMINI: "true"
    MOCK_TTS: "true"
```

## Troubleshooting

### Tests Failing with Real API

- Check `GEMINI_API_KEY` is set correctly
- Verify API key has sufficient quota
- Check network connectivity
- Review error messages in test output

### No Traces in LangSmith

- Verify `LANGSMITH_TRACING=true`
- Check `LANGSMITH_API_KEY` is valid
- Ensure you're running real API tests (not mock)
- Wait a few seconds for traces to appear

### Mock Tests Failing

- Check `MOCK_GEMINI=true` is set
- Verify test fixtures are applied
- Review test logs for errors

