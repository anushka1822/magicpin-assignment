import json
import re
from core.config import settings

def _extract_and_parse_json(content: str) -> dict:
    if not content:
        return {}
        
    match = re.search(r'\{[\s\S]*\}', content)
    if match:
        extracted_string = match.group(0)
        try:
            return json.loads(extracted_string)
        except Exception as e:
            print(f"JSON extraction failed: {e}")
            return {}
    else:
        print("JSON extraction failed: No JSON block found in response.")
        return {}

async def ask_llm_json(system_prompt: str, user_prompt: str) -> dict:
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openai":
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return _extract_and_parse_json(content)
        
    elif provider == "gemini":
        import google.generativeai as genai
        
        genai.configure(api_key=settings.LLM_API_KEY)
        model = genai.GenerativeModel('gemma-4-26b-a4b-it')
        
        prompt = f"System Instructions:\n{system_prompt}\n\nUser Request:\n{user_prompt}"
        
        response = await model.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        return _extract_and_parse_json(response.text)
        
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
