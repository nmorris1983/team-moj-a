from data_preprocessing import build_enriched_cases
from ai_summary import generate_summaries
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    print("Step 1: Building enriched cases...")
    enriched_cases = build_enriched_cases()
    output_path = DATA_DIR / "enriched_cases.json"
    with open(output_path, "w") as f:
        json.dump(enriched_cases, f, indent=2)
    print(f"  Written {len(enriched_cases)} cases to {output_path}")

    print("Step 2: Generating AI summaries with qwen2.5:0.5b...")
    cases_with_summaries = generate_summaries(model_name="qwen2.5:0.5b")
    print(f"  Done. {len(cases_with_summaries)} cases enriched with AI summaries.")
    print(f"  Output: {DATA_DIR / 'ai_notes.json'}")


if __name__ == "__main__":
    main()
