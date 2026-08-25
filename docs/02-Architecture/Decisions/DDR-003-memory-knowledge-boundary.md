# DDR-003 — Memory / Knowledge Boundary

> Project NOAH Architecture Decision Record
> Decision ID: DDR-003
> Status: Accepted
> Date: 2026-08-25

---

# 1. Decision

Project NOAH는 Memory와 Knowledge를 의미적으로 구분한다.

Memory는 경험, 개인적/프로젝트적 지속성, 과거의 중요한 정보와 학습된 맥락을 관리한다.

Knowledge는 외부 또는 내부의 사실, 정보, 문서, 구조화된 지식을 관리한다.

그러나 두 시스템을 물리적으로 완전히 분리하지는 않는다.

Memory와 Knowledge는 공통 Information / Retrieval Interface를 통해 Context Manager와 연결될 수 있다.

핵심 원칙:

Memory
≠
Knowledge

그리고:

Memory System
+
Knowledge System
→
Shared Information Interface
→
Context Manager

를 Candidate Architecture로 채택한다.

---

# 2. Context

Architecture Integration Review와 Memory / Knowledge Boundary Research에서
Memory, Knowledge, Context, State, Artifact의 책임이 서로 겹칠 가능성이 확인되었다.

특히 동일한 정보가:

- 사용자 Memory
- Project Memory
- Project Knowledge
- External Knowledge
- Artifact
- Task State

중 여러 형태로 존재할 수 있다.

따라서 단순한 저장 위치가 아니라:

- 의미
- 출처
- 목적
- 수명
- 권위
- 신뢰
- 소유권

을 기준으로 구분해야 한다.

---

# 3. Problem

다음과 같이 모든 정보를 하나의 Memory로 통합하면:

```text
Memory
├── User facts
├── Project facts
├── External knowledge
├── Experience
├── Documents
└── Current state

다음 문제가 발생할 수 있다.

Memory semantics 혼합
Privacy boundary 약화
Freshness 관리 어려움
Provenance 구분 어려움
Forgetting과 Deprecation 혼합
Canonical State와 Memory 혼합
External Knowledge와 User Memory 혼합

따라서 Memory와 Knowledge를 구분한다.

4. Decision Scope

이번 Decision에서 정의하는 대상:

Memory
Knowledge
Experience
Context
State
Artifact
Retrieval
Provenance
Freshness
Scope

이번 Decision에서는 다음을 최종 결정하지 않는다.

Memory Database
Vector Database
Graph Database
Embedding Model
Knowledge Graph implementation
Retrieval Framework
Storage Provider

# 5. Memory Definition

Memory는 Agent가 과거의 경험과 지속적인 사용자/프로젝트 맥락을 미래 행동에 활용하기 위해 유지하는 정보다.

후보:

```text
Memory
├── Episodic
├── Semanticized Experience
├── User Preferences
├── Relationship Context
├── Project History
└── Lessons

모든 Memory가 동일한 형태를 가질 필요는 없다.

6. Knowledge Definition

Knowledge는 특정 경험의 기억이라기보다 사실, 정보, 문서 및 구조화된 지식으로 활용되는 정보다.

후보:

Knowledge
├── External Documentation
├── Research
├── Project Knowledge
├── Structured Facts
├── Domain Knowledge
└── Verified Information
7. Experience

Experience는 실제로 발생한 사건이다.

Experience
↓
Evaluation
↓
Memory

필요한 경우:

Experience
↓
Reflection / Generalization
↓
Knowledge

로 발전할 수 있다.

8. Memory vs Knowledge

핵심 의미 구분:

Memory
= 경험과 지속성 중심

Knowledge
= 사실과 정보 중심

따라서 동일한 정보라도 출처와 목적에 따라 다른 역할을 가질 수 있다.

9. Example

다음 세 정보는 서로 다른 semantics를 가진다.

External Knowledge:
"Python 3.13은 특정 기능을 제공한다."

Project Knowledge:
"Project NOAH는 Python 3.13을 사용한다."

Project Memory:
"NOAH 개발 환경을 Python 3.13으로 결정한 이유가 있다."

내용이 일부 겹쳐도 각각의 역할은 다르다.

10. State Separation

State는 Memory나 Knowledge가 아니다.

State
= 현재 canonical condition

Memory
= 과거의 경험 / 지속 정보

Knowledge
= 사실 / 정보

예:

State:
Task = Running

Memory:
과거에 이 Task에서 발생한 오류

Knowledge:
해당 오류의 일반적인 원인
11. Context Separation

Context는 저장소가 아니다.

Memory
+
Knowledge
+
State
+
Artifact
+
Conversation
+
Environment
↓
Context Projection

Context는 현재 Model execution에 필요한 정보만 제공한다.

12. Artifact Separation

Artifact는 실제 결과물이다.

Artifact
= 실제 작업 결과

Memory
= 결과물과 관련된 경험

Knowledge
= 결과물에서 추출되거나 결과물과 관련된 사실

