# Architecture Integration Review

> Project NOAH Architecture Review
> Review 대상: 전체 Architecture Integration
> Review Version: 0.2
> Status: Review

---

# 1. Review Purpose

v0.1 Integration Review 이후 수행한 P0 Research 결과를 전체 Architecture에 반영하고,
기존 경계가 여전히 일관적인지 재검토한다.

핵심 질문:

> "P0 Research 결과를 반영했을 때 현재 NOAH Architecture의 핵심 경계가 여전히 유지되는가?"

---

# 2. Changes Since v0.1

v0.1 이후 완료된 Research:

- Task State / Runtime Boundary
- Harness Boundary
- Memory / Knowledge Boundary

각 Research가 기존 Architecture에 어떤 영향을 주는지 요약한다.

---

# 3. Updated Architecture Inventory

현재 핵심 영역:

Identity
Agent
Task
Session
Orchestration
Context
State
Memory
Knowledge
Capability
Policy
Permission
Runtime
Sandbox
Environment
Verification
Observability
Evaluation
Experience
Learning

---

# 4. Updated Core Boundaries

## Identity

Identity는 Model / Runtime / Session / Memory와 독립적인 지속성 계층.

## Task

Task는 장기 목표와 canonical progress를 표현.

## Session

Session은 특정 실행 관계를 관리.

## Runtime

Runtime은 실제 execution lifecycle을 관리.

## Harness

Harness는 Agent와 execution infrastructure 사이의 stable contract.

## State

State는 canonical condition.

## Context

Context는 Model-facing projection.

## Memory

Memory는 경험과 지속적인 개인/프로젝트 정보를 관리.

## Knowledge

Knowledge는 사실·정보·외부/구조화된 지식을 관리.

---

# 5. Updated Task / Session / Runtime Boundary

현재 가장 유력한 구조:

Task
 ↓
Session
 ↓
Runtime
 ↓
Execution

하지만 Task가 Session보다 오래 지속될 수 있다.

