# all-the-llms: A Universal LLM Interface

A unified interface for querying Large Language Models (LLMs) across multiple providers using LiteLLM and OpenRouter. This package provides intelligent model routing that automatically selects the best provider for each model request.

## Installation

Install from PyPI:

```bash
pip install all-the-llms
```

The package is also available on [PyPI](https://pypi.org/project/all-the-llms/).

## Environment Variables Reference

### Required

- **`OPENROUTER_API_KEY`**: Get your key from [OpenRouter](https://openrouter.ai/keys)

### Optional (Direct Provider Access)

Only use if you have free credits you prefer over OpenRouter. Otherwise, prefer OpenRouter.

- **`OPENAI_API_KEY`**, **`ANTHROPIC_API_KEY`**, **`GOOGLE_API_KEY`**, or any `{PROVIDER}_API_KEY`

### Optional (Azure)

- **`AZURE_API_KEY`**: Azure OpenAI API key
- **`AZURE_API_BASE`**: Endpoint URL
- **`AZURE_API_VERSION`**: API version
- **`AZURE_API_MODELS`**: Comma-separated list of deployed models (e.g., `"gpt-5,gpt-4.1,gpt-4.1-mini"`)

### Example `.env` File

```env
# OpenRouter (required for routing judge and fallback models)
OPENROUTER_API_KEY=...

# Direct provider access (optional - only use if you have free credits available 
# that you prefer over OpenRouter. Prefer OpenRouter otherwise.)
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# Azure (specified for Harvard Medical School)
AZURE_API_KEY=...
AZURE_API_BASE="https://azure-ai.hms.edu"
AZURE_API_VERSION="2024-10-21"
AZURE_API_MODELS="gpt-5,gpt-5-mini,gpt-4.1,gpt-4.1-mini,gpt-4.1-nano"
```

## What is LiteLLM?

[LiteLLM](https://github.com/BerriAI/litellm) is a Python library that provides a unified interface to call multiple LLM APIs with a consistent OpenAI-like API. It supports 100+ LLM providers including:

- **OpenAI** (GPT-4, GPT-3.5, etc.)
- **Anthropic** (Claude models)
- **Azure OpenAI**
- **Google** (Gemini, PaLM)
- **OpenRouter** (aggregator for multiple models)
- And many more...

LiteLLM handles provider-specific differences, retries, rate limiting, and error handling, allowing you to switch between providers with minimal code changes.

## What is OpenRouter?

[OpenRouter](https://openrouter.ai/) is a unified API that provides access to 100+ LLM models from various providers through a single interface. It's particularly useful when:

- You don't have direct API keys for specific providers
- You want to access models not available through your direct provider accounts
- You need a fallback option when your primary provider is unavailable
- You want to compare models across different providers

OpenRouter requires credits (free tier available) and routes requests to the appropriate provider on your behalf.

## Architecture

This package uses a three-tier routing system:

1. **Azure** (highest priority): Direct Azure OpenAI deployments
2. **Provider** (medium priority): Direct API access (OpenAI, Anthropic, etc.)
3. **OpenRouter** (fallback): Unified API for models not available through other routes

The system prioritizes routes in this order: Azure → Provider → OpenRouter.

The routing is handled by a "routing judge" - an LLM that intelligently selects the best route based on:
- Model name matching (semantic and exact)
- Available API keys
- Model availability in each catalog

## Quick Start

### 1. Install

```bash
pip install all-the-llms
```

### 2. Get Your API Key

Get a free API key from [OpenRouter](https://openrouter.ai/keys) (free tier available).

### 3. Create `.env` File

Create a `.env` file in your project root:

```env
OPENROUTER_API_KEY=your_key_here
```

That's it! You can optionally add direct provider API keys if you have them:

```env
OPENROUTER_API_KEY=your_key_here
OPENAI_API_KEY=optional_direct_key
ANTHROPIC_API_KEY=optional_direct_key
```

### 4. Your First Request

```python
from all_the_llms import LLM
from dotenv import load_dotenv

load_dotenv()

llm = LLM("gpt-4o")
response = llm.completion([{"role": "user", "content": "Hello!"}])
print(response.choices[0].message.content)
```

## Usage Examples

### Basic Text Completion

```python
from all_the_llms import LLM
from dotenv import load_dotenv

load_dotenv()

# Initialize an LLM - routing happens automatically
llm = LLM("gpt-4o")

# Make a completion request
response = llm.completion(
    messages=[{"role": "user", "content": "Hello, how are you?"}],
    temperature=0.7,
    max_tokens=100
)

print(response.choices[0].message.content)
```

**Note**: All LiteLLM features (streaming, tools, etc.) are supported through the `completion()` method's `**kwargs`. See the [LiteLLM documentation](https://docs.litellm.ai/) for a complete list of available parameters.

### Structured Output with Pydantic

Get validated, structured responses using Pydantic models. This uses the [instructor](https://github.com/jxnl/instructor) library under the hood, which automatically handles validation errors and retries to ensure you get properly formatted responses.

```python
from pydantic import BaseModel
from all_the_llms import LLM
from dotenv import load_dotenv

load_dotenv()

class User(BaseModel):
    name: str
    age: int

llm = LLM("gpt-4o")
user = llm.structured_completion(
    messages=[{"role": "user", "content": "Jason is 25 years old"}],
    response_model=User
)
print(user.name, user.age)
```

**How it works**: The `structured_completion()` method uses [instructor](https://github.com/jxnl/instructor) to automatically:
- Convert your Pydantic model to a JSON schema
- Send it to the LLM with instructions to return valid JSON
- Validate the response against your model
- Retry up to 3 times if validation fails, feeding errors back to the model
- Return a fully validated Pydantic instance

This ensures you always get properly structured, type-safe responses without manual parsing or validation.

### Custom Routing Judge

By default, the system uses `openrouter/openai/gpt-4o-mini` as the routing judge (free as long as you have an OpenRouter API key). This default can be customized by passing a different model to the `routing_judge` parameter:

```python
llm = LLM("gpt-5-2025-11-16", routing_judge="azure/gpt-4.1-mini")
```

## Development

For development, you can install the package in editable mode:

```bash
git clone https://github.com/payalchandak/all-the-llms.git
cd all-the-llms
pip install -e .
```

This allows you to make changes to the source code that take effect immediately without reinstalling.

## What the Code Does

### `LLM` Class

The `LLM` class is a thin wrapper that:

1. **Resolves the model**: Takes a user-friendly model name (e.g., `"gpt-5-2025-11-16"`) and resolves it to a concrete provider-specific model ID (e.g., `"azure/gpt-5"` or `"openrouter/openai/gpt-3.5-turbo"`)

2. **Tests the connection**: On initialization, sends a test request to verify the model is accessible and working

3. **Exposes a simple API**: Provides a `completion()` method that wraps `litellm.completion()` with the resolved model

### `ModelRouter` Class

The `ModelRouter` class handles intelligent routing:

1. **Loads model catalogs**: 
   - Azure models from `AZURE_API_MODELS` environment variable
   - Provider models from LiteLLM's catalog (based on available API keys)
   - OpenRouter models by querying the OpenRouter API

2. **Exact matching**: First tries to find exact matches in the catalogs (prioritizing Azure → Provider → OpenRouter). Model names are normalized (lowercase, whitespace removed) for matching.

3. **LLM-based routing**: If no exact match, uses a "routing judge" LLM to decide which route to use

4. **Model resolution**: Uses the routing judge again to map the requested model name to a specific model in the selected route

5. **Fallback handling**: If the selected route has no available models, falls back to other routes

## Example Behavior

When you initialize an LLM, you'll see output like this:

```
Routing model gpt-5-2025-11-16 to valid LLM...
Selected route azure because the requested model 'gpt-5-2025-11-16' semantically matches the azure model 'gpt-5'.
Resolved gpt-5-2025-11-16 to azure/gpt-5
Testing LLM at azure/gpt-5
Successfully recieved response from gpt-5-2025-08-07
```

### Routing Examples

**Azure Route** (when model matches Azure deployment):
```
Routing model gpt-5-2025-11-16 to valid LLM...
Selected route azure because the requested model 'gpt-5-2025-11-16' semantically matches the azure model 'gpt-5'.
Resolved gpt-5-2025-11-16 to azure/gpt-5
```

**Provider Route** (when direct API key is available):
```
Routing model claude-sonnet-4.5 to valid LLM...
Selected route provider because the requested model 'claude-sonnet-4.5' matches a model available from the provider with a direct api key.
Resolved claude-sonnet-4.5 to claude-sonnet-4-5
```

**OpenRouter Route** (fallback when no direct access):
```
Routing model gpt-3.5-turbo to valid LLM...
Selected route openrouter because requested model 'gpt-3.5-turbo' does not match any available azure models and there are no applicable provider options.
Resolved gpt-3.5-turbo to openrouter/openai/gpt-3.5-turbo
```

### Error Handling

The system validates each model on initialization. If a model fails, you'll see an error:

```
RuntimeError: Could not get a valid response from openrouter/deepseek/deepseek-r1-0528. 
litellm.APIError: APIError: OpenrouterException - {"error":{"message":"This request requires more credits, 
or fewer max_tokens. You requested up to 7168 tokens, but can only afford 4706..."}}
```

Common issues:
- **Insufficient credits**: OpenRouter account needs more credits
- **Invalid API key**: Check your environment variables
- **Model unavailable**: The requested model may not be available on the selected route
- **Rate limiting**: Provider may be rate limiting requests
