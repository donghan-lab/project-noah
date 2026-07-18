# Project NOAH Architecture

## Overview

Project NOAH is a personal AI operating system designed to build a trusted AI companion.

At the center of the system is NOAH Core, which coordinates planning, memory, AI collaboration, and automation while keeping the user involved in important decisions.

Every subsystem exists to support the same goal: building a trusted AI companion through collaboration rather than replacement.

The architecture reflects the core principles of Project NOAH, including Human Partnership, Trust Before Intelligence, Local First, Continuous Growth, and Modular Architecture.

The architecture is designed to evolve continuously as NOAH grows together with its user.

---

## High-Level Architecture

User
    │
    ▼
NOAH Core
    │
    ├── Planner
    │      ├── Task Planning
    │      ├── Decision Support
    │      └── Workflow Coordination
    │
    ├── AI Router
    │      ├── OpenAI
    │      ├── Claude
    │      ├── Gemini
    │      └── Ollama (Local)
    │
    ├── Memory
    │      ├── Knowledge
    │      ├── Experiences
    │      ├── Decisions
    │      ├── Journal
    │      └── Preferences
    │
    ├── Skills
    │      ├── Discord
    │      ├── GitHub
    │      ├── File Manager
    │      ├── OBS
    │      ├── Email
    │      ├── Browser
    │      └── Automation
    │
    └── Infrastructure
           ├── Synology NAS
           ├── RTX 5080 Workstation
           ├── RTX 2080 Worker
           └── Laptop

---

## Responsibilities

### User

Defines goals.

Makes important decisions.

Provides feedback that helps NOAH grow.

---

### NOAH Core

Acts as the central coordinator.

Maintains system-wide context.

Coordinates every subsystem.

Protects user data.

Ensures every subsystem follows the core principles of Project NOAH.

---

### Planner

Analyzes requests.

Creates execution plans.

Suggests improvements.

Coordinates multi-step workflows.

Never executes critical decisions without user approval.

---

### AI Router

Selects the most suitable AI model for each task.

Balances speed, quality, privacy, and cost.

Prefers the most appropriate model over the most powerful one.

---

### Memory

Stores knowledge, experiences, user preferences, project history, and important decisions.

Preserves context across conversations and projects.

Allows NOAH to continuously improve over time.

---

### Skills

Connects NOAH with external tools.

Examples include GitHub, Discord, OBS, browsers, file management, and automation.

Skills remain modular and independently replaceable.

---

### Infrastructure

Provides computing power, storage, networking, and remote execution.

Infrastructure should evolve without changing higher-level architecture.

---

## Planned Technology Stack

| Layer | Planned Technology |
|--------|--------------------|
| Workflow Automation | n8n |
| Database | PostgreSQL |
| Local AI | Ollama |
| AI Interface | Open WebUI |
| Cloud AI | OpenAI API / Gemini API / Claude API |
| Version Control | GitHub |
| Storage | Synology NAS |
| Main Compute | RTX 5080 |
| Worker Compute | RTX 2080 |
| Remote Access | Tailscale (Planned) |

> This stack represents the initial planned technologies for Project NOAH.
>
> Specific technologies may change over time, but the architectural principles should remain stable.

---

## Future Expansion

Future capabilities may include:

- Continuous Learning
- Multi-Agent Collaboration
- Voice Interface
- Personal Knowledge Graph
- Smart Home Integration
- Self-Optimization
- Autonomous Workflow Execution (with User Approval)