"""
Caseworker dashboard — GOV.UK styled Streamlit app.
Reads from data/ai_notes.json and provides filtering by risk level,
case type and status. Clicking a case shows full detail.
"""

import json
from pathlib import Path

import streamlit as st

DATA_PATH = Path(__file__).parent.parent / "data" / "ai_notes.json"

# ---------------------------------------------------------------------------
# GOV.UK design system styles injected via CSS
# ---------------------------------------------------------------------------

GOV_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=GDS+Transport&display=swap');

  /* Base */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #f3f2f1 !important;
  }
  [data-testid="stAppViewContainer"] > .main {
    background-color: #f3f2f1;
  }
  [data-testid="block-container"] {
    padding-top: 1.5rem;
    max-width: 1100px;
  }

  /* Typography */
  h1, h2, h3, h4 {
    font-family: "GDS Transport", arial, sans-serif !important;
    color: #0b0c0c;
  }
  p, li, label, span {
    font-family: arial, sans-serif;
    color: #0b0c0c;
  }

  /* Header bar */
  .govuk-header {
    background-color: #0b0c0c;
    padding: 10px 20px;
    margin-bottom: 24px;
    border-bottom: 10px solid #1d70b8;
  }
  .govuk-header__logotype {
    color: white;
    font-size: 1.1rem;
    font-weight: bold;
    font-family: arial, sans-serif;
  }

  /* Tags */
  .tag {
    display: inline-block;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: bold;
    font-family: arial, sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-radius: 2px;
  }
  .tag-red    { background: #d4351c; color: white; }
  .tag-yellow { background: #f47738; color: white; }
  .tag-green  { background: #00703c; color: white; }
  .tag-blue   { background: #1d70b8; color: white; }
  .tag-grey   { background: #505a5f; color: white; }

  /* Summary cards */
  .stat-card {
    background: white;
    border-left: 5px solid #1d70b8;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: arial, sans-serif;
  }
  .stat-card .stat-number {
    font-size: 2rem;
    font-weight: bold;
    color: #0b0c0c;
  }
  .stat-card .stat-label {
    font-size: 0.85rem;
    color: #505a5f;
  }
  .stat-card.red   { border-left-color: #d4351c; }
  .stat-card.amber { border-left-color: #f47738; }
  .stat-card.green { border-left-color: #00703c; }

  /* Case card */
  .case-card {
    background: white;
    border: 1px solid #b1b4b6;
    border-left: 5px solid #1d70b8;
    padding: 16px;
    margin-bottom: 12px;
    font-family: arial, sans-serif;
  }
  .case-card.high   { border-left-color: #d4351c; }
  .case-card.medium { border-left-color: #f47738; }
  .case-card.low    { border-left-color: #00703c; }
  .case-card h3 {
    margin: 0 0 4px 0;
    font-size: 1rem;
    font-weight: bold;
    color: #1d70b8;
  }
  .case-card .meta {
    font-size: 0.8rem;
    color: #505a5f;
    margin-bottom: 8px;
  }
  .case-card .ai-summary {
    font-size: 0.9rem;
    color: #0b0c0c;
    border-top: 1px solid #f3f2f1;
    padding-top: 8px;
    margin-top: 8px;
  }
  .case-card .next-action {
    font-size: 0.85rem;
    background: #e8f4fc;
    border-left: 3px solid #1d70b8;
    padding: 6px 10px;
    margin-top: 8px;
  }

  /* Timeline */
  .timeline-item {
    border-left: 3px solid #b1b4b6;
    padding: 4px 0 8px 12px;
    margin-bottom: 0;
    font-size: 0.85rem;
    font-family: arial, sans-serif;
    position: relative;
  }
  .timeline-item::before {
    content: '';
    width: 10px; height: 10px;
    background: #1d70b8;
    border-radius: 50%;
    position: absolute;
    left: -7px;
    top: 6px;
  }
  .timeline-date { font-weight: bold; color: #0b0c0c; }
  .timeline-event { color: #505a5f; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
  .timeline-note { color: #0b0c0c; }

  /* Divider */
  .govuk-divider {
    border: none;
    border-top: 1px solid #b1b4b6;
    margin: 16px 0;
  }

  /* Selectbox / filter labels */
  [data-testid="stSelectbox"] label {
    font-weight: bold;
    font-size: 0.85rem;
    font-family: arial, sans-serif;
    color: #0b0c0c;
  }

  /* Expander */
  [data-testid="stExpander"] {
    border: 1px solid #b1b4b6 !important;
    border-radius: 0 !important;
    background: white !important;
  }
</style>
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATUS_LABELS = {
    "awaiting_evidence": "Awaiting evidence",
    "under_review": "Under review",
    "escalated": "Escalated",
    "pending_decision": "Pending decision",
    "closed": "Closed",
}

CASE_TYPE_LABELS = {
    "benefit_review": "Benefit review",
    "licence_application": "Licence application",
    "compliance_check": "Compliance check",
}

RISK_COLOURS = {"high": "red", "medium": "yellow", "low": "green"}
RISK_TAG_CLASS = {"high": "tag-red", "medium": "tag-yellow", "low": "tag-green"}
STATUS_TAG_CLASS = {
    "awaiting_evidence": "tag-yellow",
    "under_review": "tag-blue",
    "escalated": "tag-red",
    "pending_decision": "tag-grey",
    "closed": "tag-green",
}


def normalise_next_action(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        parts = [f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in val.items()]
        return "; ".join(parts)
    return str(val) if val else ""


def risk_tag(level: str) -> str:
    cls = RISK_TAG_CLASS.get(level, "tag-grey")
    label = level.upper() if level else "UNKNOWN"
    return f'<span class="tag {cls}">{label}</span>'


def status_tag(status: str) -> str:
    cls = STATUS_TAG_CLASS.get(status, "tag-grey")
    label = STATUS_LABELS.get(status, status).upper()
    return f'<span class="tag {cls}">{label}</span>'


def type_tag(case_type: str) -> str:
    label = CASE_TYPE_LABELS.get(case_type, case_type).upper()
    return f'<span class="tag tag-blue">{label}</span>'


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@st.cache_data
def load_cases():
    with open(DATA_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Casework Dashboard", layout="wide", page_icon="⚖️")
st.markdown(GOV_CSS, unsafe_allow_html=True)

# GOV.UK style header
st.markdown("""
<div class="govuk-header">
  <span class="govuk-header__logotype">⚖️ &nbsp; MOJ Casework Dashboard</span>
</div>
""", unsafe_allow_html=True)

cases = load_cases()

# ---------------------------------------------------------------------------
# Summary stats
# ---------------------------------------------------------------------------

total = len(cases)
high = sum(1 for c in cases if c.get("ai_risk_level") == "high")
medium = sum(1 for c in cases if c.get("ai_risk_level") == "medium")
low = sum(1 for c in cases if c.get("ai_risk_level") == "low")
escalated = sum(1 for c in cases if c.get("status") == "escalated")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="stat-card"><div class="stat-number">{total}</div><div class="stat-label">Total cases</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card red"><div class="stat-number">{high}</div><div class="stat-label">High risk</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-card amber"><div class="stat-number">{medium}</div><div class="stat-label">Medium risk</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-card green"><div class="stat-number">{low}</div><div class="stat-label">Low risk</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="stat-card red"><div class="stat-number">{escalated}</div><div class="stat-label">Escalated</div></div>', unsafe_allow_html=True)

st.markdown('<hr class="govuk-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

all_statuses   = sorted({c["status"] for c in cases})
all_types      = sorted({c["case_type"] for c in cases})
all_risks      = ["high", "medium", "low"]

st.markdown("**Filter cases**")
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    filter_risk = st.selectbox(
        "Risk level",
        ["All"] + all_risks,
        format_func=lambda x: "All risk levels" if x == "All" else x.capitalize(),
    )
with fcol2:
    filter_type = st.selectbox(
        "Case type",
        ["All"] + all_types,
        format_func=lambda x: "All case types" if x == "All" else CASE_TYPE_LABELS.get(x, x),
    )
with fcol3:
    filter_status = st.selectbox(
        "Status",
        ["All"] + all_statuses,
        format_func=lambda x: "All statuses" if x == "All" else STATUS_LABELS.get(x, x),
    )

# Apply filters
filtered = [
    c for c in cases
    if (filter_risk   == "All" or c.get("ai_risk_level") == filter_risk)
    and (filter_type   == "All" or c["case_type"]         == filter_type)
    and (filter_status == "All" or c["status"]             == filter_status)
]

st.markdown(f"<p style='font-size:0.85rem;color:#505a5f;margin-bottom:8px;'>"
            f"Showing <strong>{len(filtered)}</strong> of <strong>{total}</strong> cases</p>",
            unsafe_allow_html=True)

st.markdown('<hr class="govuk-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Case list + detail
# ---------------------------------------------------------------------------

if not filtered:
    st.info("No cases match the current filters.")
else:
    left, right = st.columns([2, 3])

    with left:
        st.markdown("### Cases")
        selected_id = st.session_state.get("selected_case")

        for case in filtered:
            risk = case.get("ai_risk_level", "")
            colour = RISK_COLOURS.get(risk, "")
            card_html = f"""
            <div class="case-card {colour}">
              <h3>{case['case_id']}</h3>
              <div class="meta">
                {type_tag(case['case_type'])} &nbsp;
                {status_tag(case['status'])} &nbsp;
                {risk_tag(risk)}
              </div>
              <div style="font-size:0.8rem;color:#505a5f;">
                Last updated: {case.get('last_updated','—')}
              </div>
              <div class="ai-summary">{case.get('ai_summary','No summary available.')}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(f"View {case['case_id']}", key=f"btn_{case['case_id']}"):
                st.session_state["selected_case"] = case["case_id"]
                st.rerun()

    with right:
        selected_id = st.session_state.get("selected_case")
        selected = next((c for c in filtered if c["case_id"] == selected_id), None)

        if selected is None and filtered:
            selected = filtered[0]

        if selected:
            risk = selected.get("ai_risk_level", "")
            st.markdown(f"### {selected['case_id']}")
            st.markdown(
                f"{type_tag(selected['case_type'])} &nbsp;"
                f"{status_tag(selected['status'])} &nbsp;"
                f"{risk_tag(risk)}",
                unsafe_allow_html=True,
            )
            st.markdown('<hr class="govuk-divider">', unsafe_allow_html=True)

            # AI panel
            st.markdown("#### 🤖 AI summary")
            st.markdown(
                f"<div style='background:white;border-left:4px solid #1d70b8;padding:12px 16px;"
                f"font-family:arial,sans-serif;font-size:0.9rem;color:#0b0c0c;margin-bottom:12px;'>"
                f"{selected.get('ai_summary','No summary available.')}</div>",
                unsafe_allow_html=True,
            )

            next_action = normalise_next_action(selected.get("ai_next_action", ""))
            if next_action:
                st.markdown(
                    f"<div style='background:#e8f4fc;border-left:4px solid #1d70b8;padding:10px 14px;"
                    f"font-family:arial,sans-serif;font-size:0.85rem;margin-bottom:16px;'>"
                    f"<strong>Suggested next action:</strong><br>{next_action}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown('<hr class="govuk-divider">', unsafe_allow_html=True)

            # Timeline
            st.markdown("#### Timeline")
            for event in selected.get("timeline", []):
                st.markdown(
                    f"<div class='timeline-item'>"
                    f"<span class='timeline-date'>{event['date']}</span> "
                    f"<span class='timeline-event'>&nbsp;{event['event'].replace('_',' ')}</span><br>"
                    f"<span class='timeline-note'>{event['note']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.markdown('<hr class="govuk-divider">', unsafe_allow_html=True)

            # Required actions checklist
            st.markdown("#### Required actions")
            for action in selected.get("required_actions", []):
                st.markdown(
                    f"<div style='font-family:arial,sans-serif;font-size:0.85rem;"
                    f"padding:4px 0 4px 12px;border-left:3px solid #00703c;margin-bottom:6px;'>"
                    f"✔ {action}</div>",
                    unsafe_allow_html=True,
                )

            # Case notes (collapsible)
            with st.expander("Case notes"):
                st.markdown(
                    f"<p style='font-family:arial,sans-serif;font-size:0.85rem;'>"
                    f"{selected.get('case_notes','')}</p>",
                    unsafe_allow_html=True,
                )

            # Escalation thresholds
            thresholds = selected.get("escalation_thresholds", {})
            if thresholds:
                with st.expander("Escalation thresholds"):
                    for k, v in thresholds.items():
                        st.markdown(
                            f"<p style='font-family:arial,sans-serif;font-size:0.85rem;'>"
                            f"<strong>{k.replace('_',' ').capitalize()}:</strong> {v} days</p>",
                            unsafe_allow_html=True,
                        )
        else:
            st.info("Select a case on the left to view its details.")
