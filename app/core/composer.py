import uuid
import json
from core.llm import ask_llm_json

async def compose_tick_action(trigger_id: str, trigger_payload: dict, merchant: dict, category: dict, customer: dict | None) -> dict:
    system_prompt = """CRITICAL INSTRUCTION: You MUST NOT output any thoughts, reasoning, or bullet points. You must output ONLY the raw, valid JSON object. Do not wrap the JSON in markdown formatting.
You are "Vera", an AI assistant for local merchants.
You must output strict JSON matching EXACTLY this structure:
{
  "conversation_id": "string (generate a unique string)",
  "merchant_id": "string",
  "customer_id": "string or null",
  "send_as": "vera or merchant_on_behalf",
  "trigger_id": "string",
  "template_name": "generic_v1",
  "template_params": ["list of strings"],
  "body": "the actual whatsapp message",
  "cta": "open_ended or binary_yes_no",
  "suppression_key": "string",
  "rationale": "string"
}
Keep messages specific, use exact numbers from the data, and match the category voice."""

    user_prompt = f"""
Trigger ID: {trigger_id}
Trigger Payload: {json.dumps(trigger_payload, default=str)}
Merchant: {json.dumps(merchant, default=str)}
Category: {json.dumps(category, default=str)}
Customer: {json.dumps(customer, default=str) if customer else 'None'}
"""
    
    result = await ask_llm_json(system_prompt, user_prompt)
    
    if not result or "body" not in result:
        return {
            "conversation_id": str(uuid.uuid4()),
            "merchant_id": merchant.get("merchant_id", ""),
            "customer_id": None,
            "send_as": "vera",
            "trigger_id": trigger_id,
            "template_name": "fallback",
            "template_params": [],
            "body": "Hello, we are experiencing a slight delay. We will be right with you.",
            "cta": "none",
            "suppression_key": "fallback",
            "rationale": "Fallback: LLM failed to return valid JSON"
        }
        
    if not result.get("conversation_id"):
        result["conversation_id"] = str(uuid.uuid4())
    if not result.get("trigger_id"):
        result["trigger_id"] = trigger_id
    if not result.get("merchant_id"):
        result["merchant_id"] = merchant.get("merchant_id", "")
    return result

async def compose_reply_action(reply_req: dict, merchant: dict, category: dict, customer: dict | None) -> dict:
    system_prompt = """CRITICAL INSTRUCTION: You MUST NOT output any thoughts, reasoning, or bullet points. You must output ONLY the raw, valid JSON object. Do not wrap the JSON in markdown formatting.
You are an AI assistant replying to a message.
You must output strict JSON matching EXACTLY this structure:
{
  "action": "send or wait or end",
  "body": "string or null",
  "cta": "string or null",
  "wait_seconds": "int or null",
  "rationale": "string"
}
Detect auto-replies. If it is an auto-reply, return action="end".
Detect hostile messages. If it is hostile, return action="end".
CRITICAL RULE FOR INTENT TRANSITION: If the user's message indicates agreement or commitment (e.g., 'let's do it', 'yes', 'what's next'), you MUST transition to ACTION mode immediately. Provide the requested information, draft, or confirmation. You MUST NOT use any qualifying phrases like 'would you', 'do you', 'can you tell', 'what if', or 'how about'. Just do the task and use action words like 'done', 'sending', 'draft', 'here', 'confirm', or 'proceed'."""

    user_prompt = f"""
Reply Request Message: {reply_req.get('message', '')}
Context:
Reply Request: {json.dumps(reply_req, default=str)}
Merchant: {json.dumps(merchant, default=str)}
Category: {json.dumps(category, default=str)}
Customer: {json.dumps(customer, default=str) if customer else 'None'}
"""
    result = await ask_llm_json(system_prompt, user_prompt)
    
    if not result or "action" not in result:
        return {
            "action": "wait",
            "wait_seconds": 60,
            "rationale": "Fallback: LLM failed to return valid JSON"
        }
        
    return result
