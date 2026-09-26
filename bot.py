import json
import os
import requests
from typing import Dict, Optional

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


def compose(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> dict:
    system_prompt = f"""You are Vera, a merchant-AI assistant for magicpin. 
Your goal is to compose a highly specific, context-aware WhatsApp message for an Indian merchant.
- Anchor on verifiable facts (e.g., numbers, dates, expired offers) from the context.
- Match the merchant's language (use natural Hinglish code-mixing if they prefer 'hi').
- Maintain a peer/colleague tone. Do NOT fabricate information. 
- Single primary CTA (YES/STOP for action triggers, open_ended, or none).

Output strictly valid JSON with keys: 'body', 'cta', 'send_as' (must be 'vera'), 'suppression_key', and 'rationale'.

Contexts provided:
Category: {json.dumps(category)}
Merchant: {json.dumps(merchant)}
Trigger: {json.dumps(trigger)}
Customer: {json.dumps(customer) if customer else 'None'}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the response dict based on the contexts."}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=28
        )
        result = json.loads(response.json()['choices'][0]['message']['content'])

        return {
            "body": result.get("body", "Hi, we have an update on your magicpin profile."),
            "cta": result.get("cta", "open_ended"),
            "send_as": "vera",
            "suppression_key": result.get("suppression_key", f"{merchant.get('id', 'M')}_{trigger.get('id', 'T')}"),
            "rationale": result.get("rationale", "Generated successfully via LLM.")
        }
    except Exception as e:
        return {
            "body": f"Hi {merchant.get('identity', {}).get('name', 'Merchant')}, noticed some recent activity on your profile. Reply YES to review.",
            "cta": "YES/STOP",
            "send_as": "vera",
            "suppression_key": f"{merchant.get('id', 'unknown')}_fallback",
            "rationale": f"Fallback triggered due to API timeout/error: {str(e)}"
        }
