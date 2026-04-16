"""
AI-powered case summarisation using direct Ollama API calls.

Generates a structured summary for each case from its notes, timeline,
and relevant policy. Uses Ollama (free, local, no API key).

To switch to AWS Bedrock, replace the generate_summaries body with a
laurium llm.create_llm call using llm_platform="bedrock".
"""

import json
import re
from pathlib import Path

import ollama

DATA_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = (
    "You are an assistant helping government caseworkers understand their cases. "
    "Given case notes, timeline, policy, and required actions, respond ONLY with "
    "a JSON object with exactly these keys: summary, next_action, risk_level. "
    'risk_level must be one of: "low", "medium", "high". '
    "No extra text, no markdown, just the JSON object."
)


def build_case_text(case: dict) -> str:
    """Serialise the relevant fields of a case into a single text block."""
    timeline_text = " ".join(
        f"{e['date']} {e['event']} — {e['note']}"
        for e in case.get("timeline", [])
    )
    actions_text = " ".join(case.get("required_actions", []))
    return (
        f"Case notes: {case.get('case_notes', '')}\n"
        f"Timeline: {timeline_text}\n"
        f"Policy: {case.get('policy_body', '')}\n"
        f"Required actions: {actions_text}"
    )


def summarise_case(case: dict, model_name: str) -> dict:
    response = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_case_text(case)},
        ],
        options={"temperature": 0},
    )
    raw = response["message"]["content"].strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": raw, "next_action": "", "risk_level": ""}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_summaries(model_name: str = "qwen2.5:0.5b") -> list[dict]:
    """
    Load enriched cases, run AI summarisation, and return cases with
    summary fields attached.

    model_name: any Ollama model you have pulled locally.
    """
    with open(DATA_DIR / "enriched_cases.json") as f:
        cases = json.load(f)

    cases = cases[:5]  # Process first 5 cases only

    for i, case in enumerate(cases, 1):
        print(f"  Summarising case {i}/5: {case['case_id']}...")
        ai = summarise_case(case, model_name)
        case["ai_summary"] = ai.get("summary", "")
        case["ai_next_action"] = ai.get("next_action", "")
        case["ai_risk_level"] = ai.get("risk_level", "")

    output_path = DATA_DIR / "ai_notes.json"
    with open(output_path, "w") as f:
        json.dump(cases, f, indent=2)

    print(f"Summaries written to {output_path}")
    return cases


if __name__ == "__main__":
    generate_summaries()
