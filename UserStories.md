# User stories

## Roles

| Role        | Description                                      |
| ----------- | ------------------------------------------------ |
| Caseworker  | Processes benefit review cases day to day         |
| Team Leader | Manages a team of caseworkers and monitors risk   |
| Developer   | Builds and maintains the prototype                |

> **Out of scope for this prototype:** Applicant-facing status view (see requirement 7). Flagged as a future requirement.

---

## Requirement 1: Case list dashboard

**User story**

> As a **Caseworker**, I want to see all my assigned cases in a single dashboard, so that I can quickly identify which cases need attention.

**Acceptance criteria**

- [ ] Dashboard displays all cases assigned to the logged-in caseworker
- [ ] Each case row shows: reference number, applicant name, benefit type, current status, and deadline date
- [ ] Cases are sorted by deadline (nearest first) by default
- [ ] Caseworker can re-sort by status or date received
- [ ] Cases approaching their deadline (within 5 working days) display an amber warning tag
- [ ] Cases past their deadline display a red warning tag
- [ ] Selecting a case navigates to the case detail view
- [ ] Dashboard shows a count of total assigned cases and how many need action

---

## Requirement 2: Case detail view

**User story**

> As a **Caseworker**, I want to see all information about a single case in one place, so that I can understand the case without switching between multiple systems.

**Acceptance criteria**

- [ ] Case detail page shows a summary header: reference number, applicant name, benefit type, status, and assigned caseworker
- [ ] Applicant details section displays: name, date of birth, contact information, and representative (if any)
- [ ] Case history section shows a timeline of key events in reverse chronological order (newest first)
- [ ] Evidence section lists all documents grouped by the legal criterion they relate to
- [ ] Each piece of evidence shows: document name, source, date received, and which criterion it supports
- [ ] Missing evidence is clearly indicated with a "not yet received" marker against the relevant criterion
- [ ] A back link returns the caseworker to the dashboard

---

## Requirement 3: Policy matching and display

**User story**

> As a **Caseworker**, I want to see the relevant policy guidance automatically matched to my case, so that I can apply the correct rules without searching through a 40-page document.

**Acceptance criteria**

- [ ] Policy guidance is automatically matched based on the case's benefit type and review grounds
- [ ] Matched policy sections are displayed alongside the case detail view (not on a separate page)
- [ ] Each policy section shows: the legal criterion, a plain-English summary of the rule, and a reference to the source legislation
- [ ] Only the criteria relevant to the current case are shown (not the full policy document)
- [ ] If no matching policy is found, a message tells the caseworker to consult the full guidance manually

---

## Requirement 4: Workflow position and next actions

**User story**

> As a **Caseworker**, I want to see where my case is in the process and what actions I can take next, so that I can move the case forward without guessing.

**Acceptance criteria**

- [ ] A workflow tracker shows all steps in the review process for this case type
- [ ] The current step is clearly highlighted
- [ ] Completed steps are marked as done with a completion date
- [ ] Future steps are shown but not actionable
- [ ] Available next actions are displayed as buttons (for example, "Request evidence", "Record decision", "Escalate")
- [ ] Taking an action updates the workflow position and case status
- [ ] Mandatory steps cannot be skipped

---

## Requirement 5: Deadline detection and alerts

**User story**

> As a **Caseworker**, I want to be alerted when evidence is overdue or deadlines are approaching, so that I do not miss important dates and applicants are not left waiting.

**Acceptance criteria**

- [ ] Cases approaching their SLA deadline (within 5 working days) show an amber warning tag on the dashboard and case detail view
- [ ] Cases past their SLA deadline show a red "overdue" tag on the dashboard and case detail view
- [ ] Evidence requests that have not been returned within the expected timeframe are flagged as overdue on the case detail view
- [ ] The dashboard shows a summary count of cases at risk and cases overdue
- [ ] Deadline dates are calculated from the data and displayed in the format "6 September 2024"

---

## Requirement 6: Team leader overview

**User story**

> As a **Team Leader**, I want to see a high-level overview of all cases across my team, so that I can identify cases at risk of breaching deadlines and manage team capacity.

**Acceptance criteria**

- [ ] Overview page shows all cases across the team (not filtered to one caseworker)
- [ ] Summary statistics displayed at the top: total open cases, cases at risk, cases overdue, cases closed this week
- [ ] Cases can be filtered by caseworker, status, or benefit type
- [ ] A workload summary shows how many open cases each caseworker has
- [ ] Team leader can select any case to view its full detail
- [ ] Cases at risk or overdue are visually prominent

---

## Requirement 7: Applicant status view (future requirement)

**User story**

> As an **Applicant**, I want to check the status of my case, so that I know where my case is in the process and what is expected of me.

**Status:** Out of scope for this prototype. Flagged for future development.

---

## Requirement 8: AI advisor integration points

**User story**

> As a **Caseworker**, I want AI-generated summaries and recommended next actions, so that I can understand complex cases faster and make better decisions.

**Acceptance criteria**

- [ ] Each case displays a simulated AI-generated plain-English summary of the case (loaded from JSON data)
- [ ] Each case displays simulated recommended next actions based on the current workflow position and evidence status
- [ ] AI suggestions are clearly labelled as AI-generated (for example, with a tag or prefix)
- [ ] The caseworker can see the suggestion but is not required to follow it
- [ ] Suggestions include a confidence indicator (for example, high, medium, low)

---

## Requirement 9: Data loading and parsing

**User story**

> As a **Developer**, I want the application to load and parse the provided JSON data files, so that all case, policy, and workflow data is available to the application.

**Acceptance criteria**

- [ ] Application reads case data from `app/data/cases.json` at startup
- [ ] Application reads policy data from `app/data/policies.json` at startup
- [ ] Application reads workflow data from `app/data/workflows.json` at startup
- [ ] Data is available to routes and templates via standard Prototype Kit data mechanisms
- [ ] Missing or malformed data does not crash the application

---

## Requirement 10: Responsive web interface

**User story**

> As a **Caseworker**, I want to use the tool on different screen sizes, so that I can access case information from a desktop or tablet.

**Acceptance criteria**

- [ ] Layout uses the GOV.UK grid system (`govuk-grid-row`, `govuk-grid-column-*`)
- [ ] Content reflows correctly at desktop (1024px+), tablet (768px), and mobile (320px) widths
- [ ] Tables use responsive patterns or are replaced with summary lists on small screens
- [ ] All interactive elements (buttons, links, form controls) are usable on touch devices
- [ ] No horizontal scrolling at any supported screen width
