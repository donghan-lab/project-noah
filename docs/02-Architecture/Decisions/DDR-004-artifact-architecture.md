# DDR-004 — Artifact Architecture

> Project NOAH Architecture Decision Record
> Decision ID: DDR-004
> Status: Accepted
> Date: 2026-08-25

---

# 1. Decision

Project NOAH는 Artifact를 단순한 File 또는 Tool Output이 아니라
지속적으로 추적할 수 있는 semantic work object로 정의한다.

Artifact는 실제 Storage 구현과 분리된 Contract를 가진다.

핵심 원칙:

Artifact
≠
File

Artifact
≠
Workspace

Artifact
≠
Task State

Artifact는 다음과 같은 지속적인 결과물을 표현할 수 있다.

- Source Code
- Document
- Dataset
- Media
- Build Result
- Test Result
- Configuration
- Evaluation Result
- Evidence
- Model / Binary
- Generated Output

---

# 2. Context

Architecture Integration Review와 Artifact Architecture Research를 통해
Artifact가 다음 영역과 반복적으로 연결된다는 점이 확인되었다.

- Task
- Workspace
- State
- Memory
- Knowledge
- Verification
- Evaluation
- Recovery
- Multi-Agent Collaboration

특히 Long-running Task에서는 실제 작업 결과물이
대화나 Context보다 오래 지속될 수 있다.

따라서 Artifact를 독립적인 논리적 개념으로 정의한다.

---

# 3. Problem

Artifact를 단순 File로 취급하면:

- Semantic meaning이 사라질 수 있음
- Versioning이 File Path에 종속
- Provenance 추적 어려움
- Task와의 관계 표현 어려움
- Verification Evidence 연결 어려움
- Multi-Agent collaboration 어려움
- Storage backend 교체 어려움

이 발생할 수 있다.

---

# 4. Decision Scope

이번 Decision의 대상:

- Artifact
- Artifact Identity
- Artifact Version
- Artifact Provenance
- Artifact Lineage
- Artifact Ownership
- Artifact Scope
- Artifact Lifecycle
- Artifact Storage
- Artifact Verification
- Artifact Evidence
- Artifact Permission

다음은 이번 Decision에서 최종 결정하지 않는다.

- 최종 Storage Provider
- Git 사용 범위
- Object Storage
- Artifact Graph 구현
- Physical Artifact Service
- 최종 Artifact Registry 구현

---

# 5. Artifact Definition

Artifact는 Agent 또는 User가 생성·수정·사용·검증하는
지속적인 작업 대상 또는 결과물이다.

예:

