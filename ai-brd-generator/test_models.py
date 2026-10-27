from dotenv import load_dotenv
load_dotenv()
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL'))

models = [
    'deepseek/deepseek-r1-0528:free',
    'deepseek/deepseek-chat-v3-0324:free',
    'deepseek/deepseek-r1:free',
    'meta-llama/llama-3.1-8b-instruct:free',
    'meta-llama/llama-3.2-3b-instruct:free',
    'microsoft/phi-3-mini-128k-instruct:free',
    'microsoft/phi-3-medium-128k-instruct:free',
    'google/gemma-3-12b-it:free',
    'google/gemma-3-4b-it:free',
    'qwen/qwen-2.5-7b-instruct:free',
    'mistralai/mistral-small-3.2-24b-instruct:free',
    'tngtech/deepseek-r1t-chimera:free',
]

print("Testing free models...\n")
for m in models:
    try:
        r = client.chat.completions.create(
            model=m,
            messages=[{'role': 'user', 'content': 'Reply with only the word: OK'}],
            max_tokens=10,
            timeout=20,
        )
        reply = (r.choices[0].message.content or '').strip()[:40]
        print(f"WORKS: {m}")
        print(f"       Reply: {reply}\n")
    except Exception as e:
        print(f"FAIL:  {m}")
        print(f"       Error: {str(e)[:80]}\n")
