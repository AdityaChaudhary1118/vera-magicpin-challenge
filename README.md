# Vera Bot — magicpin AI Challenge Submission

## Approach
Our approach centers on creating a deterministic, context-aware agentic workflow. We structured the prompt around the 4-context framework (`Category`, `Merchant`, `Trigger`, `Customer`) to build contextually rich WhatsApp communications.

We routed execution through OpenRouter using DeepSeek-Chat (`temperature=0.0`) to guarantee deterministic JSON output, fast processing (<30s constraint), and natural Hinglish code-mixing based on merchant language preferences.

Key design principles:
- **Fact Anchoring**: Extracting explicit metrics (e.g., CTR drops, expired offer dates, percentage changes) directly from context objects without hallucination.
- **Tone Matching**: Injecting natural Hinglish when `merchant.identity.language` specifies `hi`.
- **Strict Guardrails**: Outputting standardized CTA types (`YES/STOP`, `open_ended`, or `none`).

## Multi-Turn Intelligence
Implemented in `conversation_handlers.py`:
- **Auto-Reply Interruption Handling**: Detects automated WhatsApp Business auto-replies (e.g., business hours notices) and applies suppression to avoid burning unnecessary context turns.
- **Intent Transitioning**: Instantly pivots from qualifying to action execution upon detecting explicit merchant confirmation keywords ("kar do", "go ahead", "yes").

## Tradeoffs Made
1. **Stateless vs. Stateful**: Kept the primary `compose` function stateless for maximum evaluator portability.
2. **Fallback Strategy**: Embedded a local deterministic template fallback inside `bot.py` to prevent failures in case of network timeouts.

## What Additional Context Would Help
- Live catalog and inventory integration APIs.
- Real-time customer booking calendar state (for exact appointment slot offering).
- Granular WhatsApp message delivery and read-receipt callbacks.