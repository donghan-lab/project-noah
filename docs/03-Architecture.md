# Project NOAH Architecture

## Overview

Project NOAH is a personal AI operating system designed to build a trusted AI companion.

At the center of the system is NOAH Core, which coordinates planning, memory, AI collaboration, and automation while keeping the user involved in important decisions.

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

Maintains context.

Coordinates every subsystem.

Protects user data.

---

### Planner

Analyzes requests.

Creates execution plans.

Suggests improvements.

Coordinates multi-step workflows.

---

### AI Router

Selects the most suitable AI model for each task.

Balances speed, quality, privacy, and cost.

---

### Memory

Stores knowledge, experiences, user preferences, project history, and important decisions.

Memory allows NOAH to continuously improve over time.

---

### Skills

Connects NOAH with external tools.

Examples include GitHub, Discord, OBS, browsers, file management, and automation.

---

### Infrastructure

Provides computing power, storage, networking, and remote execution.

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
> It will evolve together with the project.

---

## Future Expansion

Future capabilities may include:

- Multi-Agent Collaboration
- Voice Interface
- Personal Knowledge Graph
- Smart Home Integration
- Self-Optimization
- Continuous Learning
- Autonomous Workflow Execution (with User Approval)
