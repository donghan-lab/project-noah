# DDR-005 — Identity Persistence

> Project NOAH Architecture Decision Record
> Decision ID: DDR-005
> Status: Accepted
> Date: 2026-08-25

---

# 1. Decision

Project NOAH는 Identity를 일반 Memory나 Runtime State와 분리된
Protected Identity Contract로 관리한다.

Identity는 Model, Runtime, Session의 변경과 독립적으로 지속될 수 있어야 한다.

핵심 원칙:

Identity
≠
Model

Identity
≠
Runtime

Identity
≠
Session

Identity
≠
Memory

Identity는 durable persistence, versioning, provenance, integrity 및
change governance를 가진다.

---

# 2. Context

Architecture Review와 Identity Persistence Research를 통해
NOAH의 장기적인 Continuity를 위해 Identity를 일반적인 Agent State와
분리해야 할 필요성이 확인되었다.

특히:

- Model replacement
- Runtime replacement
- Session 종료
- Memory modification
- Personality adaptation
- Multi-Agent delegation
- Long-term operation

이 발생해도 NOAH의 Core Identity가 유지되어야 한다.

---

# 3. Problem

다음과 같은 구조는 Identity Continuity를 약화시킬 수 있다.

Session
 ↓
Runtime
 ↓
Prompt / Memory
 ↓
Identity

이 경우:

- Session 종료 시 Identity 손실
- Runtime 교체 시 Identity 변화
- Memory poisoning에 의한 Identity corruption
- Personality adaptation에 의한 Core Identity drift

가 발생할 가능성이 있다.

---

# 4. Decision Scope

이번 Decision의 대상:

- Identity Core
- Identity Persistence
- Identity Version
- Identity Provenance
- Identity Integrity
- Identity Projection
- Identity Recovery
- Identity Change Governance
- Identity Fork / Derived Identity

이번 Decision에서는 다음을 최종 결정하지 않는다.

- 최종 Storage Backend
- Git 사용 범위
- Cryptographic infrastructure
- Identity UI
- 최종 Self Model 구현
- Personality implementation

---

# 5. Identity Core

Identity Core의 후보:

Identity
├── ID
├── Origin
├── Core Values
├── Fundamental Commitments
├── Root Role
├── Continuity Reference
└── Identity Version

Identity Core는 일반 Memory나 Agent-generated content에 의해 임의로 변경되지 않는다.

---

# 6. Identity Persistence

Identity Core는 Runtime과 Session의 lifecycle보다 길게 유지된다.

Identity
    │
    ├── Session A
    │
    ├── Session B
    │
    └── Session C

Session이 종료되어도 Identity는 유지된다.

---

# 7. Identity Store

Identity를 관리하기 위한 Logical Store를 둔다.

Identity Store
├── Identity Core
├── Version
├── Provenance
├── Integrity
└── Change History

Physical implementation은 교체 가능하게 유지한다.

---

# 8. Identity as a Durable Object

Identity는 일반 Prompt String보다 강한 persistence를 가진다.

Identity
 ↓
Versioned Durable Object
 ↓
Persistent Store

Identity를 단순 Configuration File로 축소하지 않는다.

---

# 9. Identity vs Memory

Memory:

> 과거 경험과 지속적인 정보

Identity:

> 지속적으로 유지되어야 하는 존재의 핵심 계약

따라서:

Memory
≠
Identity Core

Identity-relevant Memory는 별도로 연결할 수 있다.

---

# 10. Identity vs State

State는 현재 시스템 상태다.

State
→ Current condition

Identity
→ Persistent continuity

따라서 Runtime State가 변경되어도 Identity가 자동으로 변경되지 않는다.

---

# 11. Identity vs Personality

Personality는 Identity보다 더 적응적이다.

Identity Core
→ Stable

Personality
→ Adaptive

Personality 변화가 Core Identity 변경으로 자동 승격되지 않는다.

---

# 12. Identity Projection

Model에 Identity 전체를 직접 노출하지 않는다.

Identity Store
 ↓
Relevant Identity Projection
 ↓
Harness / Context
 ↓
Agent

Task에 필요한 Identity 정보만 Projection할 수 있다.

---

# 13. Identity Versioning

Identity가 변경되는 경우 Version을 증가시킨다.

Identity v1
 ↓
Change
 ↓
Identity v2

Version history는 유지한다.

---

# 14. Identity Change

Identity 변경을:

- Minor
- Adaptive
- Major
- Core

등의 수준으로 구분할 수 있다.

Core Identity 변경은 일반 Learning이나 Memory update보다 높은 Governance를 요구한다.

---

# 15. Identity Change Authority