예:

Artifact:
Architecture.md

Memory:
이 문서를 작성하면서 어떤 결정이 이루어졌다.

Knowledge:
현재 NOAH Architecture는 특정 구조를 사용한다.
13. Common Information Interface

Memory와 Knowledge는 semantic layer에서 분리하지만
공통 Interface를 사용할 수 있다.

후보:

Information Interface
├── Retrieve
├── Search
├── Explain Source
├── Update
├── Archive
└── Forget / Deprecate

정확한 API는 별도 Specification에서 결정한다.

14. Retrieval

공통 retrieval pipeline:

Query
↓
Candidate Retrieval
↓
Ranking
↓
Trust / Scope Filtering
↓
Projection
↓
Context

Memory와 Knowledge는 Ranking 기준이 일부 다를 수 있다.

15. Memory Retrieval

Memory에서는 다음 요소가 중요할 수 있다.

Relevance
Recency
Personal Importance
Relationship Relevance
Experience Similarity
16. Knowledge Retrieval

Knowledge에서는:

Relevance
Source Authority
Freshness
Version
Domain Reliability

등이 중요할 수 있다.

17. Provenance

Memory와 Knowledge 모두 Provenance를 가진다.

후보:

Source
Created At
Updated At
Author
Agent
Evidence
Derived From
Confidence
Verification
18. Trust

모든 정보가 동일한 신뢰도를 가지지 않는다.

후보:

User-confirmed
Verified external source
Observed environment
Tool result
Agent inference
Unverified generated information
19. Scope

Memory Scope:

User
Project
Agent
Session
Task
Temporary

Knowledge Scope:

Public
External
Project
Private
Internal

Scope와 Access Policy를 함께 고려한다.

20. Ownership

Memory:

User
Project
NOAH

Knowledge:

External Source
Project
Public
User

Ownership semantics가 다를 수 있다.

21. Temporal Semantics

Memory와 Knowledge 모두 시간 정보를 가질 수 있다.

Memory:

When did this happen?
When was this true?

Knowledge:

When was this source valid?
When was it verified?

따라서 Temporal Metadata를 공통적으로 고려한다.

22. Freshness

Knowledge는 최신성의 영향을 크게 받을 수 있다.

예:

Current API
vs
Deprecated API

Memory 역시 시간이 지나면서 stale될 수 있다.

23. Contradiction

Memory와 Knowledge 모두 충돌을 가질 수 있다.

Source A
→ X

Source B
→ Y

충돌 시:

Source Authority
+
Timestamp
+
Verification
+
Scope

등을 활용한다.

24. Forgetting vs Deprecation

Memory:

Active
↓
Stale
↓
Archived
↓
Forgotten

Knowledge:

Active
↓
Outdated
↓
Deprecated

이 차이를 유지하는 방향을 채택한다.

25. Memory Promotion

Experience가 Memory가 되는 과정:

Experience
↓
Candidate
↓
Evaluation
↓
Memory

모든 Experience를 Memory로 승격하지 않는다.

26. Knowledge Promotion

외부 또는 내부 정보도 검증 후 Knowledge로 승격할 수 있다.

Source
↓
Candidate
↓
Validation
↓
Knowledge

Generated information은 검증 전까지 확정 Knowledge로 취급하지 않는다.

27. Memory → Knowledge

Experience를 일반화하면 Knowledge가 될 수 있다.

Memory
↓
Reflection
↓
Generalization
↓
Knowledge

이 경우 원래 Memory 및 Evidence를 보존한다.

28. Knowledge → Memory

외부 Knowledge가 프로젝트에 중요한 지속 정보가 되면
Memory 또는 Project Memory의 근거가 될 수 있다.

예:

Knowledge:
Python 3.13 behavior

Project Memory:
NOAH에서는 Python 3.13을 사용하는 것으로 결정했다.
29. Security Boundary

Memory와 Knowledge는 서로 다른 보안 요구사항을 가진다.

Memory:

Privacy
Consent
User Scope
Deletion

Knowledge:

Source Trust
Integrity
Licensing
Access
Provenance
30. Memory Poisoning

Memory에 들어가는 정보는:

Experience
↓
Validation
↓
Memory

과정을 거치는 것을 원칙으로 한다.

31. Knowledge Poisoning

외부 정보도:

External Source
↓
Validation
↓
Knowledge

단계를 거친다.

32. Context Projection

최종적으로:

Memory
Knowledge
State
Artifact

가:

Context Manager

를 통해 현재 실행에 필요한 정보로 projection된다.

33. Agent Access

Agent가 Memory / Knowledge 저장소의 구현을 직접 알 필요는 없다.

Agent
↓
Information Interface
↓
Memory / Knowledge
34. Harness Relationship

Harness는 Information Interface를 Agent에 제공할 수 있다.

Agent
↓
Harness
↓
Information Interface
↓
Memory / Knowledge
35. Capability Relationship

