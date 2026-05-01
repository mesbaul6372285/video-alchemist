import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

SUPPORTED_PROVIDERS = ["openai", "claude", "openrouter", "groq"]

def get_provider_config():
    provider = os.getenv("PROVIDER", "openai").lower()
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("MODEL_NAME")
    api_base = os.getenv("API_BASE", None)

    if not api_key:
        raise ValueError("API_KEY is missing from .env")
    if not model_name:
        raise ValueError("MODEL_NAME is missing from .env")
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}. Choose from {SUPPORTED_PROVIDERS}")

    config = {
        "provider": provider,
        "api_key": api_key,
        "model_name": model_name,
        "api_base": api_base,
    }

    # Map provider to LiteLLM model string
    if provider == "openai":
        config["litellm_model"] = model_name  # e.g. "gpt-4o"

    elif provider == "claude":
        config["litellm_model"] = f"anthropic/{model_name}"  # e.g. "anthropic/claude-3-5-sonnet-20241022"

    elif provider == "openrouter":
        if not api_base:
            config["api_base"] = "https://openrouter.ai/api/v1"
        config["litellm_model"] = f"openrouter/{model_name}"  # e.g. "openrouter/meta-llama/llama-3.1-70b-instruct"

    elif provider == "groq":
        config["litellm_model"] = f"groq/{model_name}"  # e.g. "groq/llama3-70b-8192"

    return config


def get_llm_response(messages: list, temperature: float = 0.7) -> str:
    """
    Universal LLM call. Every agent uses this.
    messages = [{"role": "user", "content": "..."}, ...]
    Returns the response text string.
    """
    config = get_provider_config()

    kwargs = {
        "model": config["litellm_model"],
        "messages": messages,
        "temperature": temperature,
        "api_key": config["api_key"],
    }

    if config.get("api_base"):
        kwargs["api_base"] = config["api_base"]

    response = completion(**kwargs)
    return response.choices[0].message.content


if __name__ == "__main__":
    # Quick test
    print("Testing LLM config...")
    result = get_llm_response([{"role": "user", "content": "Say hello in one word."}])
    print(f"Response: {result}")
    print("LLM config working correctly.")