```text
Task
├── Session A
│    └── Runtime A
│
├── Session B
│    └── Runtime B
│
└── Session C
     └── Runtime C
6. Updated State Model
State
├── Task State
├── Execution State
├── Orchestration State
├── Environment State
└── Workspace State

Task State는 durable canonical state 후보.

Execution State는 Runtime-dependent.

7. Context Boundary
State
+
Memory
+
Knowledge
+
Artifact
+
Conversation
+
Environment Observation
        ↓
Context Manager
        ↓
Current Context

Context는 source of truth가 아니다.

8. Memory / Knowledge Boundary

현재 가장 유력한 구조:

Cognitive Information
├── Memory
└── Knowledge
        ↓
Shared Information / Retrieval Interface
        ↓
Context Manager

Memory와 Knowledge를 완전히 합치지도,
완전히 독립된 retrieval system으로 분리하지도 않는 Hybrid 방향을 검토한다.

9. Harness Boundary

현재 가장 유력한 구조:

Agent
   ↓
Harness Contract
   ├── Context
   ├── Capability
   ├── Policy
   ├── Runtime
   ├── Memory Access
   ├── Observability
   └── Recovery

여러 subsystem은 논리적으로 Harness에 속할 수 있지만,
물리적으로 하나의 Package / Process / Service일 필요는 없다.

10. Harness vs Runtime

현재 후보:

Harness
   ↓
Runtime

Harness는 stable execution boundary.

Runtime은 교체 가능한 execution implementation.

11. Harness vs Orchestrator
Orchestrator
= What should happen?

Harness
= How can it execute safely and persistently?

직접적인 책임 중복을 최소화한다.

12. Memory / Knowledge / Artifact

세 가지를 구분한다.

Artifact
= 실제 결과물

Memory
= 경험 / 지속적인 맥락

Knowledge
= 사실 / 정보

Artifact는 Evidence가 될 수 있다.

13. Updated Candidate Architecture
                       CONSTITUTION
                            │
                       IDENTITY
                            │
                          AGENT
                            │
                      TASK / SESSION
                            │
                      ORCHESTRATION
                            │
                 ┌──────────┼──────────┐
                 │          │          │
               STATE     CONTEXT    HARNESS
                 │          │          │
                 ├────┬─────┘          │
                 │    │                │
              MEMORY KNOWLEDGE      RUNTIME
                 │    │                │
                 └────┼────────────────┘
                      │
                 CAPABILITY
                      │
                   POLICY
                      │
                 PERMISSION
                      │
                  SANDBOX
                      │
                 EXECUTION
                      │
                VERIFICATION
                      │
              OBSERVABILITY
                      │
                EVALUATION
                      │
                 EXPERIENCE
                      │
                  LEARNING
                      │
             CONTROLLED ADAPTATION
14. Critical Stable Boundaries

현재 안정적으로 유지할 후보:

Identity ≠ Model
Agent ≠ Model
Task ≠ Session
Task State ≠ Context
State ≠ Memory
Memory ≠ Knowledge
Memory ≠ Artifact
Capability ≠ Permission
Policy ≠ Permission
Harness ≠ Agent
Harness ≠ Runtime
Orchestrator ≠ Runtime
Execution ≠ Verification
Verification ≠ Evaluation
Experience ≠ Memory
Learning ≠ Memory
15. Newly Resolved Questions

P0 Research를 통해 상대적으로 명확해진 부분을 기록한다.

예:

Task State should survive Runtime replacement.
Context is reconstructable.
Harness is a logical boundary rather than necessarily a physical service.
Memory and Knowledge are semantically distinct but may share infrastructure.
16. Remaining Conflicts

아직 남아 있는 문제:

Harness와 Runtime의 정확한 API 경계
Task State Store의 실제 구현
Knowledge Architecture
Artifact Architecture
Identity Persistence
Orchestration Contract
Event Architecture
17. Remaining P1 Research
P1
├── Artifact Architecture
├── Identity Persistence
└── Orchestration Contract

필요성이 낮은 것은 추가하지 않는다.

18. Physical Architecture Question

Logical Boundary와 Physical Boundary를 분리한다.

예:

Logical:
Memory System

Physical:
same process / database / service

초기에는 Modular Monolith를 우선 검토한다.

19. Contract-first Direction

다음 Stable Contract 후보:

Identity Contract
Task Contract
Session Contract
State Contract
Context Contract
Memory Contract
Knowledge Contract
Capability Contract
Permission Contract
Execution Contract
Verification Contract
Evaluation Contract
Harness Contract
20. Future Resilience

특정:

Model
Runtime
Database
Vector Store
Graph Store
Sandbox
Framework

를 Architecture의 핵심으로 고정하지 않는다.

21. Historical / Current / Emerging Synthesis

각 판단을:

Historical Principle
+
Current Evidence
+
Emerging Research

로 비교하고,

최종적으로:

Stable Principle

를 추출한다.

22. Architecture Classification

각 개념을:

FOUNDATIONAL
CURRENT
EMERGING
EXPERIMENTAL
DEFERRED
REJECTED

로 분류한다.

23. Preliminary Architecture Direction

현재 가장 유력한 방향:

NOAH는 Identity를 중심으로 장기 Task를 수행하는 Agent이며,
Harness와 Runtime을 통해 Context / State / Memory / Knowledge / Capability를 안전하게 사용하고,
Verification과 Evaluation을 통해 실행을 검증하며,
Experience를 Learning으로 연결해 미래 행동을 개선한다.

24. Remaining Unknowns

P1 Research가 해결해야 할 문제:

Artifact가 별도 subsystem이어야 하는가?
Identity Persistence는 어떤 저장 구조를 가져야 하는가?
Orchestration Contract는 어디에 위치하는가?
Harness Contract의 최소 API는 무엇인가?
Knowledge Retrieval은 Memory Retrieval과 어떻게 결합하는가?
Event system은 공통 infrastructure가 되어야 하는가?
25. Review Decision

v0.2에서는 아직 Blueprint를 수정하지 않는다.

현재 결과를 Candidate Architecture로 유지한다.

26. Next Step
Integration Review v0.2
        ↓
P1 Research
├── Artifact Architecture
├── Identity Persistence
└── Orchestration Contract
        ↓
Integration Review v0.3
        ↓
DDR
        ↓
02-Architecture
        ↓
Integrated PoC
27. Review Boundary

이번 Review에서는:

Final Blueprint
Final Runtime
Final Memory
Final Harness
Final Knowledge
Final Identity

를 확정하지 않는다.