"""Read-only operator triage for the current memory.save contract."""

from collections import Counter, defaultdict

import psycopg

from .db import connect


MEMORY_SAVE_GOAL = "Save explicitly requested memory"
NO_ACTION = {
    "verified_completed": "Verified terminal result; triage does not change records or replay the write.",
    "recorded_failure": "Recorded terminal failure; triage does not retry a side effect.",
    "unresolved_running": "No terminal evidence; runtime liveness and commit outcome are unknown.",
    "record_inconsistent": "Contradictory or missing evidence requires operator review before any mutation.",
}


def classify_memory_writes(tasks, executions, mappings, memories):
    """Classify durable evidence without reading memory content or changing state."""
    task_by_id = {row["id"]: row for row in tasks}
    memory_by_id = {row["id"]: row for row in memories}
    executions_by_task = defaultdict(list)
    mappings_by_execution = defaultdict(list)
    for row in executions:
        if row["task_id"] is not None:
            executions_by_task[row["task_id"]].append(row)
    for row in mappings:
        mappings_by_execution[row["execution_id"]].append(row)

    items = []
    seen_tasks = set()
    execution_ids = {row["id"] for row in executions}
    for execution in executions:
        task_id = execution["task_id"]
        task = task_by_id.get(task_id)
        if task_id in task_by_id:
            seen_tasks.add(task_id)
        memory_id = execution["memory_id"]
        memory = memory_by_id.get(memory_id)
        keys = mappings_by_execution.get(execution["id"], [])
        issues = []
        if task_id is not None and task is None:
            issues.append("TASK_NOT_IN_MEMORY_SAVE_SCOPE")
        if task is not None:
            if len(executions_by_task[task_id]) != 1:
                issues.append("EXECUTION_COUNT_MISMATCH")
            if task["actor_user_id"] != execution["actor_user_id"]:
                issues.append("ACTOR_MISMATCH")
        if len(keys) > 1 or any(key["actor_user_id"] != execution["actor_user_id"] for key in keys):
            issues.append("IDEMPOTENCY_MAPPING_MISMATCH")
        if memory_id is not None:
            if memory is None:
                issues.append("MEMORY_NOT_FOUND")
            elif memory["created_by"] != execution["actor_user_id"] or (
                memory["scope"] == "user" and memory["owner_user_id"] != execution["actor_user_id"]
            ):
                issues.append("MEMORY_ACTOR_MISMATCH")
        if execution["status"] == "succeeded" and memory_id is None:
            issues.append("MISSING_MEMORY_REFERENCE")
        if execution["status"] == "succeeded" and execution["verified_at"] is None:
            issues.append("MISSING_VERIFICATION_TIME")
        if execution["status"] in {"running", "failed"} and memory_id is not None:
            issues.append("UNEXPECTED_MEMORY_REFERENCE")

        task_status = task["status"] if task else None
        verification = task["verification_status"] if task else None
        execution_status = execution["status"]
        completed = (
            task is not None and task_status == "completed" and verification == "passed"
            and execution_status == "succeeded" and memory is not None
            and execution["verified_at"] is not None and not issues
        )
        failed = (
            execution_status == "failed" and execution["failure_code"] is not None
            and memory_id is None and execution["verified_at"] is None
            and ((task is None and task_id is None and not keys)
                 or (task is not None and task_status == "failed" and verification == "failed"))
            and not issues
        )
        running = (
            task is not None and task_status == "running" and verification == "pending"
            and execution_status == "running" and memory_id is None
            and execution["verified_at"] is None and execution["failure_code"] is None
            and not issues
        )
        if completed:
            classification, outcome = "verified_completed", "succeeded"
        elif failed:
            classification, outcome = "recorded_failure", "failed"
        elif running:
            classification, outcome = "unresolved_running", "unknown"
        else:
            classification, outcome = "record_inconsistent", "unknown"
            if not issues:
                issues.append("STATUS_OR_VERIFICATION_MISMATCH")
        items.append({
            "task_id": str(task_id) if task_id else None,
            "execution_id": str(execution["id"]),
            "capability": "memory.save",
            "task_status": task_status,
            "execution_status": execution_status,
            "verification_status": verification,
            "verified_at_present": execution["verified_at"] is not None,
            "idempotency_mapping_present": bool(keys),
            "memory_reference_present": memory_id is not None,
            "memory_exists": memory is not None,
            "classification": classification,
            "outcome": outcome,
            "issues": issues,
            "no_action_reason": NO_ACTION[classification],
        })

    for task in tasks:
        if task["id"] not in seen_tasks:
            items.append({
                "task_id": str(task["id"]), "execution_id": None, "capability": "memory.save",
                "task_status": task["status"], "execution_status": None,
                "verification_status": task["verification_status"], "verified_at_present": False,
                "idempotency_mapping_present": False, "memory_reference_present": False,
                "memory_exists": False, "classification": "record_inconsistent", "outcome": "unknown",
                "issues": ["EXECUTION_NOT_FOUND"],
                "no_action_reason": NO_ACTION["record_inconsistent"],
            })

    for mapping in mappings:
        if mapping["execution_id"] not in execution_ids:
            items.append({
                "task_id": None, "execution_id": str(mapping["execution_id"]),
                "capability": "memory.save", "task_status": None, "execution_status": None,
                "verification_status": None, "verified_at_present": False,
                "idempotency_mapping_present": True, "memory_reference_present": False,
                "memory_exists": False, "classification": "record_inconsistent", "outcome": "unknown",
                "issues": ["MAPPING_TO_NON_MEMORY_SAVE_EXECUTION"],
                "no_action_reason": NO_ACTION["record_inconsistent"],
            })

    items.sort(key=lambda item: (item["task_id"] or "", item["execution_id"] or ""))
    counts = dict(sorted(Counter(item["classification"] for item in items).items()))
    return {"status": "succeeded", "scanned": len(items), "counts": counts, "items": items}


def triage_memory_writes(connection_factory=connect):
    """Inspect one consistent, read-only PostgreSQL snapshot."""
    try:
        with connection_factory() as db:
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            tasks = db.execute("""SELECT id, actor_user_id, status, verification_status
                FROM noah.tasks WHERE goal = %s""", (MEMORY_SAVE_GOAL,)).fetchall()
            executions = db.execute("""SELECT id, task_id, actor_user_id, status, failure_code,
                memory_id, verified_at FROM noah.execution_records
                WHERE capability = 'memory.save'""").fetchall()
            mappings = db.execute("""SELECT actor_user_id, execution_id
                FROM noah.memory_write_requests""").fetchall()
            memory_ids = [row["memory_id"] for row in executions if row["memory_id"] is not None]
            memories = db.execute("""SELECT id, scope, owner_user_id, created_by
                FROM noah.memories WHERE id = ANY(%s)""", (memory_ids,)).fetchall() if memory_ids else []
            return classify_memory_writes(tasks, executions, mappings, memories)
    except (psycopg.Error, OSError, ValueError):
        return {"status": "unavailable", "failure": {"code": "DATABASE_UNAVAILABLE",
            "message": "Recovery triage could not inspect PostgreSQL; no outcome was inferred."}}
