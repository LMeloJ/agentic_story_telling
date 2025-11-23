# Gemini Model Configuration

## Valid Model Names

Google has updated their Gemini model names. The old `gemini-pro` model is no longer available in the v1beta API.

### Current Valid Models

1. **`gemini-1.5-flash`** (Default - Recommended)
   - Fast and cost-effective
   - Good for most use cases
   - Best balance of speed and quality

2. **`gemini-1.5-pro`**
   - Higher quality responses
   - Better for complex reasoning
   - Slightly slower and more expensive

3. **`gemini-1.5-flash-latest`**
   - Always uses the latest version of Flash
   - May change behavior over time

4. **`gemini-1.5-pro-latest`**
   - Always uses the latest version of Pro
   - May change behavior over time

## Configuration

### Environment Variable

Set the model name via environment variable:

```bash
export GEMINI_MODEL=gemini-1.5-flash
```

Or in your `.env` file:

```bash
GEMINI_MODEL=gemini-1.5-flash
```

### Default Model

The default model is now `gemini-1.5-flash`. You can override it:

- **Via environment**: `GEMINI_MODEL=gemini-1.5-pro`
- **In code**: Update `GeminiConfig` default value

## Model Comparison

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| `gemini-1.5-flash` | ⚡ Fast | ⭐⭐⭐ Good | 💰 Low | General use, NPCs |
| `gemini-1.5-pro` | 🐢 Slower | ⭐⭐⭐⭐⭐ Excellent | 💰💰 Higher | Complex reasoning |

## Troubleshooting

### Error: "404 models/gemini-pro is not found"

**Solution**: Update your model name to a valid one:

```bash
# Old (doesn't work)
GEMINI_MODEL=gemini-pro

# New (works)
GEMINI_MODEL=gemini-1.5-flash
```

### Finding Available Models

You can list available models using the Gemini API:

```python
import google.generativeai as genai

genai.configure(api_key="your-key")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(model.name)
```

## Migration Guide

If you were using `gemini-pro`:

1. **Update environment variable**:
   ```bash
   # Before
   GEMINI_MODEL=gemini-pro
   
   # After
   GEMINI_MODEL=gemini-1.5-flash
   ```

2. **Update config files**: Check any config files that hardcode the model name

3. **Test**: Run your tests to verify everything works

## Recommendations

- **For NPCs/Storytelling**: Use `gemini-1.5-flash` (fast, good quality, cost-effective)
- **For Complex Reasoning**: Use `gemini-1.5-pro` (better quality, slower)
- **For Production**: Use specific version (e.g., `gemini-1.5-flash`) not `-latest` variants

## References

- [Google AI Studio](https://aistudio.google.com/) - Test models and get API keys
- [Gemini API Documentation](https://ai.google.dev/docs) - Official documentation

