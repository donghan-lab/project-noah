# Project NOAH Infrastructure

This document defines the infrastructure principles of Project NOAH.

The purpose of these guidelines is to keep the system simple, scalable, and easy to maintain as Project NOAH grows.

---

# Philosophy

Infrastructure should be stable before it becomes complex.

Every service must have a clear purpose.

Scalability should never sacrifice maintainability.

---

# Folder Structure

```text
Project-NOAH/

compose/
config/
database/
docker/
n8n/
```

Each directory has a single responsibility.

---

# Docker

Docker Compose files are stored inside the `compose/` directory.

Container names should begin with the `noah-` prefix.

Persistent services should use dedicated Docker volumes.

All containers communicate through a shared Docker network.

---

# AI Runtime

Ollama runs directly on the host machine.

Docker services communicate with Ollama through the local network.

This approach provides better GPU performance and simplifies model management.

---

# Database

PostgreSQL is the primary relational database.

Additional databases may be introduced only when they provide clear benefits.

---

# Networking

Use a single shared Docker network unless service isolation becomes necessary.

---

# Volumes

Persistent data should never be stored inside containers.

Each service must own its dedicated volume.

---

# Configuration

Environment-specific settings should be stored separately from application logic.

## Environment Variables

Docker-specific environment variables are stored in `compose/.env`.

Application-specific environment variables may use a separate `.env` file in the project root if needed in the future.

Environment variables containing secrets must never be committed to the repository.

Configuration files should remain separate from application logic.

---

# Naming Convention

Docker resources should use the following naming convention.

Examples:

- noah-postgres
- noah-n8n
- noah-open-webui
- noah-network

---

# Future Expansion

The infrastructure is designed to support future services, including:

- Redis
- Qdrant
- Monitoring
- NOAH Core
- Additional AI services

without requiring major structural changes.