import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str) -> list | dict:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def get_policy_body(case_type: str, policies: list[dict]) -> str:
    bodies = [p["body"] for p in policies if case_type in p.get("applicable_case_types", [])]
    return " ".join(bodies)


def get_workflow_state(case_type: str, status: str, workflow_states: dict) -> dict:
    states = workflow_states.get("case_types", {}).get(case_type, {}).get("states", [])
    return next((s for s in states if s["state"] == status), {})


def build_enriched_cases() -> list[dict]:
    cases = load_json("cases.json")
    policies = load_json("policy-extracts.json")
    workflow_states = load_json("workflow-states.json")

    enriched = []
    for case in cases:
        workflow_state = get_workflow_state(case["case_type"], case["status"], workflow_states)

        enriched.append({
            "case_id": case["case_id"],
            "case_type": case["case_type"],
            "status": case["status"],
            "created_date": case["created_date"],
            "last_updated": case["last_updated"],
            "timeline": case["timeline"],
            "case_notes": case["case_notes"],
            "policy_body": get_policy_body(case["case_type"], policies),
            "required_actions": workflow_state.get("required_actions", []),
            "escalation_thresholds": workflow_state.get("escalation_thresholds", {}),
        })

    return enriched


if __name__ == "__main__":
    enriched_cases = build_enriched_cases()
    output_path = DATA_DIR / "enriched_cases.json"
    with open(output_path, "w") as f:
        json.dump(enriched_cases, f, indent=2)
    print(f"Written {len(enriched_cases)} cases to {output_path}")
