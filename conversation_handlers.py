def respond(state, merchant_message: str) -> dict:
    msg_lower = str(merchant_message).lower().strip()
    state = state if isinstance(state, dict) else {}

    hostile_keywords = ["stop", "spam", "useless", "band karo", "remove", "not interested", "unsubscribe", "bother"]
    if any(kw in msg_lower for kw in hostile_keywords):
        state["hostile_seen"] = True
        return {
            "action": "end",
            "body": "Understood. I have stopped messaging you and removed you from future outreach.",
            "cta": "none",
            "send_as": "vera",
            "suppression_key": "hostile_opt_out"
        }

    auto_reply_keywords = [
        "automated", "auto-reply", "autoreply", "unavailable", "business hours",
        "get back", "thank you for your message", "thanks for your message",
        "currently away", "out of office", "away", "later", "not available",
        "working hours", "leave a message", "reach out", "will respond",
        "operating hours", "we are closed"
    ]
    if any(kw in msg_lower for kw in auto_reply_keywords):
        auto_count = int(state.get("auto_reply_count", 0)) + 1
        state["auto_reply_count"] = auto_count
        if auto_count >= 2:
            return {
                "action": "end",
                "body": "",
                "cta": "none",
                "send_as": "none",
                "suppression_key": "auto_reply"
            }
        return {
            "action": "pause",
            "body": "",
            "cta": "none",
            "send_as": "none",
            "suppression_key": "auto_reply"
        }

    intent_keywords = ["lets do it", "let's do it", "whats next", "what's next", "go ahead", "yes", "kar do", "proceed"]
    if any(kw in msg_lower for kw in intent_keywords):
        return {
            "action": "execute",
            "body": "Fantastic! I have processed the update for your profile. It will reflect on magicpin within the next 24 hours. Let me know if you need help with anything else!",
            "cta": "none",
            "send_as": "vera",
            "suppression_key": "intent_executed"
        }

    return {
        "action": "reply",
        "body": "Would you like me to go ahead and process this update for you? Please reply YES or STOP.",
        "cta": "YES/STOP",
        "send_as": "vera",
        "suppression_key": "default_turn"
    }
