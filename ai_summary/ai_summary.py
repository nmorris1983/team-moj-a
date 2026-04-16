"""
AI-powered case summarisation.

Primary path:  laurium BatchExtractor (structured extraction with retries,
               few-shot examples, and Pydantic validation).
Fallback path: direct Ollama API call (lightweight, no extra dependencies).

The fallback activates automatically if laurium fails for any reason.

To use AWS Bedrock instead of Ollama, pass llm_platform="bedrock" to
generate_summaries() — laurium handles that transparently.
"""

import json
import re
from pathlib import Path
from typing import Literal

import ollama
import pandas as pd
from langchain_core.output_parsers import PydanticOutputParser
from laurium.decoder_models import extract, llm, pydantic_models, prompts

DATA_DIR = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Shared schema
# ---------------------------------------------------------------------------

SCHEMA = {
    "summary": str,
    "next_action": str,
    "risk_level": Literal["low", "medium", "high"],
}

DESCRIPTIONS = {
    "summary": "A 2-3 sentence plain-English summary of where this case is and why, written for a caseworker picking it up for the first time.",
    "next_action": "The single most important action the caseworker should take right now, based on the case status and policy.",
    "risk_level": "Overall risk level: high if escalated or deadline breached, medium if a reminder is due or decision is stale, low otherwise.",
}

FEW_SHOT_EXAMPLES = [
    {
        "text": (
            "Case notes: Applicant relocated from Birmingham to Manchester in December 2025. "
            "Previous claim under reference REF-55102 was closed in November 2025. "
            "New claim opened due to change of circumstances. "
            "Awaiting income statement — applicant stated employer has been contacted.\n"
            "Timeline: 2026-01-10 case_created — Initial application received via online portal. "
            "2026-01-15 evidence_requested — Requested proof of address and income statement. "
            "2026-02-02 evidence_received — Proof of address received. Income statement still outstanding.\n"
            "Policy: When a benefit review is triggered by a change of circumstances, the caseworker must obtain "
            "proof of new address, an income statement, and a signed declaration. "
            "Issue a reminder if evidence is outstanding after 28 days. Escalate after 56 days.\n"
            "Required actions: Send evidence request to applicant. Issue reminder if evidence outstanding after 28 days. "
            "Escalate to team leader if evidence outstanding after 56 days."
        ),
        "summary": (
            "This benefit review was triggered by a change of address. "
            "Proof of address has been received but the income statement remains outstanding. "
            "The evidence request was made on 15 January and has now been outstanding for over 28 days."
        ),
        "next_action": "Issue a reminder to the applicant for the outstanding income statement as the 28-day threshold has been reached.",
        "risk_level": "medium",
    }
]

SYSTEM_PROMPT = (
    "You are an assistant helping government caseworkers understand their cases. "
    "Given case notes, timeline, policy, and required actions, respond ONLY with "
    "a JSON object with exactly these keys: summary, next_action, risk_level. "
    'risk_level must be one of: "low", "medium", "high". '
    "No extra text, no markdown, just the JSON object."
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Primary path: laurium BatchExtractor
# ---------------------------------------------------------------------------

def _create_laurium_extractor(case_llm) -> extract.BatchExtractor:
    system_message = prompts.create_system_message(
        base_message=(
            "You are an assistant helping government caseworkers understand their cases. "
            "Given the case notes, timeline, policy, and required actions for a case, "
            "produce a concise structured summary."
        ),
        keywords=["evidence", "deadline", "escalate", "outstanding", "reminder", "decision"],
    )
    extraction_prompt = prompts.create_prompt(
        system_message=system_message,
        examples=FEW_SHOT_EXAMPLES,
        example_human_template="Case: {text}",
        example_assistant_template=(
            '{{"summary": "{summary}", "next_action": "{next_action}", "risk_level": "{risk_level}"}}'
        ),
        final_query="Case: {text}",
        schema=SCHEMA,
        descriptions=DESCRIPTIONS,
    )
    OutputModel = pydantic_models.make_dynamic_example_model(
        schema=SCHEMA,
        descriptions=DESCRIPTIONS,
        model_name="CaseSummary",
    )
    parser = PydanticOutputParser(pydantic_object=OutputModel)
    return extract.BatchExtractor(
        llm=case_llm,
        prompt=extraction_prompt,
        parser=parser,
        max_concurrency=1,
    )


def _summarise_with_laurium(cases: list[dict], model_name: str) -> list[dict]:
    """Run laurium BatchExtractor over cases. Returns cases with ai_ fields set."""
    print("  Using laurium BatchExtractor...")
    case_llm = llm.create_llm(
        llm_platform="ollama",
        model_name=model_name,
        temperature=0.0,
    )
    extractor = _create_laurium_extractor(case_llm)
    df = pd.DataFrame([{"case_id": c["case_id"], "text": build_case_text(c)} for c in cases])
    results = extractor.process_chunk(df, text_column="text")
    results_map = results.set_index("case_id").to_dict(orient="index")
    for case in cases:
        ai = results_map.get(case["case_id"], {})
        case["ai_summary"] = ai.get("summary", "")
        case["ai_next_action"] = ai.get("next_action", "")
        case["ai_risk_level"] = ai.get("risk_level", "")
    return cases


# ---------------------------------------------------------------------------
# Fallback path: direct Ollama API
# ---------------------------------------------------------------------------

def _summarise_case_ollama(case: dict, model_name: str) -> dict:
    response = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_case_text(case)},
        ],
        options={"temperature": 0},
    )
    raw = response["message"]["content"].strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": raw, "next_action": "", "risk_level": ""}


def _summarise_with_ollama(cases: list[dict], model_name: str) -> list[dict]:
    """Fallback: call Ollama directly, one case at a time."""
    print("  Using direct Ollama API (fallback)...")
    for i, case in enumerate(cases, 1):
        print(f"    Case {i}/{len(cases)}: {case['case_id']}...")
        ai = _summarise_case_ollama(case, model_name)
        case["ai_summary"] = ai.get("summary", "")
        case["ai_next_action"] = ai.get("next_action", "")
        case["ai_risk_level"] = ai.get("risk_level", "")
    return cases


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_summaries(model_name: str = "qwen2.5:0.5b") -> list[dict]:
    """
    Load enriched cases, run AI summarisation, and return cases with
    summary fields attached.

    Tries laurium first for structured extraction with validation.
    Falls back to direct Ollama calls if laurium fails.

    model_name: any Ollama model you have pulled locally.

    To use AWS Bedrock instead of Ollama, replace the laurium call with:
        llm.create_llm(
            llm_platform="bedrock",
            model_name="anthropic.claude-3-5-sonnet-20241022-v2:0",
            temperature=0.0,
            aws_region_name="eu-west-2",
        )
    """
    with open(DATA_DIR / "enriched_cases.json") as f:
        cases = json.load(f)

    try:
        cases = _summarise_with_laurium(cases, model_name)
    except Exception as e:
        print(f"  laurium failed ({e}), falling back to direct Ollama...")
        cases = _summarise_with_ollama(cases, model_name)

    output_path = DATA_DIR / "ai_notes.json"
    with open(output_path, "w") as f:
        json.dump(cases, f, indent=2)

    print(f"Summaries written to {output_path}")
    return cases


if __name__ == "__main__":
    generate_summaries()
