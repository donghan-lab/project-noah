# Project NOAH Development Guide

This document defines the development workflow, conventions, and engineering principles used throughout Project NOAH.

The goal is to build NOAH in a consistent, maintainable, and reliable way.

---

# Development Philosophy

Every change should move Project NOAH one step closer to becoming a trusted AI companion.

Build slowly.

Build reliably.

Build for the next ten years, not the next ten days.

---

# Development Workflow

Every feature should follow this workflow:

1. Create or update an Issue.
2. Plan the implementation.
3. Implement the feature.
4. Test the result.
5. Commit changes.
6. Update documentation if necessary.
7. Push changes to GitHub.

---

# Branch Strategy

main

- Stable branch
- Always deployable

feature/<name>

- New features

fix/<name>

- Bug fixes

research/<name>

- Experiments and research

---

# Commit Convention

docs:
Documentation changes

feat:
New features

fix:
Bug fixes

refactor:
Code improvements

chore:
Maintenance and project structure

test:
Testing

---

# Documentation Rules

Documentation is part of the project.

Whenever the architecture or philosophy changes, the documentation should be updated accordingly.

- Vision defines the destination.
- Principles define the rules.
- Architecture defines the system.
- Roadmap defines future milestones.
- Decisions record important design choices.
- Ideas store future possibilities.
- Journal records the project's evolution.

---

# Folder Responsibilities

Each directory has a single responsibility.

- docs/ → Documentation
- agents/ → AI agents
- prompts/ → Prompt templates
- workflows/ → Automation workflows
- database/ → Database resources
- docker/ → Container configuration
- config/ → Configuration files
- scripts/ → Utility scripts
- tests/ → Testing

Avoid mixing responsibilities across directories.

---

# AI Development Principles

NOAH should think proactively.

NOAH should understand intentions before generating answers.

Important actions require user approval.

Trust should be earned before autonomy.

The user always has the final decision.

---

# Engineering Principles

Prefer simple solutions over complex ones.

Optimize only when necessary.

Build modular components.

Avoid unnecessary dependencies.

Write code that future-you can understand.

---

# Project Mindset

Project NOAH is not a short-term project.

It is a lifelong journey.

Every commit is another step toward building my own Jarvis.