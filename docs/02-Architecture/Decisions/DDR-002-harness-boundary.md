# DDR-002 — Harness Boundary

> Project NOAH Architecture Decision Record
> Decision ID: DDR-002
> Status: Accepted
> Date: 2026-08-25

---

# 1. Decision

Project NOAH는 Agent와 실행 Infrastructure 사이에
논리적인 Harness Boundary를 둔다.

Harness는 Agent가 안전하고 지속적이며 관찰 가능한 방식으로
실행될 수 있도록 Context, Capability, Policy, Runtime,
Recovery, Observability 등의 실행 지원 기능을 연결하는
stable execution boundary로 정의한다.

핵심 원칙:

Agent
≠
Harness

Harness
≠
Runtime

Harness는 반드시 하나의 물리적 Service 또는 Package일 필요가 없다.

---

# 2. Context

Architecture Integration Review와 Harness Boundary Research를 통해
Agent, Runtime, Orchestrator, Context, Capability, Security 등의
책임이 서로 중복될 가능성이 확인되었다.

특히:

- Agent가 infrastructure를 직접 소유하는 문제
- Runtime과 Harness의 책임 중복
- Orchestrator와 Harness의 책임 중복
- Context / Memory / Capability의 과도한 결합
- Security enforcement가 Model 판단에 종속되는 문제
- Runtime 교체 시 Agent architecture까지 영향을 받는 문제

를 방지하기 위해 Harness Boundary가 필요하다.

---

# 3. Problem

다음과 같은 구조는 장기적으로 강한 결합을 만든다.

Agent
 ↓
Runtime
 ↓
Database
 ↓
Tool
 ↓
Sandbox

Agent가 실제 Infrastructure의 구현을 직접 이해하게 되면:

- Model 교체가 어려워지고
- Runtime 교체가 어려워지며
- Testing이 어려워지고
- Security Boundary가 약해지고
- Architecture 전체가 특정 구현에 종속될 수 있다.

---

# 4. Decision Scope

이번 Decision에서는:

- Agent
- Harness
- Runtime
- Orchestrator
- Context
- Capability
- Policy
- Permission
- Recovery
- Observability

사이의 책임 경계를 결정한다.

다음은 이번 Decision에서 확정하지 않는다.

- 최종 Runtime Framework
- 최종 Harness Framework
- 최종 Memory Backend
- 최종 Sandbox
- 최종 Orchestrator
- Physical Service Decomposition

---

# 5. Agent Responsibility

Agent는 주로:

- Goal Understanding
- Reasoning
- Planning
- Decision Making
- Capability Selection
- Result Interpretation

을 담당한다.

Agent는 일반적으로:

- Database
- Storage
- Sandbox
- Credential Store
- Telemetry Backend
- Task Store

의 실제 구현을 직접 소유하지 않는다.

---

# 6. Harness Definition

Harness는 Agent가 외부 시스템과 안전하고 지속적으로 상호작용할 수 있도록 하는 실행 계층이다.

후보 책임:

- Context management
- Capability exposure
- Policy integration
- Runtime integration
- State access
- Memory access
- Recovery
- Observability
- Verification integration

모든 기능이 하나의 구현체에 직접 들어가야 한다는 의미는 아니다.

---

# 7. Logical Boundary

Harness는 Logical Architecture Boundary로 정의한다.