```text
Artifact
├── Document
├── Source Code
├── Dataset
├── Image
├── Audio
├── Video
├── Configuration
├── Build Result
├── Test Result
├── Evaluation Result
└── Evidence
6. Artifact vs File

File은 Artifact의 하나의 physical representation일 수 있다.

Artifact
 ↓
File

예:

Architecture Document
 ↓
Architecture.md

그러나 Artifact의 Identity를 단순 Path에 의존하지 않는다.

7. Artifact Identity

Artifact는 stable ID를 가진다.

후보:

Artifact
├── ID
├── Type
├── Version
├── Owner
├── Scope
└── Status

Path나 URI가 변경되더라도 Artifact identity가 유지될 수 있어야 한다.

8. Artifact Version

Artifact는 Version을 가질 수 있다.

Artifact
 ↓
Version 1
 ↓
Version 2
 ↓
Version 3

Version history는 중요한 Artifact에서 보존한다.

9. Artifact Lineage

Artifact가 어떻게 만들어졌는지 추적할 수 있어야 한다.

예:

Source Dataset
 ↓
Processing Script
 ↓
Processed Dataset
 ↓
Analysis
 ↓
Report

Lineage 정보를 통해 결과물의 생성 관계를 추적할 수 있도록 한다.

10. Artifact Provenance

Artifact는 가능한 경우:

Source
Author
Agent
Task
Tool
Environment
Timestamp
Transformation
Version

등의 Provenance를 가진다.

11. Artifact Ownership

Artifact의 Ownership을 명시할 수 있어야 한다.

후보:

User
Project
Agent
System
External
Shared

Ownership과 Access Permission을 동일한 개념으로 취급하지 않는다.

12. Artifact Scope

Artifact는 Scope를 가질 수 있다.

Global
User
Project
Session
Task
Agent
Temporary

Scope는 Permission과 함께 사용될 수 있다.

13. Artifact Lifecycle

기본 Lifecycle 후보:

Created
 ↓
Modified
 ↓
Validated
 ↓
Published
 ↓
Archived
 ↓
Deleted

모든 Artifact가 동일한 Lifecycle을 가질 필요는 없다.

14. Temporary vs Durable Artifact

Artifact는 Temporary와 Durable로 구분할 수 있다.

Temporary
→ intermediate output

Durable
→ source code / report / project document

Retention Policy를 통해 장기 저장 여부를 결정한다.

15. Artifact Storage Abstraction

Artifact의 Logical Model과 Physical Storage를 분리한다.

가능한 Backend:

Filesystem
Git
Database
Object Storage
External Repository
NAS
Cloud Storage

특정 Backend를 Architecture Contract에 고정하지 않는다.

16. Artifact Store

향후 다음과 같은 Logical Interface를 사용할 수 있다.

Artifact Store
├── Create
├── Read
├── Update
├── Version
├── Delete
├── Archive
├── Restore
├── List
└── Search

정확한 API는 Specification 단계에서 결정한다.

17. Artifact and Task

하나의 Task가 여러 Artifact를 생성할 수 있다.

Task
 ├── Artifact A
 ├── Artifact B
 └── Artifact C

Task State에는 Artifact 자체가 아니라 Artifact Reference를 저장하는 방향을 채택한다.

18. Artifact and Workspace

Workspace는 작업 환경이며 Artifact의 실제 작업 공간이 될 수 있다.

Workspace
├── Artifacts
├── Temporary Files
├── Processes
└── Environment State

Workspace와 Artifact의 Lifecycle을 동일하게 취급하지 않는다.

19. Artifact and State

Artifact는 Task State가 아니다.

Task State
= 현재 Task의 상태

Artifact
= 작업의 지속적인 결과물

Task State는 Artifact Reference를 보유할 수 있다.

20. Artifact and Memory

Memory는 Artifact 자체가 아니라:

생성 이유
중요한 변경
사용 경험
실패 경험
향후 활용 정보

등을 기억할 수 있다.

Artifact
 ↕
Memory

관계를 유지한다.

21. Artifact and Knowledge

Artifact는 Knowledge의 Source가 될 수 있다.

Artifact
 ↓
Extraction
 ↓
Knowledge

반대로 Knowledge를 사용하여 Artifact를 생성할 수도 있다.

Knowledge
 ↓
Agent
 ↓
Artifact
22. Artifact and Capability

Capability가 Artifact를:

Read
Create
Modify
Move
Delete
Publish

할 수 있다.

이 행동들은 Permission / Policy를 통과해야 한다.

23. Artifact Permission

Artifact에 적용할 수 있는 Permission 후보:

Read
Write
Delete
Share
Publish
Execute

Artifact Type과 Risk에 따라 정책이 달라질 수 있다.

24. Artifact Security

Artifact에는:

Secrets
Credentials
Personal Data
Executable Code
Untrusted Content

가 포함될 수 있다.

따라서 Artifact도 Security Policy의 대상이다.

25. Artifact Trust

Artifact의 출처와 상태를 구분할 수 있다.

후보:

User-authored
Verified
Generated
External
Untrusted
Compromised
26. Artifact Integrity

Artifact가 변경되거나 변조되었는지 검증할 수 있어야 한다.

후보:

Hash
Checksum
Signature
Version
Git Commit
27. Artifact Verification

Artifact가 요구사항을 만족하는지 검증할 수 있어야 한다.

예:

Source Code
 → Tests

Document
 → Schema / Review

Dataset
 → Validation

Build
 → Build Verification
28. Artifact as Evidence

Artifact는 Verification Evidence가 될 수 있다.

Task
 ↓
Artifact
 ↓
Verification
 ↓
Evidence
 ↓
Evaluation

모든 Artifact가 Evidence라는 뜻은 아니다.

29. Artifact Manifest

Task / Project 단위로 Artifact를 관리하기 위한 Manifest를 둘 수 있다.

후보:

Artifact Manifest
├── Artifact ID
├── Type
├── Version
├── Status
├── Owner
├── Hash
├── Provenance
└── Verification
30. Artifact Context Projection

대형 Artifact를 Context에 직접 넣지 않는다.

Artifact
 ↓
Metadata / Relevant Section / Summary
 ↓
Context

필요한 경우 Reference를 제공한다.

31. Artifact Reference

Agent 간 Artifact 전달은 가능한 경우 Reference 중심으로 한다.

예:

Artifact ID
URI / Path
Version
Hash

전체 내용을 무조건 복사하지 않는다.

32. Progressive Disclosure

Agent가 Artifact를 사용할 때:

Metadata
 ↓
Relevant Section
 ↓
Full Artifact

순으로 필요한 만큼 접근하는 방식을 검토한다.

33. Artifact and Multi-Agent

여러 Agent가 하나의 Artifact를 공유할 수 있다.

Agent A
   ↘
    Artifact
   ↗
Agent B

이 경우 Versioning / Conflict Resolution이 필요하다.

34. Concurrent Mutation

동시에 Artifact가 수정될 경우:

Agent A → Version 2
Agent B → Version 2'

와 같은 Conflict가 발생할 수 있다.

후보:

Lock
Branch
Merge
Serial Execution
Conflict Resolution

초기 구현에서 어떤 방식을 사용할지는 PoC에서 검증한다.

35. Artifact Branching

Git-like branching을 Artifact에도 적용할 수 있는지 검토한다.

Artifact v1
 ├── Agent A Branch
 └── Agent B Branch

이후:

Merge
 ↓
Verified Artifact

방식을 사용할 수 있다.

36. Artifact Collaboration

Artifact는 Multi-Agent의 shared work object가 될 수 있다.

Task
 ↓
Shared Artifact
 ↓
Agent A
Agent B
Agent C

Blackboard Architecture와 연결되는 historical principle을 참고한다.

37. Artifact Events

Artifact lifecycle 변화는 Event로 기록할 수 있다.

ArtifactCreated
ArtifactUpdated
ArtifactValidated
ArtifactPublished
ArtifactArchived
ArtifactDeleted

Event Log와 Observability에 연결될 수 있다.

38. Artifact Observability

Trace에서:

Artifact ID
Version
Mutation
Agent
Task
Capability

를 추적할 수 있도록 한다.

39. Artifact Evaluation

Artifact 자체와 생성 과정을 모두 평가할 수 있다.

Artifact
 ↓
Evaluation

평가 후보:

Correctness
Completeness
Consistency
Validity
Integrity
Reproducibility
Usability
40. Artifact Reproducibility

가능한 경우 Artifact 생성 과정을 재현할 수 있어야 한다.

후보 정보:

Source
Code
Model
Instructions
Environment
Dependencies
Parameters
Tools
41. Artifact Checkpoint

Long-running Task에서는 Artifact가 Checkpoint 역할을 할 수 있다.

Task
 ↓
Artifact Snapshot
 ↓
Runtime Failure
 ↓
Resume
42. Artifact Recovery

Runtime이 실패해도 이미 저장된 Durable Artifact는 보존되어야 한다.

Runtime Crash
 ↓
Artifact persists
 ↓
Task resumes
43. Artifact Retention

Retention을 결정하는 요소:

Task relevance
Importance
Ownership
Evidence value
User preference
Policy
Storage cost
44. Artifact Cleanup

Temporary Artifact는 Garbage Collection 대상이 될 수 있다.

Temporary
 ↓
Unused
 ↓
Garbage Collection

Evidence나 Recovery에 필요한 Artifact는 삭제하지 않는다.

45. Artifact Immutability

일부 Artifact는 Immutable하게 관리할 수 있다.

예:

Audit Evidence
Published Artifact
Final Build
Signed Release

Immutable Artifact는 수정 대신 새로운 Version을 생성한다.

46. Artifact Taxonomy

초기 Artifact Type:

Source
Document
Data
Media
Build
Evaluation
Configuration
Model
Evidence

Artifact Type과 File Type을 구분한다.

47. Artifact Relationships

Artifact 간 관계:

Derived From
Depends On
Generated By
Verified By
Supersedes
References
Attached To
48. Artifact Lineage

Lineage를 활용하여:

Source
 ↓
Artifact A
 ↓
Transformation
 ↓
Artifact B
 ↓
Artifact C

를 추적할 수 있다.

49. Artifact Graph

관계가 복잡해지면 Artifact Graph를 사용할 수 있다.

다만 초기에는 별도 Graph 시스템을 도입하지 않는다.

50. Artifact and Knowledge Graph

Artifact에서 추출된 Knowledge와 Artifact를 연결할 수 있다.

Artifact
 ↓
Contains
 ↓
Knowledge
51. Artifact and Memory Graph

Artifact를 만든 Experience와 연결할 수 있다.

Experience
 ↓
Created
 ↓
Artifact
52. Artifact and Identity

일부 Artifact는 NOAH의 중요한 역사적 산출물이 될 수 있다.

예:

Architecture Decision
Major Research
Major Project Milestone

이러한 Artifact는 Identity-relevant Memory의 근거로 활용될 수 있다.

53. Artifact Ownership

Ownership과 Permission은 분리한다.

예:

User-owned
NOAH-generated
Project-owned
Shared
External
54. Artifact Sharing

Artifact의 공유 범위:

Private
User
Project
Agent
Public
External
55. Artifact Publishing

외부 Publish는 Side Effect이므로:

Artifact
 ↓
Review
 ↓
Permission / Approval
 ↓
Publish

를 적용할 수 있다.

56. Artifact Deletion

삭제는 보안 및 데이터 손실 위험이 있기 때문에:

Request
 ↓
Policy
 ↓
Approval if required
 ↓
Delete
 ↓
Audit

흐름을 따른다.

57. Artifact Backup

중요 Artifact는:

Version
Backup
Recovery
Restore Validation

을 고려한다.

58. Artifact Storage Migration

Storage Backend가 변경되어도 Artifact Identity는 유지되어야 한다.

Filesystem
 ↓
Object Storage

로 바뀌어도 Artifact ID와 Version semantics는 유지한다.

59. Artifact Federation

미래에는 Artifact가:

Local
NAS
Cloud
GitHub
External Service

등에 분산될 수 있다.

Artifact Contract가 이를 추상화할 수 있도록 한다.

60. Consequences
Positive
Artifact semantics 명확
File / Workspace와 분리
Versioning
Provenance
Lineage
Verification
Multi-Agent collaboration
Storage independence
Negative
Metadata 증가
Versioning complexity
Storage overhead
Concurrency handling
Lineage 관리 비용
Artifact lifecycle 관리 필요
61. Alternatives Considered
Alternative A — Artifact = File

Rejected.

Semantic information과 lifecycle을 표현하기 어렵다.

Alternative B — Artifact = Tool Result

Rejected.

Artifact가 Tool 실행보다 오래 지속될 수 있다.

Alternative C — 모든 Artifact를 Git으로 관리

Deferred.

모든 Artifact Type이 Git에 적합하지 않다.

Alternative D — Artifact를 별도 Microservice로 구현

Deferred.

초기에는 과도한 Physical Distribution이 될 수 있다.

62. Relationship to Previous Decisions
DDR-001
Task State / Runtime Boundary

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

와 직접 연결된다.

또한:

DDR-005
Identity Persistence

DDR-006
Orchestration Contract

와 연결된다.

63. Implementation Implications

향후 구현에서:

Artifact
ArtifactStore
ArtifactReference
ArtifactVersion
ArtifactMetadata
ArtifactProvenance

등의 Logical Boundary를 고려한다.

구체적인 Storage는 구현 단계에서 결정한다.

64. Validation Plan

최소 PoC:

1. Artifact 생성
2. Artifact 수정
3. Version 생성
4. Task와 연결
5. Verification
6. Evidence로 사용
7. Memory / Knowledge와 연결
8. Runtime 종료
9. Artifact 유지
10. Artifact 복원

Multi-Agent PoC에서는:

Agent A
→ Artifact v2

Agent B
→ Artifact v3

충돌을 검증한다.

65. Acceptance Criteria
☐ Artifact가 File과 독립적인 semantic identity를 가진다.
☐ Artifact Versioning이 가능하다.
☐ Task와 Artifact를 Reference로 연결할 수 있다.
☐ Artifact Provenance를 추적할 수 있다.
☐ Artifact Verification이 가능하다.
☐ Artifact를 Evidence로 사용할 수 있다.
☐ Runtime 종료 후 Durable Artifact가 유지된다.
☐ Artifact Storage backend를 교체할 수 있다.
☐ Multi-Agent Artifact conflict를 감지할 수 있다.
☐ Permission / Security를 적용할 수 있다.
66. Decision Status
Status: Accepted
Confidence: Medium

PoC 결과에 따라 수정할 수 있다.

67. Review Conditions

다음 상황에서 이 DDR을 재검토한다.

Artifact 규모가 크게 증가
Multi-Agent collaboration 증가
Artifact Graph 필요성 증가
Distributed Storage 도입
새로운 Artifact type 등장
Reproducibility 요구 증가
Storage cost 증가
68. Final Decision

Project NOAH는 Artifact를 단순 File이나 Tool Result가 아닌 semantic work object로 정의한다.

Artifact는 stable identity, version, provenance, lifecycle, ownership 및 scope를 가질 수 있다.

Artifact는 Task State와 분리되며, Task State는 Artifact Reference를 보유한다.

Artifact는 Memory와 Knowledge의 source가 될 수 있고 Verification Evidence로 사용될 수 있다.

Artifact의 physical storage는 교체 가능하며, 초기에는 Artifact를 별도의 Physical Service로 분리하지 않는다.

이를 통해 NOAH는 장기 Task에서 실제 작업 결과물을 추적하고 검증하며 복구할 수 있는 기반을 갖는다.