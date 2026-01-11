# Human-in-the-Loop Instagram Cleanup Assistant  
*A compliance-aware workflow system for sensitive user actions*

---

## Overview

This project solves a deceptively simple real-world problem:

> How do you systematically withdraw **pending Instagram follow requests** from an account
> **without violating platform policies, user trust, or ethical engineering principles?**

Instead of approaching this as an automation or bot problem, this project treats it as a **stateful, human-verified workflow orchestration problem**.

The Instagram use case is intentional, but secondary.  
The core contribution is a **safe, resumable, human-in-the-loop workflow system** that can be repurposed across many domains where automation without verification is risky.

---

## The Problem (Why this exists)

When rebranding or repurposing an Instagram account, creators often want a “clean slate”:
- Remove followers
- Unfollow accounts
- Withdraw pending follow requests

Instagram allows manual withdrawal of pending requests **one profile at a time**, but:
- There is no bulk interface
- There is no visibility into long-pending requests
- Naïve automation violates platform rules and risks account bans

This creates a genuine tension between:
- User intent
- Platform constraints
- Ethical engineering

---

## Design Philosophy

This project was guided by **explicit non-goals** as much as goals.

### What this project deliberately does **NOT** do

- ❌ No DOM automation  
- ❌ No credential handling  
- ❌ No Instagram API usage  
- ❌ No simulated clicks  
- ❌ No background loops  
- ❌ No uncontrolled bulk actions  

### What it enforces instead

- ✅ Explicit human confirmation for every action  
- ✅ User opt-in for any guided behavior  
- ✅ One profile at a time  
- ✅ Full stop / resume capability  
- ✅ Transparent, auditable state  

Good engineering is often about **refusing to cross lines**, even when something is technically possible.

---

## Core Features

### 1. Deterministic Data Ingestion
- Uses Instagram’s official data export (`pending_follow_requests.json`)
- Treats platform data as **read-only source of truth**
- No scraping or inference

### 2. Stateful Workflow Engine
- Each pending request is tracked independently
- Explicit request states:
  - `pending`
  - `completed`
  - `skipped`
- Progress persists across sessions

### 3. Human-in-the-Loop Enforcement
- A request **cannot** be completed or skipped unless its profile has been opened
- This invariant is enforced at both:
  - UI level
  - Engine level

### 4. Manual and Guided Workflow Modes
- **Manual mode**: user explicitly opens each profile
- **Guided mode** (opt-in):
  - Next profile opens automatically **after user confirmation**
  - Still requires human action on Instagram
- No background automation, ever

### 5. Safe Browser Orchestration
- Profiles open in the user’s browser using their existing login session
- Browser behavior is respected (tabs vs windows)
- No control over Instagram UI

---

## Why This Is Not “Just an Instagram Tool”

The Instagram use case is an **example**, not the product.

The same workflow architecture applies to:
- Compliance review queues
- Manual QA pipelines
- Moderation systems
- Data correction workflows
- Account migration audits
- Any process where automation without verification is dangerous

The value lies in the **workflow design**, not the platform.

---

## Architecture Overview

This system is intentionally layered to enforce safety and clarity.

```
┌──────────────────────────┐
│ Instagram Data Export │
│ (pending_follow_requests.json)
└─────────────┬────────────┘
│ read-only
▼
┌──────────────────────────┐
│ Data Parser / Normalizer│
│ - Validates schema │
│ - Extracts usernames │
│ - Converts timestamps │
└─────────────┬────────────┘
▼
┌──────────────────────────┐
│ Session State Layer │
│ - Ordered queue │
│ - Request states │
│ - Persistent progress │
│ - Stop / Resume support│
└─────────────┬────────────┘
▼
┌──────────────────────────┐
│ Workflow Engine │
│ - Enforces invariants │
│ - Valid state transitions
│ - No UI assumptions │
└─────────────┬────────────┘
▼
┌──────────────────────────┐
│ Browser Orchestration │
│ - Opens profile URLs │
│ - Rate-limited │
│ - Records user intent │
└─────────────┬────────────┘
▼
┌──────────────────────────┐
│ Streamlit UI │
│ - Explicit user actions │
│ - Mode selection │
│ - Progress visibility │
│ - Safe control flow │
└──────────────────────────┘
```

---

## Safety & Ethics Summary

This project demonstrates how to:
- Respect platform boundaries
- Avoid brittle automation
- Encode ethical constraints directly into system design
- Build tools that assist users **without impersonating them**

It is intentionally **not** a product, growth tool, or automation service.

---

## Limitations (by design)

- No bulk execution
- No headless browsing
- No background processing
- Browser behavior depends on user settings

These are not shortcomings — they are **guardrails**.

---

## Key Takeaway

> Small problems become interesting when constraints are real.  
> This project is about building reliable systems **under constraints**, not bypassing them.

---

## NOTE - This repository includes a synthetic sample Instagram export with fictional usernames for demonstration purposes only.

---

### REPO Structure
```
human-in-the-loop-cleanup-assistant/
│
├── app.py                         # Streamlit entrypoint
├── README.md
├── requirements.txt
├── .gitignore
│
├── workflow/                      # Core workflow logic
│   ├── __init__.py
│   ├── models.py                  # Data models (PendingRequest, RequestState)
│   ├── parser.py                  # Instagram export parsing
│   ├── session.py                 # SessionState + persistence
│   ├── engine.py                  # Workflow invariants & transitions
│   └── browser.py                 # Safe browser orchestration
│
├── data/
│   └── pending_follow_requests.sample.json
│
└── scripts/
    └── generate_sample_pending_requests.py
```

---

## License

This project is shared for educational and portfolio purposes only.
