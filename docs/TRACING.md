# API Call Tracing with LangSmith

This document explains how to visualize and monitor API calls in Dynevi using LangSmith.

## Overview

LangSmith provides comprehensive observability for LLM applications, allowing you to:
- **Visualize API calls** in a web dashboard
- **Track performance metrics** (latency, token usage, costs)
- **Debug issues** with detailed request/response logs
- **Monitor errors** and failures
- **Analyze patterns** across conversations

## Setup

### 1. Get LangSmith API Key

1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Create a new project (or use default)
3. Get your API key from Settings → API Keys

### 2. Configure Environment Variables

Add these to your `.env` file:

```bash
# Enable LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_api_key_here

# Optional: Set project name (defaults to "dynevi")
LANGSMITH_PROJECT=dynevi
```

### 3. Verify Installation

LangSmith is already included as a dependency (via langchain). If you need to install it separately:

```bash
uv add langsmith
```

## Usage

### Automatic Tracing

Once configured, API calls are **automatically traced**:

- **Gemini API calls** - All `generate_response()` calls are traced
- **TTS API calls** - All `generate_audio()` calls are traced
- **Metadata included**: Duration, success/failure, error types, circuit breaker state

### Viewing Traces

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project (default: "dynevi")
3. View traces in real-time or search historical traces

### What Gets Traced

#### Gemini API Calls
- **Inputs**: Prompt (truncated to 100 chars), system instruction presence, context length, temperature
- **Outputs**: Response length
- **Metadata**: Model name, circuit breaker state, duration
- **Errors**: Error type, error message, retry attempts

#### TTS API Calls
- **Inputs**: Text length, voice configuration (ID, speed, pitch), cache status
- **Outputs**: Generated audio file path
- **Metadata**: Provider name, cache hit/miss
- **Duration**: Generation time in milliseconds

## Example Trace Data

```json
{
  "name": "gemini.generate_content",
  "run_type": "llm",
  "inputs": {
    "prompt": "Hello, how are you?",
    "has_system_instruction": true,
    "context_length": 5,
    "temperature": 0.7
  },
  "outputs": {
    "response_length": 42
  },
  "metadata": {
    "model": "gemini-2.5-flash",
    "circuit_breaker_state": "closed",
    "duration_ms": 1234.56
  }
}
```

## Disabling Tracing

To disable tracing (useful for testing or when API key is not available):

```bash
# Option 1: Set environment variable
LANGSMITH_TRACING=false

# Option 2: Don't set LANGSMITH_API_KEY
# Tracing will automatically disable if API key is missing
```

The code gracefully handles missing LangSmith - it will log a debug message and continue without tracing.

## Advanced Usage

### Custom Tracing

You can add custom traces for your own functions:

```python
from src.services.tracing_service import get_tracing_service, trace_api_call

# Option 1: Use decorator
tracing_service = get_tracing_service()

@tracing_service.trace_function(name="my_custom_function")
def my_function():
    # Your code here
    pass

# Option 2: Manual tracing
trace_api_call(
    service_name="custom",
    operation="my_operation",
    inputs={"param1": "value1"},
    outputs={"result": "success"},
    metadata={"custom_field": "value"},
    duration_ms=123.45,
    success=True,
)
```

### Filtering and Searching

In LangSmith dashboard, you can:
- Filter by service name (`gemini`, `tts`)
- Filter by operation (`generate_content`, `generate_audio`)
- Search by metadata fields
- Filter by success/failure
- Filter by time range

## Troubleshooting

### Tracing Not Working

1. **Check environment variables**:
   ```bash
   echo $LANGSMITH_TRACING
   echo $LANGSMITH_API_KEY
   ```

2. **Check logs**: Look for messages like:
   - `"LangSmith tracing enabled"` - ✅ Working
   - `"LangSmith tracing not enabled"` - ⚠️ Check config
   - `"Failed to initialize LangSmith tracing"` - ❌ Check API key

3. **Verify API key**: Test your API key at [https://smith.langchain.com](https://smith.langchain.com)

### No Traces Appearing

- Wait a few seconds - traces are sent asynchronously
- Check your project name matches in LangSmith dashboard
- Verify network connectivity to LangSmith API

## Best Practices

1. **Use descriptive project names**: Set `LANGSMITH_PROJECT` to organize traces by environment (e.g., `dynevi-dev`, `dynevi-prod`)

2. **Monitor costs**: LangSmith has usage limits on free tier - monitor your usage

3. **Sanitize sensitive data**: The code automatically truncates long prompts, but be careful with sensitive information in metadata

4. **Use for debugging**: Enable tracing when debugging issues, disable in production if needed for performance

## Integration with Other Tools

LangSmith integrates with:
- **LangChain/LangGraph**: Automatic tracing for LangChain operations
- **OpenAI**: Can wrap OpenAI clients for tracing
- **Custom LLMs**: Use `@traceable` decorator for any function

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)

