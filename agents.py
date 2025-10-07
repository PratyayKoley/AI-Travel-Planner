import re
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# =============================
# 🔐 API KEYS & ENDPOINTS
# =============================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
COHERE_API_URL = "https://api.cohere.ai/v2/chat"

# =============================
# 🧠 GENERIC LLM CALLS
# =============================
def call_groq(prompt, model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=1200):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    if r.status_code != 200:
        raise Exception(f"Groq API error: {r.status_code}, {r.text}")
    return r.json()["choices"][0]["message"]["content"]

def call_cohere(prompt, model="command-a-03-2025", temperature=0.7, max_tokens=500):
    headers = {"Authorization": f"Bearer {COHERE_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    r = requests.post(COHERE_API_URL, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise Exception(f"Cohere API error: {r.status_code}, {r.text}")

    response = r.json()
    # v2/chat returns text at response["message"]["content"][0]["text"]
    try:
        return response["message"]["content"][0]["text"]
    except Exception as e:
        raise Exception(f"Unexpected Cohere response: {json.dumps(response, indent=2)}") from e


# =============================
# 🧩 UTILITY: Extract JSON
# =============================
def extract_json(text, is_array=False):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    match = re.search(r'\[.*\]' if is_array else r'\{.*\}', text, re.DOTALL)
    if not match:
        raise Exception(f"No JSON found in: {text[:300]}")
    json_str = match.group(0)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    return json.loads(json_str)

# =============================
# 🤖 AGENTS
# =============================

class QueryResolverAgent:
    def __init__(self, llm="cohere"):
        print("\n[AGENT 1: Query Resolver - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_cohere(prompt, model="command-r-08-2024")

    def resolve_query(self, query):
        print(f"Query: {query}")
        prompt = f"""Extract structured info from: "{query}"
Return valid JSON: {{"state":"name","city":"name","days":3,"budget":10000,"style":"balanced"}}"""
        content = self.call_model(prompt)
        extracted = extract_json(content, is_array=False)

        dest_prompt = f"""List 5 tourist places in {extracted['city']}, {extracted['state']}.
Return JSON array: [{{"name":"Place 1"}},{{"name":"Place 2"}}]"""
        dest_content = call_groq(dest_prompt, model="qwen/qwen3-32b")
        places = extract_json(dest_content, is_array=True)

        destinations = [{"name": p.get("name","Unknown"), "city": extracted['city']} for p in places[:5]]
        return {**extracted, "destinations": destinations}


class PlannerAgent:
    def __init__(self, llm="groq"):
        print("\n[AGENT 2: Planner - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_groq(prompt, model="llama-3.3-70b-versatile")

    def create_itineraries(self, resolved):
        city = resolved['city']
        days = resolved['days']
        places = [d['name'] for d in resolved['destinations'][:3]]
        plans = []
        for name, style in [("Relaxed","relaxed"),("Balanced","balanced"),("Packed","packed")]:
            prompt = f"""Create a {days}-day itinerary for {city}, visiting {', '.join(places)}.
Return JSON: {{"name":"{name}","style":"{style}","days":{days},"daywise":[{{"day":1,"place":"{places[0]}","activities":["Visit {places[0]}"]}}]}}"""
            content = self.call_model(prompt)
            plans.append(extract_json(content, is_array=False))
        return plans


class CostAgent:
    def __init__(self, llm="groq"):
        print("\n[AGENT 3: Cost Estimator - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_groq(prompt, model="qwen/qwen3-32b")

    def estimate_costs(self, resolved, plans):
        city, days = resolved['city'], resolved['days']
        prompt = f"""Estimate typical daily travel costs in {city}. Return JSON:
{{"accommodation":1500,"food":800,"transport":500,"activities":1000}}"""
        daily = extract_json(self.call_model(prompt), is_array=False)
        costed = []
        for plan in plans:
            mult = {"relaxed":0.85,"balanced":1.0,"packed":1.2}.get(plan["style"],1)
            breakdown = {
                "accommodation": daily['accommodation']*days,
                "food": daily['food']*days,
                "transport": daily['transport']*days,
                "activities": int(daily['activities']*days*mult)
            }
            total = sum(breakdown.values())
            costed.append({
                "plan_name": plan["name"],
                "estimated_cost": total,
                "within_budget": total <= resolved['budget'],
                "breakdown": breakdown,
                "plan": plan
            })
        return sorted(costed, key=lambda x: x["estimated_cost"])


class SummarizerAgent:
    def __init__(self, llm="cohere"):
        print("\n[AGENT 4: Summarizer - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_cohere(prompt, model="command-r-plus-08-2024")

    def generate_summary(self, resolved, costed):
        best = costed[0]
        base_summary = f"""
Destination: {resolved['city']}, {resolved['state']}
Days: {resolved['days']}, Budget: ₹{resolved['budget']}
Selected Plan: {best['plan_name']} — Total Cost: ₹{best['estimated_cost']:,}
Itinerary: {json.dumps(best['plan']['daywise'], indent=2)}
"""
        prompt = f"Write a friendly, engaging travel summary in markdown based on this data:\n{base_summary}"
        return self.call_model(prompt)


# =============================
# 🧩 ORCHESTRATOR
# =============================
class MultiAgentOrchestrator:
    def __init__(self):
        print("\n🚀 INITIALIZING MULTI-MODEL AGENT SYSTEM\n")
        self.agent1 = QueryResolverAgent(llm="cohere")     # Cohere for structured parsing
        self.agent2 = PlannerAgent(llm="groq")             # Groq for itinerary planning
        self.agent3 = CostAgent(llm="groq")                # Groq for cost reasoning
        self.agent4 = SummarizerAgent(llm="cohere")        # Cohere for final summaries

    def process_query(self, query):
        resolved = self.agent1.resolve_query(query)
        plans = self.agent2.create_itineraries(resolved)
        costed = self.agent3.estimate_costs(resolved, plans)
        summary = self.agent4.generate_summary(resolved, costed)
        return summary