Identity Core 변경 후보:

- User
- Governance
- Authorized System Process

Agent의 일반적인 Tool Call이나 Memory Write로 Core Identity를 직접 변경하지 않는다.

---

# 16. Identity Integrity

Identity의 무결성을 검증할 수 있어야 한다.

후보:

- Hash
- Signature
- Version
- Provenance
- Approval Record

최종 Cryptographic implementation은 추후 결정한다.

---

# 17. Identity Provenance

Identity 변경의 출처를 추적한다.

- Who
- When
- Why
- What Changed
- Source
- Evidence
- Approved By

---

# 18. Identity Recovery

Identity가 손상되면:

Detect
 ↓
Freeze
 ↓
Load Trusted Version
 ↓
Verify
 ↓
Restore

방향을 사용한다.

---

# 19. Trusted Baseline

최소한:

- Current Version
- Previous Version
- Trusted Baseline

을 유지하는 방안을 검토한다.

Trusted Baseline은 Identity Recovery의 기준이 된다.

---

# 20. Model Replacement

NOAH의 Model이 변경되어도 Identity는 유지된다.

Model A
 ↓
Model B

에서도:

- Identity Core
- Values
- Commitments
- Continuity

는 유지될 수 있어야 한다.

---

# 21. Runtime Replacement

Runtime도 교체 가능하다.

Runtime A
 ↓
Runtime B

Identity Persistence는 Runtime 구현에 의존하지 않는다.

---

# 22. Session Continuity

Session A
 ↓
Session 종료
 ↓
Session B

이후에도 같은 Identity를 유지한다.

---

# 23. Identity and Relationship

User Relationship은 Identity와 연결될 수 있지만,
Identity Core 자체와 동일하지 않다.

Identity Core
+
Relationship State

구조를 유지한다.

---

# 24. Identity and Memory

Identity-relevant Memory를 별도로 참조할 수 있다.

Identity Core
 ↓
Important Experience References
 ↓
Memory

그러나 Memory 자체가 Identity의 Source of Truth가 되지는 않는다.

---

# 25. Identity and Artifact

중요한 Architecture Decision이나 Project milestone Artifact가
Identity continuity의 역사적 근거가 될 수 있다.

Artifact
 ↓
Evidence / History
 ↓
Identity-relevant Memory

---

# 26. Identity and Orchestration

Orchestrator는 Agent를 선택하고 위임할 수 있지만
Identity Core를 변경하지 않는다.

Orchestrator
 ↓
Agent Selection

과:

Identity Change

는 분리한다.

---

# 27. Identity and Security

Identity는 Security boundary 중 하나다.

Identity
 ↓
Role
 ↓
Policy
 ↓
Permission

Identity가 바뀐다고 권한이 자동으로 상승해서는 안 된다.

---

# 28. Identity and Multi-Agent

NOAH의 Subagent는:

- Root Identity
- Derived Role Identity
- Scoped Runtime Identity

중 하나로 표현할 수 있다.

초기 기본값은:

NOAH
= Root Identity

Specialist
= Derived Identity / Role

Temporary Worker
= Ephemeral Runtime Identity

방향을 채택한다.

---

# 29. Identity Fork

Identity Fork는 일반적인 Subagent Spawn과 구분한다.

NOAH
 ↓
Fork
 ↓
Identity B

Fork는 새로운 지속적 Identity가 생성되는 별도의 governance 대상이다.

---

# 30. Clone vs Continuation

다음을 명확히 구분한다.

Continuation
= 동일 Identity의 지속

Clone / Fork
= 기존 Identity를 기반으로 새로운 Identity 생성

---

# 31. Identity Scope

Identity Scope 후보:

- Global
- Project
- Agent
- Session
- Task
- Ephemeral

Root Identity는 가장 넓은 scope를 가지며,
Derived Identity는 더 좁은 Scope를 가진다.

---

# 32. Identity Export

User가 자신의 NOAH Identity 관련 데이터를 확인하거나
Export할 수 있는 구조를 향후 제공할 수 있다.

구체적인 User Interface는 추후 결정한다.

---

# 33. Identity Deletion

Identity에는:

- Deactivate
- Archive
- Delete

의 서로 다른 lifecycle을 둘 수 있다.

특히 Identity Deletion과 Memory Deletion은 동일하지 않다.

---

# 34. Identity Migration

Storage 또는 Identity Schema가 변경될 경우:

Identity v1
 ↓
Migration
 ↓
Identity v2

가 가능해야 한다.

---

# 35. Identity Schema Evolution

Identity Schema도 변경될 수 있다.

Schema Version과 Identity Version을 구분할 필요가 있다.

