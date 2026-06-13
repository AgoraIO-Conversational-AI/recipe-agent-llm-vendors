"""Vendor registry — data-driven switchboard over the A4.1 LLM vendors."""
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agora_agent.agentkit import vendors as V

CATEGORY = "LLM"   # one of: STT | LLM | TTS | REALTIME  (per repo)


@dataclass
class VendorSpec:
    cls: Callable[..., Any]
    creds: Dict[str, str] = field(default_factory=dict)   # sdk_field -> ENV_VAR (required, no default)
    defaults: Dict[str, Any] = field(default_factory=dict)  # sdk_field -> default value
    model_field: Optional[str] = None   # field overridden by {CATEGORY}_MODEL
    voice_field: Optional[str] = None   # field overridden by {CATEGORY}_VOICE


SPECS: Dict[str, VendorSpec] = {
  "openai":   VendorSpec(V.OpenAI, {}, {"model": "gpt-4o-mini"}, model_field="model"),
  "anthropic":VendorSpec(V.Anthropic,
                {"api_key": "ANTHROPIC_API_KEY"},
                {"model": "claude-3-5-sonnet-20241022", "url": "https://api.anthropic.com",
                 "max_tokens": 1024, "headers": {}}, model_field="model"),
  "gemini":   VendorSpec(V.Gemini, {"api_key": "GEMINI_API_KEY"},
                {"model": "gemini-2.0-flash"}, model_field="model"),
  "groq":     VendorSpec(V.Groq, {"api_key": "GROQ_API_KEY"},
                {"model": "llama-3.3-70b-versatile", "base_url": "https://api.groq.com/openai/v1"},
                model_field="model"),
  "azure":    VendorSpec(V.AzureOpenAI,
                {"api_key": "AZURE_OPENAI_API_KEY", "endpoint": "AZURE_OPENAI_ENDPOINT",
                 "deployment_name": "AZURE_OPENAI_DEPLOYMENT"},
                {"model": "gpt-4o"}, model_field="model"),
  "bedrock":  VendorSpec(V.AmazonBedrock,
                {"access_key": "AWS_ACCESS_KEY_ID", "secret_key": "AWS_SECRET_ACCESS_KEY",
                 "region": "AWS_REGION"},
                {"model": "anthropic.claude-3-5-sonnet-20240620-v1:0"}, model_field="model"),
  "vertexai": VendorSpec(V.VertexAILLM,
                {"api_key": "GOOGLE_API_KEY", "project_id": "GOOGLE_PROJECT_ID",
                 "location": "GOOGLE_LOCATION"},
                {"model": "gemini-2.0-flash"}, model_field="model"),
  "dify":     VendorSpec(V.Dify, {"api_key": "DIFY_API_KEY", "url": "DIFY_URL"},
                {"model": "dify"}),
  "custom":   VendorSpec(V.CustomLLM,
                {"api_key": "CUSTOM_LLM_API_KEY", "base_url": "CUSTOM_LLM_BASE_URL"},
                {"model": "gpt-4o-mini"}, model_field="model"),
}


def available() -> List[str]:
    return sorted(SPECS)


def required_env(name: str) -> List[str]:
    return list(SPECS[name].creds.values())


def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    env = env if env is not None else os.environ
    if name not in SPECS:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")
    spec = SPECS[name]
    kwargs: Dict[str, Any] = dict(spec.defaults)
    # generic model/voice overrides
    if spec.model_field and env.get(f"{CATEGORY}_MODEL"):
        kwargs[spec.model_field] = env[f"{CATEGORY}_MODEL"]
    if spec.voice_field and env.get(f"{CATEGORY}_VOICE"):
        kwargs[spec.voice_field] = env[f"{CATEGORY}_VOICE"]
    # required creds + infra from env
    missing: List[str] = []
    for sdk_field, var in spec.creds.items():
        val = env.get(var)
        if not val:
            missing.append(var)
        else:
            kwargs[sdk_field] = val
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return spec.cls(**kwargs)
