# Requirements Document

## Introduction

A web-based casework decision support tool for government caseworkers. The tool helps caseworkers quickly understand case status, surface relevant policy guidance, track workflow position, flag overdue deadlines, and identify next actions — replacing the current fragmented experience of juggling multiple systems, lengthy documents, and scattered notes.

This is a hackathon prototype built in one day. It loads synthetic data from JSON files (cases, policies, workflow states) and presents a clear, actionable interface. The architecture is designed so that mocked AI endpoints can be replaced by real language model calls later.

## Glossary

- **Dashboard**: The main screen showing an overview of all cases with key metrics and alerts
- **Case_Viewer**: The component that displays a single case's full details, timeline, notes, and related policy
- **Policy_Engine**: The module that matches and surfaces relevant policy extracts based on case type and status
- **Workflow_Tracker**: The module that determines a case's position in its workflow state machine and computes next valid actions
- **Deadline_Monitor**: The module that calculates deadline status (on-time, approaching, overdue) based on timeline events and policy rules
- **Timeline_Display**: The component that renders a case's chronological event history with context
- **AI_Advisor**: The module (initially mocked) that provides AI-generated case summaries and recommended next actions
- **Caseworker**: A government employee managing 20-40 active cases who needs to understand cases quickly and apply correct policy
- **Team_Leader**: A manager responsible for 200-300 cases across a team, needing visibility into deadline risks and capacity
- **Applicant**: A citizen waiting for a decision on their case

## Requirements

### Requirement 1: Case List Dashboard

**User Story:** As a Caseworker, I want to see all my assigned cases in a single dashboard, so that I can quickly identify which cases need attention.

#### Acceptance Criteria

1. WHEN the Caseworker opens the Dashboard, THE Dashboard SHALL load case data from the cases.json file and display all cases in a list view.
2. THE Dashboard SHALL display for each case: the case_id, case_type, current status, applicant name, date last updated, and deadline status.
3. WHEN a case has an overdue deadline, THE Dashboard SHALL display a visual indicator (red badge) next to that case.
4. WHEN a case has a deadline approaching within 7 days, THE Dashboard SHALL display a visual indicator (amber badge) next to that case.
5. WHEN the Caseworker selects a case from the Dashboard, THE Dashboard SHALL navigate to the Case_Viewer for that case.
6. THE Dashboard SHALL allow the Caseworker to filter cases by case_type (benefit_review, licence_application, compliance_check).
7. THE Dashboard SHALL allow the Caseworker to filter cases by status (e.g., awaiting_evidence, in_review, escalated).

### Requirement 2: Case Detail View

**User Story:** As a Caseworker, I want to see all information about a single case in one place, so that I can understand the case without switching between multiple systems.

#### Acceptance Criteria

1. WHEN the Caseworker opens a case, THE Case_Viewer SHALL display the case_id, case_type, status, applicant name, applicant reference, created date, and last updated date.
2. WHEN the Caseworker opens a case, THE Case_Viewer SHALL display all case_notes in a readable, formatted section.
3. WHEN the Caseworker opens a case, THE Case_Viewer SHALL display the full timeline of events in chronological order using the Timeline_Display.
4. THE Timeline_Display SHALL show for each event: the date, event type, and associated note.
5. WHEN the Caseworker opens a case, THE Case_Viewer SHALL display the workflow position and next valid actions (provided by the Workflow_Tracker).
6. WHEN the Caseworker opens a case, THE Case_Viewer SHALL display relevant policy extracts (provided by the Policy_Engine).

### Requirement 3: Policy Matching and Display

**User Story:** As a Caseworker, I want to see the relevant policy guidance alongside my case, so that I can apply the correct rules without searching through a 40-page document.

#### Acceptance Criteria

1. WHEN the Caseworker opens a case, THE Policy_Engine SHALL match policy extracts from policy-extracts.json where the policy's applicable_case_types includes the case's case_type.
2. THE Policy_Engine SHALL return all matching policy extracts, ordered by relevance to the case's current status.
3. THE Case_Viewer SHALL display matched policy extracts in a dedicated "Applicable Policy" section, showing the policy title and body text.
4. IF no matching policy extracts are found for a case type, THEN THE Case_Viewer SHALL display a message stating "No specific policy guidance found for this case type."

### Requirement 4: Workflow Position and Next Actions

**User Story:** As a Caseworker, I want to see where my case is in the process and what actions I can take next, so that I can move the case forward without guessing.

#### Acceptance Criteria