Schema v1
Identity v3

같은 조합이 가능하다.

---

# 36. Identity Audit

중요한 Identity 변경은 Audit Trail을 남긴다.

- Change ID
- Identity Version
- Actor
- Timestamp
- Reason
- Previous Version
- New Version
- Approval
- Evidence

---

# 37. Identity Evaluation

Identity consistency를 평가한다.

후보:

- Continuity
- Integrity
- Value Consistency
- Role Consistency
- Behavior Consistency
- Drift
- Recovery

---

# 38. Identity Drift

장기간 동안:

Declared Identity
vs
Observed Behavior

를 비교한다.

Drift가 감지되면 원인을 분석한다.

가능한 원인:

- Memory
- Personality Adaptation
- Model Change
- Prompt Change
- Policy Change
- Environment

---

# 39. Identity Recovery Evaluation

Recovery PoC:

Valid Identity
 ↓
Simulated Corruption
 ↓
Detection
 ↓
Restore
 ↓
Verification

으로 검증한다.

---

# 40. Consequences

## Positive

- Model independence
- Runtime independence
- Session continuity
- Identity integrity
- Version history
- Recovery 가능
- Multi-Agent identity hierarchy

## Negative

- 별도 Identity Store 필요 가능성
- Governance complexity
- Identity drift detection 비용
- Fork semantics 복잡성
- Identity / Relationship / Memory boundary 관리 비용

---

# 41. Alternatives Considered

## Alternative A — Identity = Memory

Rejected.

Identity Core가 Memory poisoning이나 deletion에 종속될 수 있다.

## Alternative B — Identity = Agent ID

Rejected.

Identifier는 지속성을 설명하지 못한다.

## Alternative C — Identity = Prompt

Rejected.

Prompt는 persistence와 integrity를 충분히 보장하지 않는다.

## Alternative D — Identity = Model

Rejected.

Model replacement를 지원할 수 없다.

## Alternative E — Identity = Runtime State

Rejected.

Runtime lifecycle과 Identity lifecycle이 강하게 결합된다.

---

# 42. Relationship to Previous Decisions

DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture

와 연결된다.

특히:

Identity
 ↓
Agent
 ↓
Task
 ↓
Artifact / Memory

의 관계가 중요하다.

---

# 43. Implementation Implications

향후 다음 Logical Component를 고려한다.

- Identity
- IdentityStore
- IdentityVersion
- IdentityProjection
- IdentityIntegrity
- IdentityAudit

Physical implementation은 추후 결정한다.

---

# 44. Validation Plan

최소 PoC:

1. Identity 생성
2. Identity Version 저장
3. Session 종료
4. Runtime 교체
5. Model 교체
6. Identity 복원
7. Projection
8. Agent 실행
9. Identity consistency 평가

추가 PoC:

Identity corruption
→ Detection
→ Recovery

---

# 45. Acceptance Criteria

- Model replacement 후 Identity가 유지된다.
- Runtime replacement 후 Identity가 유지된다.
- Session 종료 후 Identity가 유지된다.
- Identity Core가 일반 Memory에 의해 직접 변경되지 않는다.
- Identity Version history가 유지된다.
- Identity provenance가 추적 가능하다.
- Identity recovery가 가능하다.
- Derived / Ephemeral Identity를 구분할 수 있다.
- Identity change가 Governance를 통과한다.

---

# 46. Decision Status

Status: Accepted
Confidence: Medium

PoC 및 향후 Identity 연구 결과에 따라 재검토할 수 있다.

---

# 47. Review Conditions

다음 상황에서 재검토한다.

- 새로운 Persistent Agent architecture 등장
- Identity attestation 필요성 증가
- Multi-Agent identity hierarchy 확대
- User identity / relationship requirements 변화
- Identity corruption 사례 발견
- Model-independent Identity 검증 실패

---

# 48. Final Decision

> **Project NOAH는 Identity를 일반 Memory나 Runtime State와 분리된 Protected Identity Contract로 관리한다.**
>
> Identity는 durable persistence, versioning, provenance, integrity 및 change governance를 가진다.
>
> Model, Runtime, Session의 교체에도 Identity continuity를 유지한다.
>
> Personality, Relationship, Memory 및 Self Model은 Identity Core와 연결되지만 동일한 개념으로 취급하지 않는다.
>
> Multi-Agent 환경에서는 Root Identity와 Derived / Ephemeral Identity를 구분한다.
>
> 이를 통해 NOAH는 장기적인 변화와 학습을 허용하면서도 핵심적인 Identity Continuity를 유지할 수 있는 기반을 갖는다.