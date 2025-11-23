# LangSmith Setup Guide

## Quick Setup

1. **Get your LangSmith API key**:
   - Sign up at [https://smith.langchain.com](https://smith.langchain.com)
   - Go to Settings → API Keys
   - Create a new API key

2. **Set environment variables**:
   ```bash
   export LANGSMITH_TRACING=true
   export LANGSMITH_API_KEY=your_api_key_here
   export LANGSMITH_PROJECT=dynevi  # Optional, defaults to "dynevi"
   ```

3. **Run your tests or application**:
   ```bash
   # For tests
   uv run pytest tests/test_real_api.py -v
   
   # For application
   python main.py
   ```

4. **View traces**:
   - Go to [https://smith.langchain.com](https://smith.langchain.com)
   - Navigate to your project
   - See all API calls!

## How It Works

### Automatic Tracing with @traceable

The `generate_response` method in `GeminiService` is decorated with `@traceable`, which automatically:
- Captures function inputs and outputs
- Records execution time
- Sends traces to LangSmith

### Manual Tracing

For other operations, we use `trace_api_call()` which creates RunTree objects in LangSmith.

## Troubleshooting

### Traces Not Appearing

1. **Check environment variables**:
   ```bash
   echo $LANGSMITH_TRACING
   echo $LANGSMITH_API_KEY
   ```

2. **Check logs**:
   Look for messages like:
   - `"LangSmith tracing enabled"` ✅
   - `"Traced API call to LangSmith"` ✅
   - `"LangSmith tracing not enabled"` ❌

3. **Verify API key**:
   - Make sure your API key is valid
   - Check it's set in the environment before running

4. **Check project name**:
   - Make sure the project exists in LangSmith
   - Or it will be created automatically

5. **Wait a few seconds**:
   - Traces are sent asynchronously
   - May take 5-10 seconds to appear

### Common Issues

**Issue**: "LangSmith tracing not enabled"
- **Solution**: Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`

**Issue**: Traces appear but are empty
- **Solution**: Check that you're making real API calls (not mock mode)

**Issue**: Only some traces appear
- **Solution**: Make sure `@traceable` decorator is on the function, or `trace_api_call()` is being called

## Advanced Configuration

### Different Projects for Different Environments

```bash
# Development
export LANGSMITH_PROJECT=dynevi-dev

# Testing
export LANGSMITH_PROJECT=dynevi-tests

# Production
export LANGSMITH_PROJECT=dynevi-prod
```

### Disable Tracing

```bash
# Option 1: Unset the flag
unset LANGSMITH_TRACING

# Option 2: Set to false
export LANGSMITH_TRACING=false

# Option 3: Remove API key
unset LANGSMITH_API_KEY
```

## What Gets Traced

### Gemini API Calls
- ✅ Function name: `gemini.generate_response`
- ✅ Inputs: prompt, system_instruction, context, temperature
- ✅ Outputs: response text
- ✅ Metadata: model name, duration, circuit breaker state
- ✅ Errors: Full error details if call fails

### TTS API Calls
- ✅ Function name: `tts.generate_audio`
- ✅ Inputs: text, voice config
- ✅ Outputs: audio file path
- ✅ Metadata: provider, cache hit/miss, duration

## Integration with Tests

When running tests with real API calls:

```bash
# Enable tracing for tests
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=your_key
export LANGSMITH_PROJECT=dynevi-tests

# Run real API tests
uv run pytest tests/test_real_api.py -v
```

All API calls from tests will appear in the `dynevi-tests` project.

## Best Practices

1. **Use separate projects** for dev/test/prod
2. **Monitor costs** - LangSmith has usage limits
3. **Filter traces** - Use project names and metadata to organize
4. **Review regularly** - Check traces to optimize API usage
5. **Disable in production** if not needed (saves costs)

## References

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)
- [Tracing Guide](docs/TRACING.md)

