# Project NOAH Development Environment

This document describes the official development environment for Project NOAH.

The goal is to ensure that the project can be reproduced consistently on any machine.

---

# Operating System

- Windows 11 (64-bit)

---

# Development Tools

| Tool | Version |
|------|---------|
| Visual Studio Code | 1.119.0 |
| Git | 2.55.0.windows.2 |
| Python | 3.13.14 |
| pip | 25.1.1 |
| Docker Desktop | 29.6.1 |
| Docker Compose | v2.5.0 |
| GitHub Desktop | Latest Stable |

---

# Git Configuration

Default Editor

- Visual Studio Code

Default Branch

- main

SSH

- Bundled OpenSSH

HTTPS Backend

- Windows Secure Channel

Line Endings

- Checkout Windows-style, commit Unix-style

Terminal

- MinTTY

Credential Manager

- Git Credential Manager

---

# Python Configuration

Version

- Python 3.13.14

Installed Features

- pip
- py launcher
- Documentation
- Python Test Suite
- Add Python to PATH

---

# Visual Studio Code Extensions

Core Extensions

- Python (Microsoft)
- Pylance (Microsoft)
- Docker (Microsoft)
- YAML (Red Hat)
- GitHub Pull Requests (GitHub)
- Markdown All in One
- GitLens
- Error Lens

---

# Verification

The following commands were successfully verified.

```bash
git --version

python --version

py --version

pip --version

docker --version

docker compose version

code --version
```

---

# Philosophy

Project NOAH prioritizes a stable and reproducible development environment.

New tools should only be introduced when they provide meaningful value to the project.

The development environment should remain simple, consistent, and easy to rebuild.