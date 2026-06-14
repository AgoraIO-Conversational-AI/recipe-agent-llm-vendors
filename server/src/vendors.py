"""LLM vendor registry — one readable builder per Agora-supported LLM vendor.

Each `build_<vendor>(env)` is a self-contained, copy-pasteable example of wiring
that vendor into an Agora Conversational AI agent: it shows the real SDK
constructor call and exactly which env vars it needs. `build_vendor(name)`
selects one by `LLM_VENDOR`. Optional `LLM_MODEL` overrides the model.

Add or change a vendor by editing its builder below + the REGISTRY line.
"""
import os
from typing import Callable, Dict, List, Optional, Tuple

from agora_agent.agentkit.vendors import (
    OpenAI, Anthropic, Gemini, Groq, AzureOpenAI, AmazonBedrock, VertexAILLM,
    Dify, CustomLLM,
)

CATEGORY = "LLM"


def _model(env, default: str) -> str:
    """The selected model, overridable with LLM_MODEL."""
    return env.get("LLM_MODEL") or default


# --- one builder per vendor (these are the samples) -------------------------

def build_openai(env):
    """OpenAI — Agora-managed, key-less by default."""
    return OpenAI(model=_model(env, "gpt-4o-mini"))


def build_anthropic(env):
    """Anthropic Claude — set ANTHROPIC_API_KEY (console.anthropic.com)."""
    return Anthropic(
        api_key=env["ANTHROPIC_API_KEY"],
        model=_model(env, "claude-3-5-sonnet-20241022"),
        url="https://api.anthropic.com",
        max_tokens=1024,
        headers={},
    )


def build_gemini(env):
    """Google Gemini (AI Studio) — set GEMINI_API_KEY (aistudio.google.com)."""
    return Gemini(
        api_key=env["GEMINI_API_KEY"],
        model=_model(env, "gemini-2.0-flash"),
    )


def build_groq(env):
    """Groq — set GROQ_API_KEY (console.groq.com)."""
    return Groq(
        api_key=env["GROQ_API_KEY"],
        model=_model(env, "llama-3.3-70b-versatile"),
        base_url="https://api.groq.com/openai/v1",
    )


def build_azure(env):
    """Azure OpenAI — set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT."""
    return AzureOpenAI(
        api_key=env["AZURE_OPENAI_API_KEY"],
        endpoint=env["AZURE_OPENAI_ENDPOINT"],
        deployment_name=env["AZURE_OPENAI_DEPLOYMENT"],
        model=_model(env, "gpt-4o"),
    )


def build_bedrock(env):
    """Amazon Bedrock — set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION."""
    return AmazonBedrock(
        access_key=env["AWS_ACCESS_KEY_ID"],
        secret_key=env["AWS_SECRET_ACCESS_KEY"],
        region=env["AWS_REGION"],
        model=_model(env, "anthropic.claude-3-5-sonnet-20240620-v1:0"),
    )


def build_vertexai(env):
    """Google Vertex AI — set GOOGLE_API_KEY, GOOGLE_PROJECT_ID, GOOGLE_LOCATION."""
    return VertexAILLM(
        api_key=env["GOOGLE_API_KEY"],
        project_id=env["GOOGLE_PROJECT_ID"],
        location=env["GOOGLE_LOCATION"],
        model=_model(env, "gemini-2.0-flash"),
    )


def build_dify(env):
    """Dify — set DIFY_API_KEY and DIFY_URL (your Dify app endpoint)."""
    return Dify(
        api_key=env["DIFY_API_KEY"],
        url=env["DIFY_URL"],
        model=_model(env, "dify"),
    )


def build_custom(env):
    """Any OpenAI-compatible endpoint — set CUSTOM_LLM_API_KEY and CUSTOM_LLM_BASE_URL."""
    return CustomLLM(
        api_key=env["CUSTOM_LLM_API_KEY"],
        base_url=env["CUSTOM_LLM_BASE_URL"],
        model=_model(env, "gpt-4o-mini"),
    )


# --- registry: name -> (builder, required env vars) -------------------------
# An empty env list means the vendor is Agora-managed / key-less.
REGISTRY: Dict[str, Tuple[Callable, List[str]]] = {
    "openai":    (build_openai,    []),
    "anthropic": (build_anthropic, ["ANTHROPIC_API_KEY"]),
    "gemini":    (build_gemini,    ["GEMINI_API_KEY"]),
    "groq":      (build_groq,      ["GROQ_API_KEY"]),
    "azure":     (build_azure,     ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]),
    "bedrock":   (build_bedrock,   ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]),
    "vertexai":  (build_vertexai,  ["GOOGLE_API_KEY", "GOOGLE_PROJECT_ID", "GOOGLE_LOCATION"]),
    "dify":      (build_dify,      ["DIFY_API_KEY", "DIFY_URL"]),
    "custom":    (build_custom,    ["CUSTOM_LLM_API_KEY", "CUSTOM_LLM_BASE_URL"]),
}


def available() -> List[str]:
    return sorted(REGISTRY)


def required_env(name: str) -> List[str]:
    return list(REGISTRY[name][1])


def needs_key(name: str) -> bool:
    return bool(REGISTRY[name][1])


def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    """Build the selected vendor; raises ValueError naming any missing env vars."""
    env = env if env is not None else os.environ
    if name not in REGISTRY:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")
    builder, required = REGISTRY[name]
    missing = [var for var in required if not env.get(var)]
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return builder(env)
