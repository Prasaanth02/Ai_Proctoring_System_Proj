from dotenv import load_dotenv
load_dotenv()
import os, json
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL'))

MODEL = 'nvidia/nemotron-3-super-120b-a12b:free'

SYSTEM = """You are a business analyst assistant.
Extract business requirements information from the provided text chunk.

Return ONLY a valid JSON object with exactly these keys:
{
  "business_problem": [],
  "objectives": [],
  "stakeholders": [],
  "functional_requirements": [],
  "non_functional_requirements": [],
  "business_rules": [],
  "assumptions": [],
  "constraints": [],
  "dependencies": [],
  "risks": [],
  "success_criteria": []
}

Rules:
- Each value must be a list of plain strings.
- Extract ONLY information explicitly present in the text.
- Do NOT invent or hallucinate requirements.
- If a category has no information in the text, return an empty list [].
- Do NOT wrap the JSON in markdown code fences.
- Output raw JSON only."""

TEXT = """
The company needs a leave management system. Employees should be able to apply for leave online.
Managers must approve or reject requests within 2 business days.
The system must be available 99.9% of the time.
Key stakeholders include HR Manager, Employees, and IT Department.
The system must integrate with the existing payroll system.
Risk: Low user adoption if the interface is not intuitive.
"""

print(f"Testing: {MODEL}\n")
r = client.chat.completions.create(
    model=MODEL,
    messages=[
        {'role': 'system', 'content': SYSTEM},
        {'role': 'user', 'content': f'Text chunk:\n\n{TEXT}'},
    ],
    temperature=0.0,
    max_tokens=1000,
    timeout=40,
)
reply = r.choices[0].message.content or ''
print("Raw reply:")
print(reply[:500])
print("\n--- Trying to parse JSON ---")
start = reply.rfind('{')
end = reply.rfind('}') + 1
if start != -1:
    try:
        parsed = json.loads(reply[start:end])
        print("Parsed OK:")
        for k, v in parsed.items():
            if v:
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"Parse failed: {e}")
else:
    print("No JSON found in reply")
