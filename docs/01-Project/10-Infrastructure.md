# Project NOAH Infrastructure

This document defines the infrastructure principles of Project NOAH.

The purpose of these guidelines is to keep the system simple, scalable, and easy to maintain as Project NOAH grows.

This document establishes the infrastructure standards that support the long-term growth of Project NOAH.

---

# Philosophy

Infrastructure should be stable before it becomes complex.

Every service must have a clear purpose.

Scalability should never sacrifice maintainability.

Infrastructure should evolve without disrupting existing services.

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

Each directory exists for a specific purpose and should avoid overlapping responsibilities.

---

# Docker

Docker Compose files are stored inside the `compose/` directory.

Container names should begin with the `noah-` prefix.

Persistent services should use dedicated Docker volumes.

All containers communicate through a shared Docker network.

Containers should remain as independent as possible.

---

# AI Runtime

Ollama runs directly on the host machine.

Docker services communicate with Ollama through the local network.

This approach provides better GPU performance and simplifies model management.

This design allows AI services to be upgraded independently from containerized applications.

---

# Database

PostgreSQL is the primary relational database.

Additional databases may be introduced only when they provide clear benefits.

Each database should have a clearly defined responsibility.

---

# Networking

Use a single shared Docker network unless service isolation becomes necessary.

Network complexity should grow only when required.

---

# Volumes

Persistent data should never be stored inside containers.

Each service must own its dedicated volume.

Persistent data should remain portable and recoverable.

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

Consistent naming improves maintainability and readability.

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

Future technologies should integrate without requiring fundamental architectural changes.