1. WHEN the Caseworker opens a case, THE Workflow_Tracker SHALL load the workflow state machine from workflow-states.json for the case's case_type.
2. THE Workflow_Tracker SHALL determine the case's current position in the state machine based on the case's status field.
3. THE Workflow_Tracker SHALL compute the list of valid next transitions from the current state.
4. THE Case_Viewer SHALL display the current workflow state prominently, along with a list of valid next actions the Caseworker can take.
5. THE Case_Viewer SHALL display a visual representation of the workflow state machine, highlighting the current state.

### Requirement 5: Deadline Detection and Alerts

**User Story:** As a Caseworker, I want to be alerted when evidence is overdue or deadlines are approaching, so that I do not miss important dates and applicants are not left waiting.

#### Acceptance Criteria

1. WHEN a case has an evidence_requested event in its timeline and no corresponding evidence_received event within 28 days, THE Deadline_Monitor SHALL flag the case as "evidence approaching deadline."
2. WHEN a case has an evidence_requested event in its timeline and no corresponding evidence_received event within 56 days, THE Deadline_Monitor SHALL flag the case as "evidence overdue — escalation required."
3. THE Deadline_Monitor SHALL calculate the number of days since the last update for each case.
4. WHEN a case has not been updated for more than 14 days, THE Deadline_Monitor SHALL flag the case as "stale — requires attention."
5. THE Dashboard SHALL display a summary count of overdue cases, approaching-deadline cases, and stale cases at the top of the page.


### Requirement 6: Team Leader Overview

**User Story:** As a Team_Leader, I want to see a high-level overview of all cases across my team, so that I can identify cases at risk of breaching deadlines and manage team capacity.

#### Acceptance Criteria

1. WHEN the Team_Leader opens the Dashboard, THE Dashboard SHALL display aggregate metrics: total active cases, cases by status, cases by case_type, and count of overdue cases.
2. THE Dashboard SHALL display a list of cases sorted by urgency, with overdue cases appearing first, followed by approaching-deadline cases.
3. WHEN the Team_Leader selects a case from the overview, THE Dashboard SHALL navigate to the Case_Viewer for that case.

### Requirement 7: Applicant Status View

**User Story:** As an Applicant, I want to check the status of my case, so that I know where my case is in the process and what is expected of me.

#### Acceptance Criteria

1. WHEN the Applicant enters a valid case reference, THE Case_Viewer SHALL display the case status, the current workflow stage in plain language, and any outstanding actions required from the Applicant.
2. IF the Applicant enters an invalid case reference, THEN THE Case_Viewer SHALL display a message stating "No case found for this reference. Please check your reference number."
3. THE Case_Viewer SHALL NOT display internal case notes, assigned team, or policy details to the Applicant.

### Requirement 8: AI Advisor Integration Points

**User Story:** As a Caseworker, I want AI-generated summaries and recommended next actions, so that I can understand complex cases faster and make better decisions.

#### Acceptance Criteria

1. WHEN the Caseworker opens a case, THE AI_Advisor SHALL provide a plain-language summary of the case based on the timeline and case notes.
2. WHEN the Caseworker opens a case, THE AI_Advisor SHALL provide a list of recommended next actions based on the case status, applicable policy, and workflow position.
3. THE AI_Advisor SHALL clearly label all AI-generated content with a visual indicator stating "AI-generated suggestion — verify before acting."
4. WHILE the AI_Advisor is using mocked responses, THE AI_Advisor SHALL return pre-written summaries and recommendations that demonstrate the intended behaviour.
5. THE AI_Advisor SHALL expose a defined interface (function signature) so that mocked responses can be replaced by real language model calls without changing the rest of the application.

### Requirement 9: Data Loading and Parsing

**User Story:** As a developer, I want the application to load and parse the provided JSON data files, so that all case, policy, and workflow data is available to the application.

#### Acceptance Criteria

1. WHEN the application starts, THE Dashboard SHALL load and parse cases.json, policy-extracts.json, and workflow-states.json from the challenge-3 directory.
2. IF a data file is missing or contains invalid JSON, THEN THE Dashboard SHALL display an error message identifying which file failed to load.
3. FOR ALL valid case records in cases.json, parsing then serializing then parsing SHALL produce an equivalent object (round-trip property).
4. THE Policy_Engine SHALL parse each policy extract and index the extracts by applicable_case_types for efficient lookup.

### Requirement 10: Responsive Web Interface

**User Story:** As a Caseworker, I want to use the tool on different screen sizes, so that I can access case information from a desktop or tablet.

#### Acceptance Criteria

1. THE Dashboard SHALL render correctly on screen widths from 768 pixels to 1920 pixels.
2. THE Case_Viewer SHALL render correctly on screen widths from 768 pixels to 1920 pixels.
3. THE Dashboard SHALL use clear visual hierarchy with headings, spacing, and colour coding to make information scannable.
4. THE Dashboard SHALL meet WCAG 2.1 Level AA colour contrast requirements for all text elements.
