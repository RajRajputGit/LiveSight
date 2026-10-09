# Real-Time AI Object Detection & Monitoring System

## Purpose
This documentation pack is the working source of truth for building a local-first, real-time object detection, multi-object tracking, and event-monitoring application. Use the documents iteratively throughout the project lifecycle: planning, implementation, testing, and deployment.

The project is inspired by a high-level project description and is **not a reproduction of any proprietary implementation**. Reported performance figures from the reference description are not assumed to apply to this build.

## Current target
Build a local MVP on a developer machine:
1. Read a webcam or video file.
2. Run object detection with a pretrained YOLO model.
3. Track detected objects across frames.
4. Apply deterministic event rules, starting with restricted-zone intrusion.
5. Expose events through a FastAPI backend.
6. Store event history in SQLite.
7. Show live events and status in a React dashboard.
8. Add optional mobile notifications, cloud, and edge deployment only after the local MVP is stable.

## Document index
| Document | Use it for |
|---|---|
| `01_PRODUCT_REQUIREMENTS.md` | Scope, users, requirements, acceptance criteria |
| `02_SYSTEM_ARCHITECTURE.md` | Components, boundaries, data flow, deployment options |
| `03_WORKFLOW_AND_DATA_CONTRACTS.md` | Runtime workflow and event schemas |
| `04_IMPLEMENTATION_PLAN.md` | Phased development tasks and exit criteria |
| `05_API_SPECIFICATION.md` | REST and WebSocket contract |
| `06_TEST_STRATEGY.md` | Test levels, scenarios, and measurable quality |
| `07_LOCAL_SETUP_AND_RUNBOOK.md` | Environment setup, run commands, troubleshooting |
| `08_DEPLOYMENT_AND_OPERATIONS.md` | Docker, production hardening, edge/cloud path |
| `09_DECISIONS_AND_CHANGELOG.md` | Architecture decisions and change history |
| `10_AI_CODING_AGENT_WORKFLOW.md` | How to use an AI coding agent iteratively without losing control |
| `11_GLOSSARY.md` | Shared terminology |

## How to use the pack
- Treat `01_PRODUCT_REQUIREMENTS.md` and `02_SYSTEM_ARCHITECTURE.md` as the baseline.
- Before each implementation phase, update the relevant document and define acceptance criteria.
- After a meaningful change, update API contracts, tests, decisions, and changelog.
- Keep claims factual: mark targets as targets until measured.
- Do not add a new service or technology unless it solves a documented requirement.

## Suggested repository layout
```text
ai-vision-project/
├── README.md
├── docs/
│   ├── 01_PRODUCT_REQUIREMENTS.md
│   ├── 02_SYSTEM_ARCHITECTURE.md
│   ├── 03_WORKFLOW_AND_DATA_CONTRACTS.md
│   ├── 04_IMPLEMENTATION_PLAN.md
│   ├── 05_API_SPECIFICATION.md
│   ├── 06_TEST_STRATEGY.md
│   ├── 07_LOCAL_SETUP_AND_RUNBOOK.md
│   ├── 08_DEPLOYMENT_AND_OPERATIONS.md
│   ├── 09_DECISIONS_AND_CHANGELOG.md
│   ├── 10_AI_CODING_AGENT_WORKFLOW.md
│   └── 11_GLOSSARY.md
├── backend/
├── vision/
├── frontend/
├── tests/
├── scripts/
├── data/                 # local samples only; do not commit sensitive video
├── .env.example
├── .gitignore
└── docker-compose.yml    # introduced in a later phase
```

## Project status
- Status: Planning / local MVP
- First milestone: single video source → detection → tracking → event rule → visible event
- Known constraints: local hardware varies; webcam permissions vary; model download requires network access initially
