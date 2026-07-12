# Project NOAH Architecture

## Overview

Project NOAH is built around a central AI coordinator.

The coordinator communicates with multiple AI providers, local infrastructure, and external services while keeping the user at the center of every decision.

---

## High-Level Architecture

User
    │
    ▼
NOAH Core
    │
    ├── AI Router
    │      ├── GPT
    │      ├── Claude
    │      ├── Gemini
    │      └── Ollama (Local)
    │
    ├── Memory
    │      ├── Knowledge
    │      ├── Decisions
    │      └── Journal
    │
    ├── Skills
    │      ├── Discord
    │      ├── GitHub
    │      ├── OBS
    │      ├── File Manager
    │      └── Automation
    │
    └── Infrastructure
           ├── NAS
           ├── RTX 5080
           ├── RTX 2080
           └── Laptop

---

## Responsibilities

### User

Makes final decisions and approves important actions.

### NOAH Core

Coordinates every task.

Chooses the appropriate AI model.

Maintains long-term memory.

Protects sensitive information.

### AI Router

Selects the most suitable AI provider for each request.

### Memory

Stores knowledge, decisions, and project history.

### Skills

Provides integrations such as Discord, GitHub, file management, broadcasting tools, and automation.

### Infrastructure

Provides computing resources, storage, networking, and remote access.

---

## Planned Technology Stack

| Layer | Planned Technology |
|--------|--------------------|
| Workflow Automation | n8n |
| Database | PostgreSQL |
| Local AI | Ollama |
| AI Interface | Open WebUI |
| Cloud AI | Gemini API |
| Version Control | GitHub |
| Storage | Synology NAS |
| Main Compute | RTX 5080 PC |
| Server / Worker | RTX 2080 PC |
| Remote Access | Tailscale (Planned) |

> This represents the initial planned technology stack for Project NOAH.
> The stack may evolve as the project grows.

---

## Future Expansion

Project NOAH is designed to evolve over time.

Future components may include:

- Multi-Agent Collaboration
- Voice Interface
- Mobile Companion
- Vector Database
- Smart Home Integration
- Autonomous Workflow Execution
