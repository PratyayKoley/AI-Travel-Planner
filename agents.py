import re
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = True  # Toggle this to False to hide prints

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
    if DEBUG:
        print(f"\n🧩 [Groq Model: {model}] Prompt:\n{prompt[:600]}...\n")

    r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    if r.status_code != 200:
        raise Exception(f"Groq API error: {r.status_code}, {r.text}")
    
    result = r.json()["choices"][0]["message"]["content"]
    if DEBUG:
        print(f"🔹 [Groq Output]: {result[:1000]}...\n")
    return result


def call_cohere(prompt, model="command-a-03-2025", temperature=0.7, max_tokens=500):
    headers = {"Authorization": f"Bearer {COHERE_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    if DEBUG:
        print(f"\n🧩 [Cohere Model: {model}] Prompt:\n{prompt[:600]}...\n")

    r = requests.post(COHERE_API_URL, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise Exception(f"Cohere API error: {r.status_code}, {r.text}")

    response = r.json()
    try:
        result = response["message"]["content"][0]["text"]
        if DEBUG:
            print(f"🔹 [Cohere Output]: {result[:1000]}...\n")
        return result
    except Exception as e:
        raise Exception(f"Unexpected Cohere response: {json.dumps(response, indent=2)}") from e


# =============================
# 🧩 UTILITY: Extract JSON
# =============================
def extract_json(text, is_array=False):
    text = re.sub(r'```(?:json)?', '', text)
    text = text.strip()
    pattern = r'\[.*\]' if is_array else r'\{.*\}'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise Exception(f"No JSON found in: {text[:300]}")
    json_str = match.group(0)
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
    json_str = json_str.replace("\n", " ").replace("\r", " ").strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("\n⚠️ Invalid JSON detected:\n", json_str[:500])
        raise e


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
        print("\n========== 🌍 QUERY RESOLVER START ==========")
        print(f"User Query: {query}")

        prompt = f"""Extract structured info from: "{query}"
Return valid JSON: {{"state":"name","city":"name","days":3,"budget":10000,"style":"balanced"}}"""
        content = self.call_model(prompt)
        extracted = extract_json(content, is_array=False)

        for key in ["budget", "days"]:
            try:
                extracted[key] = int(extracted[key])
            except Exception:
                extracted[key] = 0

        dest_prompt = f"""List 5 tourist places in {extracted['city']}, {extracted['state']}.
Return JSON array: [{{"name":"Place 1"}},{{"name":"Place 2"}}]"""
        dest_content = call_groq(dest_prompt, model="qwen/qwen3-32b")
        places = extract_json(dest_content, is_array=True)

        destinations = [{"name": p.get("name", "Unknown"), "city": extracted['city']} for p in places[:5]]
        result = {**extracted, "destinations": destinations}

        print("✅ Parsed Query Data:\n", json.dumps(result, indent=2))
        print("========== 🌍 QUERY RESOLVER END ==========\n")
        return result


class PlannerAgent:
    def __init__(self, llm="groq"):
        print("\n[AGENT 2: Planner - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_groq(prompt, model="llama-3.3-70b-versatile")

    def create_itineraries(self, resolved):
        print("\n========== 🧭 ITINERARY PLANNER START ==========")
        city, days = resolved['city'], resolved['days']
        places = [d['name'] for d in resolved['destinations'][:3]]
        plans = []
        for name, style in [("Relaxed","relaxed"),("Balanced","balanced"),("Packed","packed")]:
            prompt = f"""
Create a detailed {days}-day itinerary for {city}, covering key attractions like {', '.join(places)}.
Return strictly valid JSON only in this format:

{{
  "name": "{name}",
  "style": "{style}",
  "days": {days},
  "daywise": [
    {{"day": 1, "place": "{places[0]}", "activities": ["Visit {places[0]}", "Explore nearby cafes"]}},
    {{"day": 2, "place": "{places[1]}", "activities": ["Sightseeing", "Try local food"]}}
  ]
}}
Make sure the itinerary has exactly {days} entries in the 'daywise' list (one per day).
"""
            content = self.call_model(prompt)
            plan = extract_json(content, is_array=False)
            if DEBUG:
                print(f"\n🗓️ [{name} PLAN OUTPUT]:\n", json.dumps(plan, indent=2)[:800])
            plans.append(plan)
        print("========== 🧭 ITINERARY PLANNER END ==========\n")
        return plans


class CostAgent:
    def __init__(self, llm="groq"):
        print("\n[AGENT 3: Cost Estimator - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_groq(prompt, model="qwen/qwen3-32b")

    def estimate_costs(self, resolved, plans):
        print("\n========== 💰 COST ESTIMATOR START ==========")
        city, days = resolved['city'], resolved['days']

        # Step 1: Ask LLM for daily baseline costs
        prompt = f"""Estimate typical daily travel costs in {city}. Return JSON:
{{"accommodation":1500,"food":800,"transport":500,"activities":1000}}"""
        daily = extract_json(self.call_model(prompt), is_array=False)

        costed = []

        # Step 2: Calculate cost plan-wise
        for plan in plans:
            style = plan["style"]
            mult = {"relaxed": 0.85, "balanced": 1.0, "packed": 1.2}.get(style, 1)

            # Base daily breakdown (multiplied by style intensity)
            daily_style_cost = {
                "accommodation": daily["accommodation"],
                "food": daily["food"],
                "transport": daily["transport"],
                "activities": int(daily["activities"] * mult)
            }

            # Step 3: Generate per-day cost breakdowns
            daywise_with_costs = []
            for day_item in plan["daywise"]:
                day_num = day_item["day"]
                # Simulate slightly varying daily costs
                variation = 0.9 + 0.2 * (day_num / days)
                per_day_cost = {
                    k: int(v * variation)
                    for k, v in daily_style_cost.items()
                }
                total_day_cost = sum(per_day_cost.values())
                day_item_with_cost = {
                    **day_item,
                    "daily_cost": total_day_cost,
                    "cost_breakdown": per_day_cost
                }
                daywise_with_costs.append(day_item_with_cost)

            # Step 4: Compute plan-level totals
            total = sum(d["daily_cost"] for d in daywise_with_costs)
            breakdown = {
                "accommodation": sum(d["cost_breakdown"]["accommodation"] for d in daywise_with_costs),
                "food": sum(d["cost_breakdown"]["food"] for d in daywise_with_costs),
                "transport": sum(d["cost_breakdown"]["transport"] for d in daywise_with_costs),
                "activities": sum(d["cost_breakdown"]["activities"] for d in daywise_with_costs)
            }

            plan["daywise"] = daywise_with_costs  # inject cost data into plan

            cost_data = {
                "plan_name": plan["name"],
                "estimated_cost": total,
                "within_budget": total <= resolved['budget'],
                "breakdown": breakdown,
                "plan": plan
            }

            costed.append(cost_data)
            if DEBUG:
                print(f"\n💸 [{plan['name']} Plan Daily & Total Costs]:\n", json.dumps(cost_data, indent=2)[:1000])

        print("========== 💰 COST ESTIMATOR END ==========\n")
        return sorted(costed, key=lambda x: x["estimated_cost"])



class SummarizerAgent:
    def __init__(self, llm="cohere"):
        print("\n[AGENT 4: Summarizer - Using", llm, "]")
        self.llm = llm

    def call_model(self, prompt):
        return call_cohere(prompt, model="command-r-plus-08-2024")

    def generate_summary(self, resolved, costed):
        print("\n========== 📝 SUMMARIZER START ==========")
        best = costed[0]
        base_summary = f"""
Destination: {resolved['city']}, {resolved['state']}
Days: {resolved['days']}, Budget: ₹{resolved['budget']}
Selected Plan: {best['plan_name']} — Total Cost: ₹{best['estimated_cost']:,}
Itinerary: {json.dumps(best['plan']['daywise'], indent=2)}
"""
        prompt = f"Write a friendly, engaging travel summary in markdown based on this data:\n{base_summary}"
        result = self.call_model(prompt)
        print("🪄 Generated Summary (Markdown):\n", result[:1000])
        print("========== 📝 SUMMARIZER END ==========\n")
        return result


# =============================
# 🧩 ORCHESTRATOR
# =============================
class MultiAgentOrchestrator:
    def __init__(self):
        print("\n🚀 INITIALIZING MULTI-MODEL AGENT SYSTEM\n")
        self.agent1 = QueryResolverAgent()
        self.agent2 = PlannerAgent()
        self.agent3 = CostAgent()
        self.agent4 = SummarizerAgent()

    def process_query(self, query):
        print("\n============== 🌐 ORCHESTRATION START ==============\n")
        resolved = self.agent1.resolve_query(query)
        plans = self.agent2.create_itineraries(resolved)
        costed = self.agent3.estimate_costs(resolved, plans)
        summary = self.agent4.generate_summary(resolved, costed)
        print("\n============== ✅ ORCHESTRATION COMPLETE ==============\n")
        return summary