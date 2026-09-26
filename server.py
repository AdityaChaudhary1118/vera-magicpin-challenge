import os
import socket

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from conversation_handlers import respond


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def resolve_port() -> int:
    env_port = os.environ.get("MAGICPIN_PORT")
    candidate_ports = []
    if env_port:
        candidate_ports.append(int(env_port))

    candidate_ports.extend([8081, 8080] + list(range(8082, 8082 + 20)))

    seen = set()
    for port in candidate_ports:
        if port in seen:
            continue
        seen.add(port)
        if is_port_available(port):
            return port

    raise RuntimeError("No free local port found for the bot server")


APP_PORT = resolve_port()
os.environ["MAGICPIN_PORT"] = str(APP_PORT)

app = FastAPI()
current_context = {"context_store": {}}


def _get_context(scope: str, context_id: str):
    return current_context.get("context_store", {}).get(scope, {}).get(str(context_id))


def _make_trigger_action(trigger: dict, merchant: dict, customer: dict = None) -> dict:
    merchant_name = merchant.get("identity", {}).get("name", "Merchant")
    trigger_kind = trigger.get("kind", "update")
    customer_name = customer.get("identity", {}).get("first_name", "Customer") if customer else None

    if trigger.get("scope") == "customer" and customer_name:
        body = (
            f"Hi {customer_name}, this is a quick update for {merchant_name}. "
            f"We noticed a relevant {trigger_kind} and want to help you take the next step. "
            "Reply YES to continue or STOP to opt out."
        )
    else:
        body = (
            f"Hi {merchant_name}, I noticed a relevant {trigger_kind} for your business. "
            f"We have a timely opportunity based on your recent activity. "
            "Reply YES to review or STOP to opt out."
        )

    return {
        "action": "send",
        "body": body,
        "merchant_id": merchant.get("merchant_id") or merchant.get("id") or trigger.get("merchant_id"),
        "customer_id": customer.get("customer_id") if customer else trigger.get("customer_id"),
        "trigger_id": trigger.get("id") or trigger.get("trigger_id"),
        "cta": "YES/STOP",
        "send_as": "vera",
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def universal_handler(request: Request, path: str):
    global current_context
    path_lower = path.lower()

    if "healthz" in path_lower:
        return JSONResponse({"status": "ok"})

    if "metadata" in path_lower:
        return JSONResponse({
            "name": "Vera Bot",
            "version": "1.0",
            "team_name": "magicpin",
            "model": "deepseek-chat",
        })

    if "reply" in path_lower or "webhook" in path_lower:
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        message = payload.get("message") or payload.get("text") or payload.get("body") or ""
        response_dict = respond(current_context, str(message))
        return JSONResponse(response_dict)

    if "context" in path_lower:
        try:
            data = await request.json()
        except Exception:
            data = {}

        if isinstance(data, dict):
            scope = data.get("scope")
            context_id = data.get("context_id")
            if scope and context_id:
                current_context.setdefault("context_store", {}).setdefault(str(scope), {})[str(context_id)] = {
                    "version": data.get("version"),
                    "payload": data.get("payload", {}),
                    "delivered_at": data.get("delivered_at"),
                }
                return JSONResponse({
                    "accepted": True,
                    "scope": scope,
                    "context_id": context_id,
                    "version": data.get("version"),
                })

        return JSONResponse({"accepted": False, "error": "invalid-context-payload"})

    if "tick" in path_lower:
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        trigger_ids = payload.get("available_triggers") or payload.get("triggers") or []
        actions = []
        context_store = current_context.get("context_store", {})

        for trigger_id in trigger_ids:
            trigger_entry = None
            for scope_key in ["trigger", "triggers"]:
                bucket = context_store.get(scope_key, {})
                if str(trigger_id) in bucket:
                    trigger_entry = bucket[str(trigger_id)]
                    break

            if not trigger_entry:
                continue

            trigger = trigger_entry.get("payload", {})
            merchant_id = trigger.get("merchant_id")
            customer_id = trigger.get("customer_id")
            merchant = context_store.get("merchant", {}).get(str(merchant_id), {}).get("payload", {}) if merchant_id else {}
            customer = context_store.get("customer", {}).get(str(customer_id), {}).get("payload", {}) if customer_id else None

            if not merchant:
                merchant = {"identity": {"name": "Merchant"}, "merchant_id": merchant_id}

            actions.append(_make_trigger_action(trigger, merchant, customer))

        return JSONResponse({"actions": actions})

    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    port = resolve_port()
    os.environ["MAGICPIN_PORT"] = str(port)
    print(f"Starting server on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