```text
Agent
   ↓
Harness Contract
   ├── Context
   ├── Capability
   ├── Policy
   ├── Runtime
   ├── Memory Access
   ├── Recovery
   └── Observability

이들은 내부적으로 별도 Module / Component로 구현할 수 있다.

8. Harness vs Runtime

Runtime은 실제 Execution Lifecycle을 담당한다.

Runtime
├── Start
├── Run
├── Pause
├── Resume
├── Cancel
├── Retry
├── Checkpoint
└── Recover

Harness는 Runtime을 사용하는 Agent-facing execution substrate로 본다.

따라서:

Harness
 ↓
Runtime

관계를 기본 후보로 채택한다.

9. Harness vs Orchestrator

Orchestrator:

무엇을 실행할 것인가?

Harness:

선택된 실행을 어떻게 안전하고 지속적으로 수행할 것인가?

예:

Task
 ↓
Orchestrator
 ↓
Execution Plan
 ↓
Harness
 ↓
Runtime
 ↓
Execution

Orchestrator와 Harness의 책임을 직접적으로 중복시키지 않는다.

10. Harness vs Context

Context Manager는 Harness 내부 Component로 구현할 수 있다.

Harness
 └── Context Manager

그러나 Context의 실제 Source of Truth는 Task State, Memory,
Knowledge, Artifact 등에 존재한다.

Harness는 필요한 정보를 Context로 projection한다.

11. Harness vs Memory

Harness는 Memory 자체를 소유하지 않는다.

Harness
 ↓
Memory Interface
 ↓
Memory System

Memory Backend는 교체 가능하게 유지한다.

12. Harness vs Capability

Harness는 Agent가 Capability를 사용할 수 있도록 연결한다.

Agent
 ↓
Harness
 ↓
Capability
 ↓
Policy
 ↓
Execution

Capability의 실제 구현은 Harness와 분리한다.

13. Harness vs Security

Security-critical authorization을 Model 판단에만 의존하지 않는다.

후보:

Agent Request
 ↓
Harness
 ↓
Policy
 ↓
Permission
 ↓
Runtime / Sandbox
 ↓
Execution

Harness는 Security Enforcement에 필요한 Component를 연결할 수 있다.

14. Harness vs Observability

Harness는 중요한 실행을 Trace / Event / Metric으로 남길 수 있어야 한다.

예:

Harness
 ↓
Observability
 ├── Agent
 ├── Task
 ├── Capability
 ├── Permission
 ├── Runtime
 ├── State
 └── Verification

Observability Backend 자체는 교체 가능하게 유지한다.

15. Harness vs Verification

Harness는 Verification을 실행 경로에 연결할 수 있다.

Execution
 ↓
Verification
 ↓
State Commit

하지만 Verification logic 자체를 Harness가 모두 소유할 필요는 없다.

16. Harness vs Recovery

Long-running Task를 위해 Harness는 Recovery mechanism을 연결할 수 있어야 한다.

Runtime Failure
 ↓
Persisted Task State
 ↓
Harness Recovery
 ↓
New Runtime
 ↓
Resume

Recovery가 성공하려면 Task State와 Runtime State가 적절히 분리되어 있어야 한다.

17. Harness Contract

초기 Contract 후보:

Harness
├── Context Access
├── State Access
├── Capability Access
├── Policy Access
├── Runtime Control
├── Recovery
├── Observability
└── Verification Hooks

정확한 API는 구현 단계에서 결정한다.

18. Harness and Task State

Harness는 Task State를 직접적인 source of truth로 대체하지 않는다.

Task State
→ canonical durable state

Harness
→ access / coordination
19. Harness and Identity

Identity Core는 Harness의 소유물이 아니다.

Identity Store
 ↓
Identity Projection
 ↓
Harness / Agent

Harness는 Identity를 Agent가 사용할 수 있도록 projection하는 역할을 가질 수 있다.

20. Harness and Artifacts

Harness는 Artifact에 접근할 수 있도록 연결한다.

Harness
 ↓
Artifact Interface
 ↓
Artifact Store

Artifact의 실제 lifecycle은 Artifact Architecture가 담당한다.

21. Harness and Orchestration

복수 Agent가 필요한 경우:

Task
 ↓
Orchestrator
 ↓
Delegation
 ↓
Harness
 ↓
Agent / Runtime

각 Agent가 동일한 Harness Contract를 사용할 수 있는 구조를 검토한다.

22. Single Agent Default

Harness는 Multi-Agent를 전제로 하지 않는다.

기본:

Task
 ↓
Agent
 ↓
Harness
 ↓
Runtime

필요한 경우:

Task
 ↓
Orchestrator
 ↓
Multiple Agents
 ↓
Each Agent Harness

로 확장한다.

23. Multi-Agent Harness

각 Subagent에 별도의 Harness를 만들 필요가 있는지 구현 단계에서 검증한다.

논리적으로는:

Agent A → Harness
Agent B → Harness
Agent C → Harness

또는:

Shared Harness Infrastructure
 ├── Agent A
 ├── Agent B
 └── Agent C

둘 모두 가능성을 유지한다.

24. Model Independence

Harness는 특정 Model Provider에 종속되지 않는다.

Model A
Model B
Local Model
Future Model
      ↓
Harness Contract

를 유지한다.

25. Runtime Independence

Runtime Framework 역시 교체 가능하다.

Runtime A
Runtime B
Future Runtime
      ↓
Harness Contract
26. Physical Architecture

Harness는 처음부터 별도의 Service로 만들지 않는다.

초기에는:

NOAH
└── Modular Monolith
    └── Harness Modules

를 우선 검토한다.

필요성이 확인되면 이후 Service / Process 분리를 고려한다.

27. Stability vs Replaceability

Stable:

Harness Contract
Execution Boundary
Security Integration
Context Integration
Recovery Contract
Observability Contract

Replaceable:

Runtime
Database
Sandbox
Telemetry
Model
Memory Backend
Orchestrator
28. Security Consequences

Harness Boundary는 Agent가 직접:

filesystem
network
credential
process
external services

에 접근하는 것을 막는 중요한 경계가 된다.

29. Failure Consequences

Harness가 실패하거나 잘못 설계되면:

Agent execution 실패
Context 손실
Recovery 실패
Observability 손실
Permission bypass

등이 발생할 수 있다.

따라서 Harness 자체도 Evaluation 대상이 된다.

30. Performance Consequences

추상화 계층이 증가하면:

latency
serialization
state transfer
tracing overhead

가 증가할 수 있다.

따라서 필요 이상으로 Harness Boundary를 세분화하지 않는다.

31. Alternatives Considered
Alternative A — Agent owns Runtime

Rejected.

Agent가 infrastructure 구현과 강하게 결합된다.

Alternative B — Harness = Runtime

Deferred / Not preferred.

간단하지만 Runtime 교체성과 logical boundary가 약해질 수 있다.

Alternative C — Harness as Separate Service

Deferred.

초기에는 과도한 Physical Distribution이 될 가능성이 있다.

Alternative D — No Harness Boundary

Rejected.

Agent / Infrastructure coupling이 과도해질 가능성이 있다.

32. Relationship to Previous Decisions
DDR-001
Task State / Runtime Boundary

와 직접적으로 연결된다.

Task State
      ↓
Harness
      ↓
Runtime

또한:

DDR-003
Memory / Knowledge Boundary
DDR-004
Artifact Architecture
DDR-005
Identity Persistence
DDR-006
Orchestration Contract

과 연결된다.

33. Validation Plan

최소 PoC:

User
 ↓
Task
 ↓
Agent
 ↓
Harness
 ↓
Runtime
 ↓
Capability
 ↓
Policy
 ↓
Artifact
 ↓
Verification
 ↓
Evaluation

검증:

- Runtime replacement
- Context reconstruction
- Permission enforcement
- Trace completeness
- Recovery
34. Acceptance Criteria
☐ Agent가 Runtime 구현에 직접 의존하지 않는다.
☐ Agent가 Storage 구현에 직접 의존하지 않는다.
☐ Capability 실행이 Harness 경계를 통과한다.
☐ Policy / Permission이 실행 전에 적용된다.
☐ Runtime replacement가 가능하다.
☐ Recovery를 지원할 수 있다.
☐ Observability가 유지된다.
☐ Context를 State에서 재구성할 수 있다.
☐ Harness가 특정 Model Provider에 종속되지 않는다.
35. Decision Status
Status: Accepted
Confidence: Medium

PoC 결과에 따라 수정할 수 있다.

36. Review Condition

다음의 경우 이 DDR을 재검토한다.

새로운 Runtime Architecture
Distributed Agent Runtime
새로운 Agent Harness 연구
PoC에서 책임 중복 발견
Performance 문제가 심각해짐
Security boundary 변경
Multi-Agent scale 증가
37. Final Decision

Project NOAH는 Agent와 Infrastructure 사이에 Logical Harness Boundary를 둔다.

Harness는 Context, Capability, Policy, Runtime, Recovery, Observability 및 관련 실행 지원 Component를 연결하는 stable execution boundary다.

Harness는 Agent의 판단 자체를 대체하지 않으며, Runtime이나 특정 Infrastructure 구현과 동일하지 않다.

Harness는 처음부터 별도의 Physical Service로 분리하지 않으며, Modular Architecture 내부의 Logical Boundary로 먼저 구현한다.

향후 실제 요구사항과 PoC 결과에 따라 Physical decomposition을 결정한다.