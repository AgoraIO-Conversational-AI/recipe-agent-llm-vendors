# Deep Dive — Vendor Registry

**When to Read This:** You are adding a new LLM vendor, changing an existing vendor's SDK fields or model defaults, debugging a `ValueError` about missing credentials, or auditing which env vars a vendor needs. For the high-level picture, start at [02_architecture](../02_architecture.md).

The LLM vendor switchboard in `server/src/vendors.py` is the central feature of this recipe. All nine A4.1 LLM vendors are registered here as copy-pasteable builder functions and a data-driven `REGISTRY`.

## The registry structure

```python
REGISTRY: Dict[str, Tuple[Callable, List[str]]] = {
    "openai":    (build_openai,    []),                              # keyless
    "anthropic": (build_anthropic, ["ANTHROPIC_API_KEY"]),
    "gemini":    (build_gemini,    ["GEMINI_API_KEY"]),
    "groq":      (build_groq,      ["GROQ_API_KEY"]),
    "azure":     (build_azure,     ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]),
    "bedrock":   (build_bedrock,   ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]),
    "vertexai":  (build_vertexai,  ["GOOGLE_API_KEY", "GOOGLE_PROJECT_ID", "GOOGLE_LOCATION"]),
    "dify":      (build_dify,      ["DIFY_API_KEY", "DIFY_URL"]),
    "custom":    (build_custom,    ["CUSTOM_LLM_API_KEY", "CUSTOM_LLM_BASE_URL"]),
}
```

Each entry is `(builder_fn, required_cred_env_vars)`. Empty creds list = Agora-managed / keyless.

## `build_vendor()` — the single construction entry point

```python
def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    env = env if env is not None else os.environ
    if name not in REGISTRY:
        raise ValueError(f"unknown LLM vendor '{name}'; choose one of {available()}")
    builder, required = REGISTRY[name]
    missing = [var for var in required if not env.get(var)]
    if missing:
        raise ValueError(
            f"LLM vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return builder(env)
```

The `env` parameter is injected for tests; production code passes `None` (falls back to `os.environ`).

## Per-vendor SDK constructors

### `openai` — Agora-managed, keyless

```python
OpenAI(model=_model(env, "gpt-4o-mini"))
```

No API key. The LLM is Agora-managed. `LLM_MODEL` overrides the model name.

### `anthropic`

```python
Anthropic(
    api_key=env["ANTHROPIC_API_KEY"],
    model=_model(env, "claude-3-5-sonnet-20241022"),
    url="https://api.anthropic.com",
    max_tokens=1024,
    headers={},
)
```

### `gemini` (Google AI Studio)

```python
Gemini(
    api_key=env["GEMINI_API_KEY"],
    model=_model(env, "gemini-2.0-flash"),
)
```

### `groq`

```python
Groq(
    api_key=env["GROQ_API_KEY"],
    model=_model(env, "llama-3.3-70b-versatile"),
    base_url="https://api.groq.com/openai/v1",
)
```

### `azure`

```python
AzureOpenAI(
    api_key=env["AZURE_OPENAI_API_KEY"],
    endpoint=env["AZURE_OPENAI_ENDPOINT"],
    deployment_name=env["AZURE_OPENAI_DEPLOYMENT"],
    model=_model(env, "gpt-4o"),
)
```

`AZURE_OPENAI_ENDPOINT` is the full resource URL (e.g. `https://your-resource.openai.azure.com`).

### `bedrock`

```python
AmazonBedrock(
    access_key=env["AWS_ACCESS_KEY_ID"],
    secret_key=env["AWS_SECRET_ACCESS_KEY"],
    region=env["AWS_REGION"],
    model=_model(env, "anthropic.claude-3-5-sonnet-20240620-v1:0"),
)
```

### `vertexai` (Google Vertex AI)

```python
VertexAILLM(
    api_key=env["GOOGLE_API_KEY"],
    project_id=env["GOOGLE_PROJECT_ID"],
    location=env["GOOGLE_LOCATION"],
    model=_model(env, "gemini-2.0-flash"),
)
```

### `dify`

```python
Dify(
    api_key=env["DIFY_API_KEY"],
    url=env["DIFY_URL"],
    model=_model(env, "dify"),
)
```

`DIFY_URL` is your Dify app endpoint (e.g. `https://api.dify.ai/v1/chat-messages`).

### `custom` (any OpenAI-compatible endpoint)

```python
CustomLLM(
    api_key=env["CUSTOM_LLM_API_KEY"],
    base_url=env["CUSTOM_LLM_BASE_URL"],
    model=_model(env, "gpt-4o-mini"),
)
```

`CUSTOM_LLM_BASE_URL` is the full OpenAI-compatible endpoint (e.g. `https://your-host/v1/chat/completions`).

## Model override (`LLM_MODEL`)

`_model(env, default)` returns `env.get("LLM_MODEL") or default`. Setting `LLM_MODEL` overrides the model name for any vendor. The default is the SDK-verified value shown above per vendor.

## How it is wired into the session

In `Agent.start()` (`agent.py`):

```python
selected = (vendor or self.vendor).strip()   # per-request override or LLM_VENDOR
llm = build_vendor(selected)                 # raises ValueError on missing creds

stt = DeepgramSTT(model="nova-3", language="en")
tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")

agora_agent = AgoraAgent(
    client=self.client,
    greeting=self.greeting,
    failure_message="Please wait a moment.",
    max_history=50,
    turn_detection={...},                    # STT-pipeline-owned (not on the LLM vendor)
    advanced_features={"enable_rtm": True},
    parameters=parameters,
).with_stt(stt).with_llm(llm).with_tts(tts)
```

## Adding a new vendor

1. Import the SDK vendor class from `agora_agent.agentkit.vendors`.
2. Write a `build_<name>(env)` function following the pattern above.
3. Add a `REGISTRY` entry: `"<name>": (build_<name>, ["REQUIRED_ENV_VAR", ...])`.
4. Add commented-out env block to `server/.env.example`.
5. Run `bun run verify:backend` + `cd server && pytest tests -v`.

`test_vendors.py::test_every_vendor_constructs_and_emits_config` automatically covers the new vendor (it iterates `available()`).

## Registry helper functions

| Function | Returns |
| -------- | ------- |
| `available()` | Sorted list of all registered vendor names |
| `required_env(name)` | List of required credential env var names |
| `needs_key(name)` | `True` if the vendor requires credentials |
| `build_vendor(name, env?)` | Constructed SDK vendor object, or `ValueError` |

## Related L1

- [02_architecture](../02_architecture.md) · [04_conventions](../04_conventions.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
