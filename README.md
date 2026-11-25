# Tonesetter

A small prototype that helps you say difficult things without sounding rude or
being easy to misread. Give it a draft you want to polish, or just describe what
you are trying to say — it prints one message, ready to copy and send.

Good for setting boundaries, declining invitations, and expressing disappointment.

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and replace the placeholder with your key
```

You can also `export GEMINI_API_KEY="your-api-key"` instead of using `.env`;
shell variables take precedence over `.env` values. `GOOGLE_API_KEY` works too.
The default model is `gemini-4-hydrogen`; override it with `--model` or
`TONESETTER_MODEL`.

If the primary model returns HTTP 503 (high demand), Tonesetter automatically
tries the next model: `gemini-3.5-flash-lite` by default. Set
`TONESETTER_FALLBACK_MODELS` to a comma-separated list to change the fallback chain.

## Usage

Interactive mode — it asks for the scenario, relationship, tone, then your draft
(or, if you leave the draft blank, what you want to say):

```bash
uv run tonesetter
```

One-shot mode — useful for quick tests and scripts:

```bash
uv run tonesetter --intent "decline a colleague's Friday drinks invitation, need to pick up my kid" \
  --scenario decline --relationship colleague --tone gentle

uv run tonesetter --draft "Stop asking me to babysit every weekend. I'm tired of being the default." \
  --scenario boundary --relationship family
```

`--draft` and `--intent` can be combined. At least one is required. The tool prints
only the rewritten message to stdout; prompts and errors go to stderr.

## How it works

`src/tonesetter/prompts.py` holds the system instruction and a few worked examples.
`src/tonesetter/service.py` makes a Gemini call with a Pydantic response schema
containing a single field, so the reply is just the message. On HTTP 503 it retries
with the fallback models. The CLI prints that field.

## Tests

```bash
uv run pytest
```