Memory / Knowledge Retrieval도 Capability로 노출될 수 있다.

예:

memory.search
knowledge.search
knowledge.explain_source

하지만 내부 Storage implementation은 외부화하지 않는다.

36. Identity Relationship

Identity-relevant Memory는 일반 Memory보다 높은 중요도를 가질 수 있다.

그러나:

Memory
≠
Identity Core

를 유지한다.

37. Orchestration Relationship

Multi-Agent 환경에서 Memory / Knowledge Scope를 명확하게 한다.

Agent A
→ Memory A

Agent B
→ Memory B

Shared Knowledge
→ Explicitly Granted
38. Evaluation Relationship

Memory 평가:

Recall
Freshness
Utility
Contradiction
Forgetting
Personalization

Knowledge 평가:

Correctness
Source Reliability
Freshness
Coverage
Retrieval Accuracy
Citation
39. Artifact Relationship

Artifact는 Memory / Knowledge의 source가 될 수 있다.

Artifact
↓
Extraction
├── Memory Candidate
└── Knowledge Candidate
40. Storage Abstraction

Memory와 Knowledge의 Physical Storage는 교체 가능하다.

후보:

SQL
Document Store
Vector
Graph
Filesystem
Object Storage
41. No Backend Lock-in

다음은 Architecture Contract에 포함하지 않는다.

Specific Vector DB
Specific Graph DB
Specific Embedding Model
Specific Search Engine
42. Consequences
Positive
Memory semantics 명확
Knowledge semantics 명확
Privacy boundary 개선
Provenance 관리 용이
Retrieval infrastructure 공유 가능
Storage 교체 가능
Long-term evolution 가능
Negative
두 개념을 관리해야 하는 복잡성
중복 저장 가능성
Cross-system synchronization
Contradiction resolution 필요
Retrieval architecture 복잡성 증가
43. Alternatives Considered
Alternative A — Everything is Memory

Rejected.

이유:

External Knowledge와 User Memory 혼합
Freshness 관리 어려움
Privacy boundary 약화
Semantics 혼합
Alternative B — Everything is Knowledge

Rejected.

이유:

Experience와 relationship continuity 표현 어려움
User-specific information 관리 어려움
Alternative C — Completely Separate Systems

Deferred / Not Preferred.

의미적으로는 분리하지만 물리적으로 완전히 분리하면 중복과 통합 비용이 증가한다.

Alternative D — Unified Information Layer

Accepted as an interface concept.

Memory와 Knowledge를 하나의 의미로 합치는 것이 아니라,
공통 Retrieval / Information Interface를 제공하는 방향이다.

44. Relationship to Previous Decisions
DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

와 직접 연결된다.

또한:

DDR-004
Artifact Architecture

DDR-005
Identity Persistence

DDR-006
Orchestration Contract

와 연결된다.

45. Implementation Implications

향후:

Memory Interface
Knowledge Interface
Information / Retrieval Interface
Context Projection

등의 논리적 경계를 고려한다.

구체적인 storage는 구현 단계에서 선택한다.

46. Validation Plan

최소 PoC에서:

User Memory
Project Memory
External Knowledge
Project Knowledge
Artifact-derived Knowledge

를 동일한 Task에서 사용해본다.

평가:

Retrieval Quality
Context Quality
Freshness
Trust
Privacy
Task Success
Cost
47. Acceptance Criteria
☐ Memory와 Knowledge가 의미적으로 구분된다.
☐ State와 Context가 혼합되지 않는다.
☐ Artifact와 Memory/Knowledge가 구분된다.
☐ 공통 Retrieval Interface가 가능하다.
☐ Provenance가 유지된다.
☐ Scope / Ownership이 유지된다.
☐ Memory Poisoning 방어가 가능하다.
☐ Knowledge freshness를 관리할 수 있다.
☐ Storage backend가 교체 가능하다.
48. Decision Status
Status: Accepted
Confidence: Medium

PoC 결과에 따라 수정할 수 있다.

49. Review Conditions

다음 상황에서 재검토한다.

새로운 Memory Architecture 등장
Knowledge Graph requirement 증가
User privacy requirement 변화
Retrieval architecture 변경
Long-term Memory 규모 증가
Unified information layer가 성능상 병목이 되는 경우
50. Final Decision

Project NOAH는 Memory와 Knowledge를 의미적으로 분리한다.

Memory는 경험과 개인/프로젝트의 지속적인 맥락을 관리하며,
Knowledge는 외부 및 내부의 사실·정보·문서를 관리한다.

두 시스템은 완전히 동일한 저장소로 통합하지 않지만,
공통 Information / Retrieval Interface를 통해 Context Manager와 연결될 수 있다.

State는 현재 canonical condition으로,
Context는 Model-facing projection으로,
Artifact는 실제 작업 결과물로 각각 분리한다.

이 구조를 통해 Memory, Knowledge, State, Context, Artifact 사이의 책임을 명확히 하고
향후 구현 기술 교체 가능성을 유지한다.