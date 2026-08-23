# Artifact Architecture Research

> Project NOAH Research
> Research 대상: Artifact Architecture
> Research Version: 0.1
> Priority: P1
> Status: Research

---

# 1. Research Purpose

Project NOAH가 생성·변경·사용하는 파일, 코드, 데이터, 보고서, 테스트 결과 및 기타 산출물을 하나의 지속 가능한 개념으로 관리하기 위한 Artifact Architecture를 연구한다.

핵심 질문:

> "NOAH가 만들어내거나 사용하는 결과물을 시스템에서 무엇으로 취급할 것인가?"

본 문서는 최종 Architecture를 결정하지 않는다.

---

# 2. Why This Research Matters

현재 Architecture Integration Review에서 Artifact가:

- Task
- Workspace
- State
- Memory
- Knowledge
- Verification
- Evidence
- Recovery

와 반복적으로 연결되고 있다.

따라서 Artifact를 단순 파일이나 Tool Output으로 취급하는 것이 적절한지 검토한다.

---

# 3. Current NOAH Hypothesis

현재 가설:

> Artifact는 Agent가 생성·수정·관찰·검증하는 지속적인 결과물 또는 작업 대상이다.

Artifact는 반드시 파일일 필요는 없다.

후보:

```text
Artifact
├── File
├── Directory
├── Code
├── Document
├── Image
├── Audio
├── Video
├── Dataset
├── Database Record
├── Report
├── Test Result
├── Build Result
├── Configuration
└── External Resource

이 가설을 연구를 통해 검증한다.

4. Artifact vs File

File은 Artifact의 한 구현 형태일 수 있다.

File
→ storage representation

Artifact
→ semantic work object

예:

README.md

는 파일이지만:

Project README Artifact

는 Task의 결과물로 관리될 수 있다.

5. Artifact vs Workspace

Workspace는 작업 환경이다.

Artifact는 Workspace 안에서 생성되거나 수정되는 지속적인 대상이다.

Workspace
├── Artifacts
├── Temporary Files
├── Processes
└── Environment State

따라서:

Workspace ≠ Artifact

를 검토한다.

6. Artifact vs Task

Task는 목표다.

Artifact는 목표를 수행하면서 생성되거나 변경되는 결과물이다.

Task
 ↓
Artifact

예:

Task:
"Architecture 문서 작성"

Artifact:
Architecture-Integration-Review-v0.2.md

하나의 Task가 여러 Artifact를 생성할 수 있다.

7. Artifact vs State

Artifact는 State와 다르다.

State
= 현재 시스템의 상태

Artifact
= 지속적으로 존재하는 작업 결과물

예:

State:
Task = Running

Artifact:
architecture.md

하지만 Artifact의 metadata 일부는 State에 포함될 수 있다.

8. Artifact vs Memory

Artifact:

실제 결과물

Memory:

결과물과 관련하여 미래에 사용할 수 있는 경험 또는 정보

예:

Artifact:
Architecture-Review.md

Memory:
"이 구조를 선택한 이유는 Runtime과 Task State를 분리하기 위해서였다."

Artifact와 Memory의 연결 관계를 연구한다.

9. Artifact vs Knowledge

Artifact는 Knowledge의 source가 될 수 있다.

Artifact
 ↓
Extraction
 ↓
Knowledge Candidate

예:

Research Paper
→ Artifact

Facts extracted from paper
→ Knowledge
10. Artifact vs Evidence

Artifact가 Verification Evidence가 될 수 있다.

Task
 ↓
Artifact
 ↓
Verification
 ↓
Evidence

그러나 모든 Artifact가 Evidence는 아니다.

11. Artifact Identity

Artifact에는 stable identity가 필요할 가능성이 높다.

후보:

Artifact ID
Name
Type
Version
Owner
Created At
Updated At
Location

파일 경로만으로 Artifact Identity를 표현하기에 충분한지 검토한다.

12. Artifact Versioning

Artifact는 수정될 수 있다.

Artifact
 ↓
Version 1
 ↓
Version 2
 ↓
Version 3

Version history가 필요한지 검토한다.

13. Artifact Lineage

Artifact가 어디에서 만들어졌는지 추적할 수 있어야 한다.

Source
 ↓
Artifact A
 ↓
Transformation
 ↓
Artifact B

예:

Source Dataset
→ Processing Script
→ Processed Dataset
→ Evaluation Report

이를 Artifact Lineage로 검토한다.

14. Artifact Provenance

Artifact의 provenance:

Source
Author
Agent
Task
Tool
Timestamp
Environment
Version
Transformation

등을 포함할 수 있다.

15. Artifact Ownership

Artifact의 소유권:

User
Project
Task
Agent
System
External

을 구분할 필요가 있다.

특히 Personal AI에서는 User-owned Artifact와 System-generated Artifact를 구분하는 것이 중요할 수 있다.

16. Artifact Scope

후보:

Global
User
Project
Session
Task
Agent
Temporary

Memory / Knowledge Scope와 유사하지만 동일한 규칙을 사용할 필요는 없다.

17. Artifact Lifecycle

후보:

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

Task에 따라 lifecycle이 달라질 수 있다.

18. Temporary vs Durable Artifact

모든 Artifact를 영구 저장할 필요는 없다.

Temporary
→ intermediate output

Durable
→ final report / source code / project document

Retention policy를 검토한다.

19. Artifact Retention

Retention 기준:

Task relevance
Importance
User ownership
Legal / policy requirements
Evidence value
Storage cost

등을 고려한다.

20. Artifact Storage

Artifact는:

Filesystem
Object Storage
Database
Git Repository
Document Store
External Service

등에 저장될 수 있다.

Logical Artifact와 Physical Storage를 분리한다.

21. Git-backed Artifacts

Code와 Documentation은 Git repository 자체가 Artifact Storage가 될 수 있다.

Artifact
 ↓
Git
 ↓
Version
 ↓
Commit

Git history가 Artifact Lineage를 제공할 수 있는지 검토한다.

22. Artifact and Git

Git Object:

version-control primitive

Artifact:

semantic work object

둘을 동일하게 취급하지 않는다.

23. Artifact and Workspace

Workspace에서:

Read
Create
Modify
Move
Delete

가 일어나면서 Artifact 상태가 변할 수 있다.

따라서 Workspace Action과 Artifact Mutation 사이의 경계를 연구한다.

24. Artifact Mutation

Artifact 변경도:

Proposal
 ↓
Permission
 ↓
Execution
 ↓
Verification
 ↓
Commit

의 구조를 가질 수 있다.

25. Artifact Verification

Artifact 자체가 요구사항을 만족하는지 검증할 수 있어야 한다.

예:

Code
→ Tests

Document
→ Schema / Review

Dataset
→ Validation

Build
→ Build Verification
26. Artifact Evidence

Verification에서 Artifact를 증거로 사용할 수 있다.

Artifact
 ↓
Evidence Reference
 ↓
Evaluation

원본 Artifact와 Evidence Reference를 구분한다.

27. Artifact and Task State

Task State에는 Artifact Reference를 저장할 수 있다.

Task State
├── Goal
├── Progress
├── Artifacts
└── Verification

Artifact 전체 내용을 Task State에 복사하지 않는다.

28. Artifact and Context

Context에 Artifact 전체를 넣지 않는다.

Artifact
 ↓
Relevant Projection
 ↓
Context

또는:

Artifact
 ↓
Tool
 ↓
Observation
 ↓
Context

를 사용한다.

29. Artifact References

큰 Artifact는 Reference로 전달한다.

예:

Artifact ID
URI
Path
Version
Checksum

등을 사용한다.

30. Artifact and Memory

Memory가 Artifact의:

생성 이유
중요한 변경
사용 경험
실패 경험

등을 기억할 수 있다.

Artifact
 ↕
Memory
31. Artifact and Knowledge

Artifact에서 Knowledge를 추출할 수 있다.

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
32. Artifact and Capability

Capability는 Artifact를 읽고 변경한다.

Capability
 ↓
Artifact

예:

read_file
write_file
git_commit
generate_report
33. Artifact Permissions

Artifact마다 Access Policy가 필요할 수 있다.

Read
Write
Delete
Share
Publish
Execute

와 같은 Permission을 검토한다.

34. Artifact Security

Artifact에는:

secrets
credentials
personal data
malicious content
executable code

등이 포함될 수 있다.

따라서 Artifact 자체도 Security Boundary가 될 수 있다.

35. Artifact Trust

Artifact의 신뢰 수준:

User-authored
Verified
Generated
External
Untrusted

등을 검토한다.

36. Artifact Integrity

Artifact가 변조되지 않았는지 확인할 수 있어야 한다.

후보:

Checksum
Hash
Signature
Version
Git Commit
37. Artifact Lineage Graph

복잡한 프로젝트에서는:

Input
 ↓
Artifact A
 ↓
Transformation
 ↓
Artifact B
 ↓
Artifact C

같은 graph를 추적할 수 있다.

이는 Reproducibility와 Evaluation에 유용하다.

38. Artifact Reproducibility

Artifact 생성 과정을 다시 실행할 수 있는지 검토한다.

필요 정보:

Source
Code
Model
Prompt / Instruction
Environment
Dependencies
Parameters
Tools
39. Artifact Checkpoint

Long-running Task에서는 중간 Artifact가 checkpoint 역할을 할 수 있다.

Task
 ↓
Artifact Snapshot
 ↓
Runtime Failure
 ↓
Resume
40. Artifact Recovery

Runtime이 실패해도 이미 저장된 Artifact는 보존되어야 한다.

Runtime Crash
 ↓
Artifact persists
 ↓
Task resumes
41. Artifact Cleanup

Temporary Artifact는 계속 쌓일 수 있다.

후보 lifecycle:

Temporary
 ↓
Unused
 ↓
Garbage Collection

단, Evidence나 Recovery에 필요한 Artifact는 삭제하지 않는다.

42. Artifact and Multi-Agent

여러 Agent가 하나의 Artifact를 사용할 수 있다.

Agent A
   ↘
    Artifact
   ↗
Agent B

이 경우:

locking
versioning
conflict detection
merge

가 필요할 수 있다.

43. Concurrent Mutation

두 Agent가 동시에 Artifact를 수정하면:

Agent A
→ Version 2

Agent B
→ Version 2'

같은 conflict가 발생한다.

해결 후보:

Lock
Branch
Merge
Conflict Resolution
Serial Execution
44. Artifact Branching

Git-like branching을 Artifact에도 적용할 수 있는지 검토한다.

Artifact v1
 ├── Agent A Branch
 └── Agent B Branch

이후:

Merge
 ↓
Verified Artifact
45. Artifact Collaboration

Artifact를 Multi-Agent collaboration의 공통 작업 공간으로 사용할 수 있다.

Task
 ↓
Shared Artifact
 ↓
Agent A
Agent B
Agent C

Blackboard architecture와 연결되는 역사적 아이디어로 볼 수 있다.

46. Artifact as Shared State

Artifact가 Agent 간 communication channel이 될 수 있다.

하지만 Artifact 전체를 공유하는 것과 Artifact Reference를 공유하는 것은 구분한다.

47. Artifact and Event

Artifact 변경은 Event를 생성할 수 있다.

ArtifactCreated
ArtifactUpdated
ArtifactDeleted
ArtifactPublished
ArtifactValidated
48. Artifact and Observability

Trace에서:

Artifact ID
Version
Mutation
Source

를 기록할 수 있다.

49. Artifact and Evaluation

Evaluation은 Artifact를 직접 평가할 수 있다.

Artifact
 ↓
Evaluation
 ↓
Pass / Fail

또한 Artifact 생성 과정도 평가할 수 있다.

50. Artifact Quality

평가 후보:

Correctness
Completeness
Consistency
Validity
Integrity
Reproducibility
Usability
51. Artifact and Learning

Artifact를 통해 경험을 얻을 수 있다.

Artifact
 ↓
Evaluation
 ↓
Experience
 ↓
Memory
 ↓
Learning
52. Artifact and Identity

어떤 Artifact가 NOAH의 중요한 역사적 산출물일 수 있다.

예:

Major Architecture Decision
Major Research
Major Project Milestone

이런 Artifact는 Identity-relevant memory의 근거가 될 수 있다.

53. Artifact and User Ownership

User가 만든 Artifact와 NOAH가 생성한 Artifact의 Ownership을 구분한다.

User-owned
NOAH-generated
Shared
External
54. Artifact Sharing

Artifact를:

Private
Project
Specific Agent
User
Public

으로 공유 범위를 설정할 수 있다.

55. Artifact Publishing

Artifact를 외부에 Publish하는 행위는 높은 Risk를 가질 수 있다.

Artifact
 ↓
Review
 ↓
Approval
 ↓
Publish

Permission & Security Architecture와 연결된다.

56. Artifact as Evidence

고위험 Task에서는 Artifact를 evidence package에 포함할 수 있다.

Task
 ↓
Artifact
 ↓
Verification
 ↓
Evidence
 ↓
Evaluation
57. Artifact Manifest

Task 단위로 Artifact를 관리하기 위해 Manifest를 둘 수 있다.

Artifact Manifest
├── Artifact ID
├── Version
├── Type
├── Status
├── Owner
├── Hash
├── Provenance
└── Verification
58. Artifact Metadata

Metadata는 Artifact 본문과 분리한다.

Artifact
+
Metadata

이는 대용량 Artifact 관리에서 중요할 수 있다.

59. Large Artifacts

대형 Artifact:

video
dataset
model
binary

를 Context나 Task State에 직접 포함하지 않는다.

Reference만 전달한다.

60. Artifact Storage Abstraction

현재:

Artifact Store

라는 논리적 Interface를 검토한다.

구현:

Filesystem
Git
Object Storage
Database
External Storage

교체 가능하게 한다.

61. Artifact Lifecycle

통합 후보:

Create
 ↓
Track
 ↓
Modify
 ↓
Validate
 ↓
Use
 ↓
Publish
 ↓
Archive
 ↓
Delete
62. Artifact Retention Policy

Retention 결정에:

Importance
Ownership
Evidence
Task Status
Cost
User Preference
Policy

를 사용한다.

63. Artifact Deletion

삭제는:

Requested
 ↓
Policy
 ↓
Approval
 ↓
Delete
 ↓
Audit

과정을 거칠 수 있다.

64. Artifact Version Recovery

잘못된 변경이 발생하면:

Artifact v3
 ↓
Detect failure
 ↓
Restore v2

를 지원할 수 있다.

65. Artifact Immutability

일부 Artifact는 immutable하게 둘 가치가 있다.

예:

Evidence
Audit Log
Final Build
Published Artifact

이들은 append-only / immutable storage가 적합할 수 있다.

66. Mutable vs Immutable Artifact
Mutable
→ source code
→ working document

Immutable
→ signed release
→ evaluation evidence
→ audit record

Artifact type에 따라 정책을 다르게 적용한다.

67. Artifact Taxonomy

초기 후보:

Artifact
├── Source
├── Document
├── Data
├── Media
├── Build
├── Evaluation
├── Configuration
├── Model
└── Evidence
68. Artifact Type vs File Type

예:

Markdown

은 File Type.

Architecture Decision

은 Artifact Type.

둘을 분리한다.

69. Artifact Semantic Type

Artifact는 domain semantics를 가질 수 있다.

예:

Architecture Document
Research Report
Decision Record
Source Code
Test Report
Dataset
Release

이는 Evaluation과 Workflow를 쉽게 만들 수 있다.

70. Artifact Discovery

Agent가 필요한 Artifact를 찾을 수 있어야 한다.

Task
 ↓
Artifact Search
 ↓
Relevant Artifact
 ↓
Context
71. Artifact Index

후보:

Artifact Index
├── Metadata
├── Semantic Index
├── Relationship Index
└── Version Index
72. Artifact Relationship

Artifact 사이에는 관계가 존재할 수 있다.

Derived From
Depends On
Generated By
Verified By
Supersedes
References
Attached To
73. Artifact Graph

관계를 Graph로 표현할 수 있다.

Source
 ↓
Code
 ↓
Build
 ↓
Test
 ↓
Release

이 구조는 Lineage와 Reproducibility에 활용할 수 있다.

74. Artifact and Knowledge Graph

Artifact Graph와 Knowledge Graph를 결합할 필요가 있는지 검토한다.

예:

Artifact
 ↓
Contains
 ↓
Knowledge
75. Artifact and Memory Graph

Artifact와 Experience 관계:

Experience
 ↓
Created
 ↓
Artifact

를 Graph로 연결할 수 있다.

76. Artifact and Context Engineering

큰 Artifact는:

Artifact
 ↓
Chunk / Summary / Metadata
 ↓
Context Selection

으로 제공할 수 있다.

77. Progressive Disclosure

Agent에게:

Artifact metadata
Relevant section
Full artifact

순으로 필요한 만큼 제공하는 방식을 검토한다.

78. Artifact Security

실행 가능한 Artifact:

Code
Binary
Script
Model

는 일반 Document보다 높은 위험을 가질 수 있다.

따라서:

Artifact
 ↓
Risk Classification
 ↓
Policy
 ↓
Sandbox

를 고려한다.

79. Artifact Integrity

Artifact가 변경되었을 때:

Hash
Signature
Version
Origin

을 검증할 수 있다.

80. Artifact Trust

후보:

Trusted
Verified
Generated
External
Untrusted
Compromised

를 사용한다.

81. Artifact Provenance Chain

예:

User Input
 ↓
Agent
 ↓
Tool
 ↓
Artifact
 ↓
Verification

모든 단계가 Trace와 연결될 수 있다.

82. Artifact Audit

고위험 Artifact에 대해서:

Created By
Modified By
Approved By
Published By
Deleted By

를 추적할 수 있다.

83. Artifact Cost

대형 Artifact는:

Storage
Bandwidth
Compute
Indexing
Backup

비용을 발생시킨다.

84. Artifact Backup

중요 Artifact에는:

Version
Backup
Recovery
Restore Test

를 적용할 수 있다.

85. Artifact Replication

필요한 경우 여러 Storage에 복제할 수 있다.

하지만 초기 단계에서는 과도한 분산을 피한다.

86. Artifact Federation

미래에 Artifact가:

Local
NAS
Cloud
GitHub
External Service

에 분산될 수 있다.

Artifact abstraction이 이를 숨길 수 있어야 한다.

87. Historical / Foundational Ideas

오래된 개념에서 참고할 수 있는 것:

File Systems

Persistent named objects

Databases

Transactions / versioning

Git

Versioned immutable history

Build Systems

Artifact dependency graph

Data Lineage

Transformation provenance

Blackboard Architecture

Shared artifacts / workspace

Distributed Systems

Durable object / replication

88. Current Frontier

현재 연구 방향:

Agent-generated artifacts
Artifact-centric workflows
Context repositories
Git-backed Agent workspaces
Long-running coding agents
Artifact lineage
Executable artifacts
Sandboxed artifacts
Artifact evaluation
89. Emerging Possibilities

미래에는 Artifact가 단순 결과물이 아니라:

Artifact
→ State
→ Interface
→ Memory Source
→ Knowledge Source
→ Collaboration Object

로 확장될 가능성을 검토한다.

90. Candidate Artifact Architecture
                        ARTIFACT SYSTEM
                              │
                       Artifact Registry
                              │
               ┌──────────────┼──────────────┐
               │              │              │
            Metadata       Storage        Lineage
               │              │              │
               └──────────────┼──────────────┘
                              │
                         Artifact
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       Workspace           Memory             Knowledge
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                         Verification
                              │
                         Evaluation
                              │
                            Audit
91. Candidate Artifact Contract
Artifact
├── ID
├── Type
├── Version
├── Metadata
├── Owner
├── Scope
├── Location
├── Provenance
├── Integrity
├── Permissions
├── Dependencies
├── Verification
└── Lifecycle
92. Stable vs Replaceable
Stable
Artifact ID
Artifact Type
Version
Provenance
Lifecycle
Access Contract
Integrity
Lineage
Replaceable
Filesystem
Git
Object Storage
Database
Index
Cloud Provider
93. Risks
Artifact Explosion

너무 많은 중간 결과물이 생성될 수 있다.

Storage Growth

장기간 누적될 수 있다.

Stale Artifacts

오래된 결과가 최신 상태로 오인될 수 있다.

Conflicting Versions

여러 Agent가 동시에 수정할 수 있다.

Security

악성 Artifact가 실행될 수 있다.

Privacy

개인정보가 포함될 수 있다.

Lineage Complexity

변환 관계가 매우 복잡해질 수 있다.

94. Open Questions
Artifact의 최소 단위는 무엇인가?
모든 파일을 Artifact로 취급해야 하는가?
Artifact Registry가 필요한 규모는 언제인가?
Artifact ID는 Path와 어떻게 다른가?
Artifact의 canonical source는 무엇인가?
Versioning은 Git으로 충분한가?
Artifact Lineage는 어디까지 추적해야 하는가?
Temporary Artifact를 언제 삭제하는가?
어떤 Artifact는 immutable해야 하는가?
Artifact와 Task State의 관계는?
Artifact와 Memory의 관계는?
Artifact와 Knowledge의 관계는?
Artifact가 Shared State가 될 수 있는가?
Multi-Agent의 동시 수정은 어떻게 해결하는가?
Artifact에 어떤 Security classification이 필요한가?
Artifact를 Context에 어떻게 projection하는가?
Artifact Store는 언제 별도 subsystem이 필요한가?
Artifact Graph가 필요한가?
Artifact가 Evidence Package의 canonical source가 될 수 있는가?
Artifact lifecycle과 Task lifecycle을 어떻게 연결하는가?
95. Research Findings

Reference별:

Reference
Artifact Model
Storage
Versioning
Lineage
Security
Evaluation
NOAH Relevance
Stable Principle

을 기록한다.

96. Historical / Current / Emerging Comparison
Category	Example	Key Principle
Historical	File systems	Persistent objects
Historical	Git	Versioned history
Historical	Build systems	Artifact dependency
Current	Agent workspaces	Persistent work product
Current	Context repositories	Human-readable artifacts
Emerging	Agent-generated artifact systems	Artifact-centric execution
97. Preliminary Recommendation

현재 가설:

Artifact는 File과 구분되는 semantic work object이며, 실제 Storage와 독립적인 Artifact Contract를 가져야 한다.

즉:

Artifact
 ↓
Artifact Store
 ↓
Physical Storage

를 검토한다.

98. Artifact and Long-Term Tasks

Long-running Task에서는 Artifact가 Task State를 보조하는 durable work product가 될 수 있다.

Task
 ↓
Artifact
 ↓
Checkpoint
 ↓
Recovery
99. Artifact and NOAH Development

NOAH 자신도 Artifact를 생성한다.

예:

Research
Review
DDR
Blueprint
Code
Tests
Reports

따라서 Artifact Architecture는 NOAH Runtime뿐 아니라 NOAH Development System에도 적용될 수 있다.

100. Future Resilience

Artifact backend가:

Git
Filesystem
Object Storage
Cloud
Distributed Storage
Future System

으로 바뀌어도 Artifact Contract를 유지한다.

101. Research Completion Criteria
☐ Artifact 정의
☐ File / Workspace와 경계 정의
☐ Task / State와 관계 정의
☐ Memory / Knowledge 관계 정의
☐ Lifecycle 정의
☐ Ownership / Scope 정의
☐ Versioning 정의
☐ Provenance / Lineage 정의
☐ Security 정의
☐ Storage abstraction 정의
☐ Multi-Agent concurrency 문제 확인
☐ Evaluation / Evidence 관계 정의
☐ 최소 Artifact Contract 후보 정의
102. Next Step
Artifact Architecture Research
        ↓
Findings
        ↓
Integration Review v0.3
        ↓
P1 Identity Persistence
        ↓
P1 Orchestration Contract
        ↓
DDR
        ↓
02-Architecture
103. Final Research Goal

이번 Research의 최종 목적:

"NOAH가 장기 작업을 수행하면서 만들어내는 실제 결과물을 지속적으로 추적하고, 검증하고, 복구하고, 다시 사용할 수 있는가?"

104. Final Principle

Artifact는 단순히 저장된 파일이 아니라, NOAH의 작업이 현실 세계에 남긴 지속적인 결과물이다.
