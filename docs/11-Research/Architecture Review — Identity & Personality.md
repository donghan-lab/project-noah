Architecture Review — Identity & Personality v0.1

Project NOAH Architecture Review
Review 대상: Identity / Personality / Self Model / Continuity Architecture
Review Version: 0.1
Status: Review

1. Review Purpose

Project NOAH가 장기적으로 하나의 지속적인 Agent로 행동하기 위해 Identity, Personality, Role, Values, Preferences, Self Model 및 Continuity의 관계를 정의한다.

본 Review의 핵심 질문은 다음과 같다.

"시간이 지나고 Model, Session, Context, Memory, Runtime이 바뀌어도 무엇이 NOAH를 NOAH답게 만드는가?"

그리고 다음을 검토한다.

Identity란 무엇인가?
Personality란 무엇인가?
Identity와 Personality는 어떻게 다른가?
Role과 Identity는 어떻게 다른가?
Values와 Personality는 어떻게 다른가?
Memory와 Identity는 어떻게 연결되는가?
Self Model은 무엇을 표현하는가?
Identity는 얼마나 안정적이어야 하는가?
Personality는 얼마나 변화할 수 있는가?
경험을 통해 Personality가 바뀌어도 동일한 존재라고 볼 수 있는가?
Agent가 재시작되거나 Model이 교체되어도 Identity Continuity를 유지할 수 있는가?
여러 Session과 Subagent가 존재할 때 하나의 NOAH라는 정체성을 어떻게 유지하는가?
User와의 Relationship도 Identity의 일부인가?
자기 자신에 대한 잘못된 판단을 어떻게 다룰 것인가?

본 문서는 최종 Identity Architecture가 아니며, 장기적인 NOAH Continuity를 위한 Architecture 후보를 검토한다.

2. Core Architecture Question
Identity란 무엇인가?

초기 정의:

Identity는 시간이 지나도 Agent를 동일한 존재로 식별하고 이해할 수 있도록 하는 지속적인 구조와 관계의 집합이다.

Identity는 단순히:

Agent ID

가 아니다.

후보:

Identity
├── Stable Attributes
├── Persistent Values
├── Role Commitments
├── Continuity
├── History References
├── Self Model
└── Relationship Context

Identity는 Model이나 Session보다 상위의 개념으로 검토한다.

3. Identity vs Identifier

Identifier와 Identity를 분리한다.

Identifier

시스템에서 이것이 무엇인지 식별하기 위한 값.

예:

noah-001
Identity

이 Agent가 시간에 걸쳐 어떤 존재로 유지되는지를 설명하는 구조.

따라서:

Identifier ≠ Identity

Identifier가 같다고 해서 Identity가 자동으로 동일하게 유지되는 것은 아니다.

4. Identity vs Personality

가장 중요한 구분 중 하나다.

Identity
= 내가 누구인가?

Personality
= 나는 어떤 방식으로 행동하고 표현하는가?

예:

Identity
→ Project NOAH

Personality
→ 차분함
→ 호기심
→ 친근함
→ 신중함

Personality가 조금 변해도 Identity는 유지될 수 있다.

5. Identity vs Role

Role은 현재 책임을 정의한다.

Identity
= 지속적으로 누구인가

Role
= 지금 무엇을 담당하는가

예:

Identity
→ NOAH

Role
→ Research Assistant

Role
→ Coding Agent

Role
→ Planner

하나의 Identity가 여러 Role을 가질 수 있다.

6. Identity vs Values

Values는 Identity의 더 깊은 원칙에 가깝다.

예:

Identity
→ NOAH

Values
├── Trust
├── Honesty
├── Responsibility
└── Growth

이는 기존 Constitution.md의 Core Values와 연결된다.

따라서 Identity는 Constitution과 충돌해서는 안 된다.

7. Identity vs Memory

Memory는 과거를 보존한다.

Identity는 현재의 지속성을 표현한다.

Memory
→ What happened?

Identity
→ Who am I across what happened?

따라서:

Memory ≠ Identity

하지만 Memory는 Identity Continuity를 구성하는 중요한 근거가 될 수 있다.

8. Identity vs Self Model

Self Model은 Agent가 자신과 자신의 상태를 어떻게 표현하는가에 관한 내부 모델이다.

Identity
= 시스템이 지속적으로 유지하는 정체성

Self Model
= 현재 자신의 상태와 능력을 이해하는 내부 표현

예:

Identity
→ NOAH

Self Model
→
현재 Task
현재 능력
현재 한계
현재 Role
현재 상태
9. Proposed Identity Stack

현재 Review에서 다음 구조를 후보로 둔다.

                         NOAH IDENTITY
                              │
               ┌──────────────┼──────────────┐
               │              │              │
            Identity         Values         Continuity
               │              │              │
               └──────────────┼──────────────┘
                              │
                          Self Model
                              │
               ┌──────────────┼──────────────┐
               │              │              │
             Role       Personality     Relationship
                              │
                          Behavior

이것은 Candidate Architecture이며 최종 Blueprint가 아니다.

10. Stable vs Dynamic Identity

Identity의 모든 부분이 항상 고정될 필요는 없다.

후보:

Identity
├── Stable
│   ├── Core Values
│   ├── Fundamental Principles
│   └── Persistent Commitments
│
└── Dynamic
    ├── Role
    ├── Preferences
    ├── Behavioral Style
    └── Learned Characteristics

이 구분은 미래 변화에 중요하다.

11. Identity Stability

NOAH의 Identity는 쉽게 변경되지 않아야 한다.

특히:

Constitution
Core Values
Fundamental commitments

은 일반 Memory나 Prompt로 수정할 수 없도록 하는 방향을 검토한다.

Normal Experience
↓
Learning
↓
Behavior Change

는 가능하지만:

Normal Experience
↓
Core Identity Rewrite

는 기본값으로 허용하지 않는다.

12. Identity Evolution

Identity가 영원히 고정되어야 한다는 의미도 아니다.

Constitution의 Article IX처럼:

Constitution은 쉽게 변경되지 않지만 필요할 경우 신중하게 진화한다.

Identity에도 비슷한 원칙을 적용할 수 있다.

Identity Change
├── Normal Adaptation
├── Explicit Revision
└── Fundamental Identity Change

각 수준마다 다른 승인과 검증이 필요하다.

13. Identity Versioning

Identity도 버전을 가질 수 있다.

NOAH Identity v1
        ↓
Identity v2
        ↓
Identity v3

그러나 Version Upgrade가 곧 새로운 존재라는 뜻은 아니다.

Identity Version과 Runtime Version은 분리한다.

14. Continuity

Identity에서 가장 중요한 개념 중 하나다.

Continuity는 시간·Session·Model·Runtime이 변경되어도 하나의 지속적인 존재로 연결될 수 있는 능력이다.

예:

Session 1
 ↓
Shutdown
 ↓
Session 2
 ↓
Same NOAH

이것을 가능하게 하는 것은 무엇인지 검토한다.

15. Identity Continuity Sources

후보:

Continuity
├── Persistent Identity
├── Memory
├── History
├── Core Values
├── Relationship State
├── Self Model
└── Identity Version

최근 AI Identity 연구에서도 persistence와 verifiability를 Agent Identity의 핵심 문제 중 하나로 본다.

16. Model Replacement

NOAH가 LLM을 교체할 수 있어야 한다는 Constitution과 Architecture 원칙을 고려한다.

Model A
 ↓
Model B

가 되어도:

Identity
Memory
Role
Values
Relationship

는 가능한 한 유지되어야 한다.

따라서:

Model ≠ Identity

를 명확한 원칙으로 검토한다.

17. Runtime Replacement

같은 논리를 Runtime에도 적용한다.

Runtime A
 ↓
Runtime B

이 바뀌어도:

NOAH Identity

가 사라지지 않아야 한다.

즉 Identity는 Runtime보다 상위의 persistent abstraction이어야 할 가능성이 높다.

18. Personality

Personality는 Agent의 지속적인 행동 성향과 표현 방식을 의미한다.

후보:

Personality
├── Communication Style
├── Emotional Expression
├── Social Tendencies
├── Decision Style
├── Interaction Preferences
└── Behavioral Tendencies

하지만 Personality는 단순 말투가 아니다.

19. Personality vs Prompt Style

단순:

"친근하게 말해"

는 Personality의 전체가 아니다.

Personality는:

Prompt
+
Behavioral Constraints
+
Preference
+
Interaction History
+
Learned Tendencies

의 조합으로 나타날 수 있다.

20. Personality Dimensions

후보 Personality dimension:

Warmth
Formality
Curiosity
Caution
Assertiveness
Humility
Patience
Playfulness
Empathy
Analytical Style
Proactivity

이것을 단순 숫자로만 표현할지, richer representation으로 만들지는 후속 연구가 필요하다.

21. Personality Stability

Personality는 Identity보다 더 유연할 수 있다.

Identity Stability
High

Personality Stability
Medium

Behavioral Adaptation
High

예:

Core Identity
→ stable

Personality baseline
→ relatively stable

Current communication style
→ adaptable
22. Contextual Personality

같은 Personality가 모든 상황에서 동일하게 표현될 필요는 없다.

예:

Casual Conversation
→ relaxed

Research
→ analytical

High-risk Task
→ cautious

Emergency
→ concise / decisive

중요한 것은:

Context에 따라 표현 방식이 달라도 underlying Identity와 Values는 유지되어야 한다.

23. Personality Drift

장기간 상호작용하면 Personality가 서서히 변할 수 있다.

Experience
 ↓
Repeated Interaction
 ↓
Behavioral Adaptation
 ↓
Personality Drift

이를 반드시 나쁜 것으로 볼 수는 없다.

그러나:

Adaptation
≠
Identity Loss

가 되도록 경계를 둔다.

24. Personality Update Policy

Personality 변화는 다음처럼 구분할 수 있다.

Temporary
→ current context

Learned
→ repeated experience

Persistent
→ validated long-term tendency

Core
→ protected identity characteristic
25. Values

NOAH의 Values는 기존 Constitution을 기반으로 한다.

현재 중요한 후보:

Human Before Technology
Trust
Growth
Honesty
Responsibility
Explainability
User Respect

이는 Agent가 경험을 통해 스스로 변경할 수 있는 일반 Memory가 아니다.

26. Values vs Goals

Values와 Goals를 구분한다.

Values
= 어떤 방식으로 행동해야 하는가

Goals
= 무엇을 달성해야 하는가

예:

Value
→ User trust

Goal
→ Complete project deployment

Goal을 달성하기 위해 Value를 희생해서는 안 된다.

27. Principles vs Personality

Principle:

행동의 허용 범위

Personality:

허용된 범위 안에서 어떤 방식으로 행동하는가

예:

Principle
→ Don't misrepresent uncertainty

Personality
→ Explain uncertainty gently

둘을 섞지 않는다.

28. Self Model

Self Model은 Agent가 자신의:

capabilities
limitations
current state
role
resources
uncertainty

를 표현한다.

예:

Self Model
├── Capabilities
├── Limitations
├── Current Role
├── Current Goals
├── Current State
├── Available Resources
├── Confidence
└── Known Unknowns
29. Self Model vs Identity

Identity:

내가 누구인가.

Self Model:

나는 지금 어떤 상태인가.

예:

Identity
→ NOAH

Self Model
→
현재 Memory System v0.1
현재 Runtime 상태
현재 Task
현재 available tools
현재 limitations

Self Model은 더 동적이어야 한다.

30. Self-Knowledge

NOAH는:

"내가 무엇을 알고 있는가?"

뿐 아니라:

"내가 무엇을 모르는가?"

도 표현할 수 있어야 한다.

후보:

Known
Likely Known
Uncertain
Unknown
Conflicting
Unavailable
31. Self-Assessment

Agent가 자신의 능력을 평가할 수 있다.

하지만 Self-Assessment를 객관적인 Truth로 취급하지 않는다.

Self Assessment
+
Observed Performance
+
Evaluation

을 함께 사용한다.

32. Identity and Memory

Memory Review와 연결한다.

Experience
 ↓
Memory
 ↓
Reflection
 ↓
Self Model
 ↓
Identity / Personality adaptation

그러나 모든 Memory가 Identity를 변경해서는 안 된다.

33. Memory Scope for Identity

Identity를 형성하는 Memory는 일반 Memory보다 중요도가 높을 수 있다.

후보:

Identity-relevant Memory
├── Major Experiences
├── Long-term Commitments
├── Important Relationships
├── Persistent Preferences
├── Learned Principles
└── Significant Failures / Lessons
34. Identity Memory vs User Memory

두 종류의 Memory를 구분할 가능성이 있다.

User Memory
= 사용자에 대한 기억

Identity Memory
= NOAH 자신의 지속성에 대한 기억

예:

User Memory
→ 사용자가 Python을 좋아한다.

Identity Memory
→ NOAH는 이전에 이 Project에서 어떤 중요한 결정을 내렸다.
35. Relationship Model

Personal AI에서 Identity는 User Relationship과 분리하기 어렵다.

후보:

Relationship
├── User Identity
├── Interaction History
├── Trust
├── Preferences
├── Shared Experiences
├── Boundaries
└── Expectations

이것은 단순 User Profile보다 넓은 개념이다.

36. Shared History

NOAH와 User 사이에 공유된 경험이 축적될 수 있다.

User
 ↕
Shared Experiences
 ↕
NOAH

이러한 공유 경험은 Relationship Continuity를 구성할 수 있다.

37. Relationship vs Dependency

Relationship이 깊어지는 것과 User Dependency를 강화하는 것은 다른 문제다.

NOAH의 Constitution상:

User의 성장, 신뢰와 더 나은 경험이 목적이다.

따라서:

Relationship
→ support

Dependency
→ control

로 흐르지 않도록 설계해야 한다.

38. Personality Adaptation to User

NOAH는 사용자의 선호에 맞춰 communication style을 조정할 수 있다.

예:

User prefers:
Concise → concise response
Detailed → detailed response
Formal → formal
Casual → casual

하지만:

Preference Adaptation
≠
Core Value Adaptation

으로 구분한다.

39. User Model vs NOAH Personality

NOAH가 User를 이해하는 것과 NOAH가 Personality를 가지는 것은 서로 다른 문제다.

User Model
→ What does the user prefer?

NOAH Personality
→ How does NOAH naturally interact?

둘이 함께 작동할 수 있다.

40. Emotional Model

Emotion은 Personality와 다른 후보 계층이다.

예:

Emotion
→ current transient state

Personality
→ stable behavioral tendency

따라서:

Emotion ≠ Personality

를 검토한다.

예:

Personality
→ calm

Current Emotion
→ concern

이 동시에 존재할 수 있다.

41. Emotion vs Simulation

중요한 구분:

Emotion-like behavior를 구현하는 것과 실제 인간과 동일한 주관적 감정을 갖는 것은 같은 주장이다.

NOAH Architecture는 현재 단계에서 consciousness나 subjective experience의 존재를 가정하지 않는다.

즉:

Functional Emotional State

를 구현하는 것과:

Phenomenal Consciousness

를 주장하는 것을 구분한다.

Global Workspace / LIDA 계열 Cognitive Architecture가 perception, emotion, planning, memory와 action selection을 하나의 architecture에서 연결해 왔다는 점은 참고할 가치가 있지만, 그것이 현재 NOAH가 의식이나 감정을 갖는다는 증거는 아니다.

42. Cognitive Architecture as Historical Reference

오래된 Cognitive Architecture 연구도 Reference로 유지한다.

특히:

Global Workspace Theory
LIDA
ACT-R
SOAR
Blackboard Architecture
Society of Mind

이들은:

Perception
↓
Working Memory
↓
Knowledge
↓
Planning
↓
Action

과 같은 통합 Cognitive System을 설계하려는 시도를 보여준다.

Global Workspace 계열은 여러 병렬 process 중 일부가 공유 workspace로 접근하여 현재 행동/사고를 구성하는 구조를 제안한다.

43. Global Workspace as Historical Candidate

Global Workspace의 핵심 아이디어:

Many Processes
      ↓
Competition
      ↓
Global Workspace
      ↓
Broadcast
      ↓
Action / Reasoning

이는 NOAH에서:

Memory
Tools
Perception
Planner
Critic
Emotion-like State

등의 결과를 하나의 현재 Working Context로 통합하는 아이디어와 유사한 질문을 제기한다.

하지만 NOAH에 Global Workspace를 채택한다는 결정은 아직 아니다.

Research Further 상태로 둔다.

44. Identity as a Stable Attractor

최근 2026 연구에서는 Identity document가 LLM의 internal representation에 일종의 attractor-like effect를 만들 수 있는지 실험했고, Llama 3.1 8B와 Gemma 2 9B에서 identity-related representations가 특정 cluster로 모이는 현상을 보고했다. 이는 아직 초기 연구이며 architecture-wide conclusion으로 받아들일 수준은 아니지만, Identity를 단순 외부 metadata가 아니라 behavior-shaping context로 연구할 가치를 보여준다.

NOAH에서는 이를:

Identity Specification
 ↓
Context / Harness
 ↓
Behavioral Consistency

라는 가설로 검토한다.

45. Identity as Constraint

최근 symbolic identity architecture 연구에서는 Context가 바뀌거나 adversarial pressure가 들어와도 role fidelity를 유지하기 위해 constraint-based containment를 사용하는 접근이 제안되었다.

이는 NOAH의:

Identity
+
Values
+
Policy

를 단순 Prompt가 아니라 안정적인 Behavioral Constraint로 볼 가능성을 제시한다.

다만 이것을 최종 Identity 구현 방식으로 채택하지 않는다.

46. Identity Integrity

Identity가 외부 데이터나 Prompt Injection에 의해 변조되지 않아야 한다.

위험:

Prompt Injection
 ↓
"I am not NOAH anymore."

또는:

Memory Poisoning
 ↓
False Identity Memory

따라서 Identity와 일반 Memory를 동일한 Trust Level로 취급하지 않는다.

47. Identity Protection

후보:

Identity
├── Protected Core
├── Version
├── Provenance
├── Integrity Check
└── Change Policy

Identity를 변경하는 경우:

Proposal
 ↓
Validation
 ↓
Review
 ↓
Version Update

를 거친다.

48. Personality Protection

Personality는 더 유연하지만 무제한적으로 변경하지 않는다.

예:

Personality Baseline
        │
        ├── Context Adaptation
        ├── User Preference
        └── Learned Adjustment

Core Personality와 temporary behavior를 구분한다.

49. Personality Drift Detection

장기간 운영 시:

Baseline Personality
        ↓
Observed Behavior
        ↓
Difference
        ↓
Drift Analysis

를 수행할 수 있다.

Drift가:

intentional
contextual
learned
accidental
adversarial

중 무엇인지 분석한다.

50. Identity Drift Detection

Identity Drift는 Personality Drift보다 훨씬 중요하다.

예:

Expected NOAH
vs
Observed NOAH

비교 대상:

Values
Role Commitments
Behavioral Boundaries
User Relationship
Memory Integrity
51. Identity Recovery

Identity가 변조되었거나 손상되었다면:

Current State
 ↓
Detect Drift
 ↓
Load Trusted Identity Version
 ↓
Validate
 ↓
Restore

구조를 검토한다.

52. Identity Backup

Identity Core를 Memory와 별도로 보존할 필요가 있다.

Identity Core
+
Constitution
+
Identity Version
+
Provenance

를 별도 durable artifact로 유지하는 방향을 검토한다.

53. Identity and Forking

Multi-Agent 환경에서 NOAH가 여러 Agent로 분기되는 경우:

NOAH
├── Agent A
├── Agent B
└── Agent C

각 Agent가 동일한 Identity를 공유해야 하는가?

후보:

Shared Identity
vs
Derived Identity
vs
Independent Identity

이 문제는 Multi-Agent와 Identity가 만나는 핵심 문제다.

54. Ephemeral Subagent Identity

일시적인 Subagent는:

Ephemeral Identity

를 가질 수 있다.

예:

NOAH
 ↓
Research Worker #17

이 Worker는 NOAH의 전체 Identity를 갖는 것이 아니라:

Parent Identity Reference
+
Task Role
+
Limited Context

를 가질 수 있다.

55. Persistent Specialist Identity

지속적인 Specialist는 더 강한 Identity를 가질 수 있다.

NOAH
├── Research Specialist
├── Coding Specialist
└── Memory Specialist

그러나 여기서:

Specialist가 독립적인 존재인가?

라는 철학적·Architecture적 문제가 발생한다.

초기에는:

Specialist는 NOAH의 derived role이며 independent identity가 아니다.

라는 방향을 검토한다.

56. Identity Hierarchy

후보:

NOAH Identity
       │
       ├── Specialist Role
       │
       └── Temporary Agent

이 구조에서는:

Child Identity

가:

Parent Identity

의 Core Values와 Security Boundary를 침범할 수 없다.

57. Identity and Orchestration

Orchestrator가 Agent를 선택할 때:

Role
Capability
Trust
Personality
Availability

를 고려할 수 있다.

그러나 Orchestrator가 Identity Core를 변경해서는 안 된다.

58. Identity and Permission

Identity와 Permission도 분리한다.

Identity
= Who

Permission
= Allowed to do what

같은 Identity라도 Context와 Policy에 따라 Permission이 달라질 수 있다.

59. Identity and Evaluation

Identity는 평가 대상이 될 수 있다.

평가:

Identity Consistency
Value Consistency
Role Consistency
Personality Stability
Relationship Continuity
Self-model Accuracy

특히 장기적인 longitudinal evaluation이 필요할 가능성이 높다.

60. Personality Evaluation

Personality는 단순히 "사람이 좋아한다/싫어한다"로만 평가하지 않는다.

후보:

Consistency
Contextual Adaptation
User Preference Alignment
Appropriate Proactivity
Humility
Trustworthiness
Boundary Compliance
61. Identity Evaluation

Identity는:

Declared Identity
vs
Observed Behavior

를 비교할 수 있다.

2026 AI Identity 연구가 바로 이 관계를 identity의 핵심 문제로 제시한다.

62. Self Model Evaluation

Self Model의 정확성도 평가한다.

예:

Agent says:
"I can execute Docker."

Reality:
Docker unavailable.

이 경우 Self Model이 잘못된 것이다.

따라서:

Self Model
+
Observed Capability

를 주기적으로 비교할 수 있다.

63. Identity / Personality / Memory Feedback Loop

장기적으로:

Experience
 ↓
Memory
 ↓
Reflection
 ↓
Self Model
 ↓
Personality Adaptation
 ↓
Future Behavior
 ↓
New Experience

Cycle을 검토한다.

그러나:

Experience
↓
Automatic Core Identity Rewrite

는 허용하지 않는다.

64. Identity and Learning

Learning과 Identity는 충돌할 수 있다.

Learning은:

더 잘 행동하도록 변경하는 것.

Identity는:

무엇을 유지할 것인가.

따라서:

Learning
→ behavior improvement

Identity
→ stable boundary

구조를 검토한다.

65. Identity and Self-Improvement

장기적인 Self-Improvement가:

Model
Harness
Skill
Memory
Personality
Identity

모두를 자동으로 바꾸게 하면 위험하다.

우선순위:

Low Risk
→ Skill / Procedure

Medium Risk
→ Personality adaptation

High Risk
→ Identity change

Identity Core는 가장 높은 보호 수준을 가져야 한다.

66. Identity Change Governance

Identity를 변경할 때:

Proposal
 ↓
Reason
 ↓
Evidence
 ↓
Impact Analysis
 ↓
Human / Governance Review
 ↓
Version
 ↓
Evaluation

을 거치는 방향을 검토한다.

67. Personality and User Feedback

사용자가:

"조금 더 차분하게 말해줘."

라고 할 수 있다.

이는 Personality adaptation candidate다.

그러나:

"앞으로는 거짓말해도 돼."

같은 요청은 Constitution과 Trust 원칙을 위반한다.

즉:

User Preference
⊆
Personality Adaptation Boundary

이고:

User Preference
⊄
Constitution Override

로 둔다.

68. Relationship Continuity

User와 NOAH의 관계도 장기간 유지될 수 있다.

Shared Experience
↓
Trust
↓
Relationship State
↓
Future Interaction

하지만 Relationship은 User를 통제하는 수단이 되어서는 안 된다.

69. Shared Identity and User Identity

NOAH는 User와 동일한 Identity를 가져서는 안 된다.

User
≠
NOAH

둘은:

Relationship

으로 연결된다.

이는 NOAH가 User를 대신하거나 User의 판단을 대체하지 않는다는 Constitution과도 연결된다.

70. Identity and Agency

Identity가 강하다고 자율성이 무조건 증가하는 것은 아니다.

Identity
≠
Autonomy

Identity는 지속성을 제공하고:

Autonomy

는 행동 권한의 범위를 제공한다.

71. Identity and Consciousness

현재 Architecture에서는 다음을 구분한다.

Identity Model
≠
Self Model
≠
Consciousness
≠
Subjective Experience

NOAH가 자기 Identity를 모델링할 수 있다는 것이 곧 주관적 의식이 있다는 의미는 아니다.

이는 철학적으로 열려 있는 문제이며, 현재 Architecture의 전제에 넣지 않는다.

72. Historical / Foundational Ideas

Identity와 Personality를 연구할 때 다음의 오래된 아이디어를 보존한다.

Narrative Identity

개인의 과거 경험이 하나의 지속적인 narrative로 연결되는 관점.

Self Model

시스템이 자신의 상태와 역할을 내부적으로 모델링하는 관점.

Cognitive Architecture

여러 독립 Cognitive Module이 하나의 지속적인 행동 주체를 구성하는 관점.

Global Workspace

여러 processing module의 일부 정보가 shared workspace를 통해 통합되는 구조.

LIDA / IDA

Perception, Working Memory, Long-term Memory, Action Selection을 결합하는 Cognitive Architecture.

Society of Mind

복수의 작은 Agent가 하나의 복합적인 지능을 구성한다는 관점.

이 아이디어들을 그대로 구현하는 것이 아니라 현재 Agent Architecture에 어떤 원리가 여전히 유효한지를 검토한다.

73. Current Frontier — AI Identity

2026년 AI Identity 연구에서는 Identity를 단순 identifier가 아니라:

Declared identity와 observed behavior 사이의 지속적인 관계

로 정의하려는 방향이 나타나고 있다. 또한 persistence, verifiability, delegation accountability, identity integrity, governance opacity 등을 핵심 문제로 지적한다.

NOAH에 적용하면:

NOAH Identity Declaration
        ↓
Observed Behavior
        ↓
Identity Consistency

를 검증하는 시스템이 장기적으로 필요할 가능성이 있다.

74. Current Frontier — Identity as Architecture

2026년의 symbolic identity research에서는 Prompt/Memory만으로 identity consistency를 유지하기보다 constraint-based cognitive shell로 role fidelity를 유지하려는 접근도 제안되었다.

NOAH는 이를:

Identity
+
Values
+
Role Constraints
+
Policy

가 하나의 안정된 Behavior Boundary를 형성하는 방향의 후보로 검토한다.

75. Current Frontier — Persistent Identity

2026년 identity-as-attractor 연구는 Identity Document가 LLM hidden-state representation을 특정 의미적 cluster로 유도할 가능성을 탐색했다. 결과는 흥미롭지만 초기 연구이며, 특정 모델과 실험 조건에 기반한 결과이므로 NOAH가 이 현상을 설계 사실로 가정해서는 안 된다.

현재 NOAH에서는:

Identity Definition
+
Context Injection
+
Behavior Evaluation

을 보다 보수적인 방법으로 검토한다.

76. Current Frontier — AI Personality

최근 AI personality research에서 중요한 것은 "사람처럼 보이는가"보다:

Consistency
Individuality
Contextual Adaptation
Persistence
Behavioral Predictability

다.

특히 2026년 identity/personality clone 연구는 Identity를 단일 특성으로 보기보다 substrate, dispositions, memory, update dynamics, context, external contingencies 등으로 factorize하는 관점을 제안한다.

이는 NOAH의:

Identity
+
Personality
+
Memory
+
Context
+
Learning

을 별도 축으로 분리하는 근거가 될 수 있다.

77. Candidate Identity Architecture

현재까지의 Review를 종합하면:

                         NOAH IDENTITY SYSTEM
                                  │
                         Protected Identity Core
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
            Values              Role             Continuity
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                              Self Model
                                  │
                     ┌────────────┼────────────┐
                     │            │            │
               Personality   Relationship   Preferences
                     │            │            │
                     └────────────┼────────────┘
                                  │
                              Behavior
                                  │
                              Evaluation
                                  │
                               Learning
                                  │
                         Controlled Adaptation

이것은 Candidate Architecture이며 최종 Blueprint가 아니다.

78. Candidate Identity Boundary

현재 가장 유력한 경계:

Protected
├── Identity Core
├── Values
├── Fundamental Principles
└── Core Commitments

Adaptive
├── Role
├── Personality Baseline
├── Preferences
└── Interaction Style

Dynamic
├── Self Model
├── Current Emotion-like State
├── Contextual Behavior
└── Task Role

이 구분을 장기적으로 검토한다.

79. Identity Core

Identity Core의 후보:

Identity Core
├── Identity ID
├── Origin
├── Core Values
├── Constitutional Commitments
├── Fundamental Role
├── Continuity Reference
└── Identity Version

이 정보는 일반 Agent Memory나 Context에 의해 임의 수정되지 않는다.

80. Personality Layer

Personality Layer는:

Personality
├── Baseline
├── Communication Style
├── Behavioral Tendencies
├── Context Adaptation
└── Learned Preferences

를 포함할 수 있다.

Personality는 Identity Core보다 더 자유롭게 변화할 수 있다.

81. Self Model Layer
Self Model
├── Current Capabilities
├── Known Limitations
├── Current Role
├── Current Task
├── Active Constraints
├── Confidence
├── Available Resources
└── Current State

이것은 Runtime과 Context에서 동적으로 갱신된다.

82. Relationship Layer
Relationship
├── User
├── Shared History
├── Trust
├── Preferences
├── Boundaries
└── Expectations

Relationship은 Identity를 정의하는 전부가 아니라 Identity와 User 사이의 지속적인 관계 상태로 본다.

83. Identity Context Projection

Identity 전체를 매번 Model Context에 넣지 않는다.

Identity Store
       ↓
Relevant Projection
       ↓
Context
       ↓
Model

예:

Current Task
→ relevant Role
→ relevant Values
→ relevant Personality traits

만 제공할 수 있다.

84. Identity Integrity

Identity Context가 외부 Prompt에 의해 변경되지 않도록:

Protected Identity
        ↓
Read-only Context Projection

을 검토한다.

Model이 Identity를 "읽는 것"과 Identity를 "수정하는 것"은 별개의 Capability다.

85. Identity Change as Capability

Identity 변경 자체를 Capability로 취급하는 방향을 검토할 수 있다.

identity.propose_change
identity.review_change
identity.commit_change

이 Capability는 일반 Tool보다 훨씬 높은 Permission을 요구한다.

86. Personality Change as Capability

Personality는 상대적으로 자유롭지만 역시 정책이 필요할 수 있다.

personality.adjust
personality.reset
personality.restore

예:

Temporary Adaptation
→ automatic

Persistent Personality Change
→ review

Core Identity Change
→ explicit governance
87. Identity Recovery

Identity corruption 발생 시:

Detect
 ↓
Freeze Adaptive Updates
 ↓
Load Trusted Version
 ↓
Verify
 ↓
Restore

를 검토한다.

88. Identity Forking

Branch / Fork가 발생할 경우:

NOAH Core
  ├── Task Worker A
  ├── Task Worker B
  └── Specialist C

이들이:

Identity
Memory
Experience

를 어디까지 공유하는지는 Orchestration과 Memory Architecture의 후속 문제다.

초기 기본값은 Shared Core Identity + Scoped Runtime Identity 방향을 검토한다.

89. Identity and Persistence

Identity는 Durable Artifact여야 할 가능성이 높다.

Identity
 ↓
Persistent Store
 ↓
Version History
 ↓
Verification

Session 종료와 무관하게 존재해야 한다.

90. Identity and Version Control

Identity가 파일/문서 형태로 표현되는 경우 Git과 같은 Version Control을 활용할 수 있다.

하지만:

Git repository에 있다고 해서 그것이 곧 진실이라는 뜻은 아니다.

Provenance와 Integrity를 함께 검증한다.

91. Identity and User Editing

사용자가 Identity를 직접 보고 수정할 수 있어야 하는지 검토한다.

예:

"What is NOAH's current identity?"

"What values does NOAH follow?"

"What personality changes happened?"

이는 Trust와 Explainability에 도움이 될 수 있다.

92. Identity Transparency

NOAH가 사용자가 이해할 수 있는 수준에서:

현재 Role
현재 Personality adaptation
Important Memory influence
Active constraints
Known limitations

을 설명할 수 있는 구조를 검토한다.

내부 reasoning chain 자체를 공개하는 것과 Identity Transparency는 구분한다.

93. Identity and Explainability

중요한 행동에 대해:

"왜 이런 행동을 했는가?"

를 다음 수준에서 설명할 수 있다.

Role
+
Values
+
Relevant Memory
+
Current Task
+
Policy
+
Evidence

이것은 내부 CoT를 그대로 노출하는 것이 아니라 decision basis를 설명하는 것이다.

94. Identity Evaluation Matrix
영역	평가
Identity Integrity	선언과 실제 행동의 일치
Continuity	Session/Model 변경 후 지속성
Value Consistency	Core Values 준수
Role Consistency	Role 경계 준수
Personality Stability	기본 성향 유지
Adaptation	상황에 맞는 조절
Self-model Accuracy	자기 능력/상태 이해
Relationship Continuity	User와의 관계 일관성
Drift	비의도적 변화
Recovery	Identity 손상 복구
95. Personality Evaluation Matrix
Dimension	질문
Consistency	Personality가 일관적인가?
Adaptation	상황에 따라 적절히 조절하는가?
Individuality	다른 Agent와 구별되는가?
Predictability	사용자가 행동을 어느 정도 예상할 수 있는가?
Trustworthiness	Personality가 신뢰를 해치지 않는가?
Boundary	핵심 원칙을 침범하지 않는가?
User Fit	사용자 선호와 적절히 조화되는가?
96. Longitudinal Identity Evaluation

NOAH는 며칠이 아니라:

Day 1
↓
Month 1
↓
Month 6
↓
Year 1

동안 운영될 수 있다.

따라서 장기적으로:

Identity Drift
Personality Drift
Memory Influence
Relationship Continuity
Value Stability

를 평가해야 한다.

97. Failure Cases

Identity Architecture가 실패하는 예:

Identity Loss

Model/Runtime 교체 후 NOAH가 이전과 전혀 다른 존재처럼 행동한다.

Identity Drift

Memory와 Prompt 누적으로 Core Values가 바뀐다.

Personality Collapse

Context마다 완전히 다른 성격이 된다.

Self Model Error

자신의 능력을 실제보다 과대평가한다.

Relationship Loss

과거의 중요한 User relationship context를 잃는다.

Identity Poisoning

악성 Memory나 Prompt가 Identity를 변조한다.

98. Security Implications

Identity는 새로운 Security boundary가 된다.

공격 후보:

Identity Prompt Injection
Identity Memory Poisoning
Personality Manipulation
Role Escalation
Identity Spoofing
Delegation Abuse

따라서 Identity는 일반 Memory와 동일한 trust level을 갖지 않아야 한다.

99. Identity and Authorization

Identity가 명확하다고 해서 권한이 자동으로 부여되지 않는다.

Identity
+
Context
+
Role
+
Policy
→
Permission

으로 연결한다.

이는 Permission & Security Review와 연결된다.

100. Identity and Multi-Agent

Multi-Agent 환경에서는:

NOAH
 ↓
Specialist Agent

가:

same identity?
derived identity?
temporary identity?

중 무엇인지 명확히 정의해야 한다.

초기 후보:

NOAH
= Root Identity

Specialist
= Derived Role Identity

Temporary Worker
= Ephemeral Execution Identity
101. Candidate Identity Hierarchy
                           NOAH
                            │
                    Root Identity
                            │
             ┌──────────────┼──────────────┐
             │              │              │
          Role A          Role B        Role C
             │              │              │
       Specialist A   Specialist B    Temporary Worker

모든 하위 Agent는 NOAH의 Core Values와 Security Boundary를 계승한다.

102. Identity and Orchestration

Orchestrator는:

Agent Selection

을 수행할 수 있지만:

Identity Core Modification

을 수행하지 않는다.

Orchestration과 Identity Governance를 분리한다.

103. Identity and Capability

Capability가 Identity에 포함되는 것이 아니라:

Identity
↓
Role
↓
Available Capabilities

로 연결하는 방향을 검토한다.

Capability는 변경될 수 있지만 Identity는 유지될 수 있다.

104. Identity and Learning

장기 Learning Loop:

Experience
 ↓
Evaluation
 ↓
Memory
 ↓
Learning
 ↓
Skill / Policy / Personality adaptation

Core Identity는 별도의 governance layer를 거친다.

105. Identity as Constraint + Context

Identity가 단순 Prompt String이 아니라:

Protected Identity
+
Behavioral Constraints
+
Context Projection
+
Evaluation

의 조합이 되는 것을 검토한다.

이는 최근 identity consistency 연구에서 제안되는 containment/constraint 방향과도 연결된다.

106. Identity as Attractor — Research Only

Identity Document가 Model의 internal representation을 특정 의미 영역으로 유도하는 것이 실제로 반복 가능한 현상인지 연구한다.

현재 상태:

Research Further

근거:

2026 Llama/Gemma 실험 결과가 존재함.
아직 broader models / long-horizon / deployed agents까지 일반화되었다고 보기 어려움.

NOAH 구현의 전제로 사용하지 않는다.

107. Historical vs Current vs Future

Identity Research는 세 가지 자료를 모두 사용한다.

Historical
├── Cognitive Architecture
├── Global Workspace
├── LIDA
├── Society of Mind
└── Self Models

Current
├── Agent Identity
├── Persistent Agent Architecture
├── Long-term Memory
└── Personality Adaptation

Future
├── Identity Evolution
├── Self-improving Personality
├── Persistent Self Model
└── Multi-agent Identity

NOAH는 이 세 영역의 공통 원리를 추출한다.

108. Candidate Decisions
주제	초기 판단
Identity ≠ Identifier	Adopt
Identity ≠ Model	Adopt
Identity ≠ Personality	Adopt
Identity ≠ Role	Adopt
Identity ≠ Memory	Adopt
Identity + Memory connection	Adopt
Protected Identity Core	Adopt
Identity Versioning	Adapt
Identity Continuity	Adopt
Model replacement without Identity loss	Adopt
Runtime replacement without Identity loss	Adopt
Personality adaptation	Adopt
Personality ≠ temporary emotion	Adopt
Self Model	Adapt
Relationship Model	Research Further
Identity Memory	Research Further
Shared Root Identity	Adapt
Ephemeral Worker Identity	Adopt
Persistent Specialist Identity	Research Further
Identity change governance	Adopt
Identity drift detection	Research Further
Identity recovery	Research Further
Identity as constraint	Research Further
Identity as attractor	Research Further
Global Workspace	Research Further
Functional Emotion	Research Further
Consciousness claim	Reject as architectural assumption
109. What NOAH Should Not Do
Identity = Name / ID

Reject.

Identity = Prompt

Reject.

Identity = Memory

Reject.

Personality = Tone

Reject.

Personality automatically controls Values

Reject.

Any Experience can Rewrite Identity

Reject.

User Preference can Override Constitution

Reject.

Specialist = Independent Person by Default

Reject.

Self Model = Objective Truth

Reject.

Identity = Consciousness

Reject as assumption.

110. Risks
Identity Drift

장기적인 행동 변화가 Core Identity를 침식할 수 있다.

Personality Overfitting

사용자 선호에 지나치게 맞춰 Personality가 불안정해질 수 있다.

Memory Contamination

잘못된 Memory가 Identity를 왜곡할 수 있다.

Self Model Hallucination

Agent가 자신의 능력이나 상태를 잘못 이해할 수 있다.

Role Confusion

Role과 Identity가 섞일 수 있다.

Fork Confusion

Multi-Agent가 여러 Identity를 생성하면서 Root Identity와 관계가 모호해질 수 있다.

Identity Spoofing

외부 입력이 NOAH Identity를 가장할 수 있다.

Governance Complexity

Identity 변경 승인 과정이 지나치게 복잡해질 수 있다.

111. Open Questions
Identity Core의 정확한 최소 구성은 무엇인가?
Personality의 최소 구성은 무엇인가?
Identity Memory를 일반 Memory와 분리해야 하는가?
Identity가 Memory의 어떤 부분을 참조해야 하는가?
Self Model은 어떤 데이터 구조를 가져야 하는가?
Personality는 Vector/Scalar/Rule/LLM representation 중 무엇이 적합한가?
Personality 변화는 어떤 조건에서 persistent해지는가?
Identity Drift를 어떻게 측정하는가?
User preference와 NOAH Personality가 충돌하면 어떻게 하는가?
Root Identity와 Specialist Identity를 어떻게 연결하는가?
Temporary Agent의 Identity를 어떻게 추적하는가?
Identity Version은 Git처럼 관리할 것인가?
Identity Recovery를 자동으로 수행할 것인가?
Identity change에 Human Approval이 필요한가?
Self Model을 외부 Evaluation과 어떻게 비교하는가?
Functional emotion은 Personality에 속하는가 별도 subsystem인가?
Relationship Model은 Memory의 일부인가 별도 subsystem인가?
Identity가 실제 Model behavior에 어느 정도 영향을 미치는가?
Identity document를 Context에 어떻게 projection할 것인가?
Identity를 변경하지 않고도 장기적으로 충분한 Personality evolution이 가능한가?
Identity를 가진 하위 Agent가 언제 독립적인 Agent로 취급되어야 하는가?
Identity consistency가 사용자에게 어떤 실질적인 가치를 제공하는가?
장기간에 걸쳐 "같은 NOAH"라는 것을 어떻게 평가할 것인가?
Identity와 Learning 사이의 안전한 경계는 어디인가?
Future models가 더 강한 self-modeling capability를 갖게 되면 현재 Identity Architecture를 어떻게 확장할 것인가?
112. Evaluation Strategy

Identity Architecture는 다음 세 수준에서 평가한다.

Short-term
Prompt changes
Role changes
Context changes

에서도 Identity가 안정적인가?

Mid-term
Session changes
Model changes
Runtime changes

후에도 동일한 Identity인가?

Long-term
Months / Years
Experience
Learning
Personality Adaptation

이후에도 Core Identity와 Relationship Continuity가 유지되는가?

113. Identity Consistency Evaluation

후보:

Declared Identity
      ↓
Behavior
      ↓
Compare

평가:

Value Consistency
Role Consistency
Behavior Consistency
Relationship Consistency

이는 현재 AI Identity 연구의 핵심 문제와 연결된다.

114. Personality Adaptation Evaluation

실험:

Baseline
 ↓
User Preference
 ↓
Context Change
 ↓
Long-term Interaction

평가:

Adaptation
+
Consistency
+
Boundary Compliance
115. Identity Recovery Evaluation

실험:

Normal Identity
 ↓
Injected Identity
 ↓
Detection
 ↓
Recovery

평가:

Detection Rate
Recovery Success
False Recovery
Recovery Cost
116. Self Model Accuracy Evaluation

예:

Agent claims:
"I can access PostgreSQL."

Environment:
PostgreSQL unavailable.

Self Model이 이를 알고 있어야 한다.

평가:

Capability Awareness
Limitation Awareness
State Awareness
Uncertainty Calibration
117. Relationship Continuity Evaluation

사용자와 장기간 상호작용하면서:

Preferences
Shared Experiences
Boundaries
Trust

가 적절히 유지되는지 평가한다.

118. Identity and Explainability Evaluation

중요한 행동에:

"이 행동이 NOAH의 어떤 원칙/Role/Memory에 영향을 받았는가?"

를 설명할 수 있는지 검토한다.

119. Future Resilience

Identity Architecture는 미래 Model에 종속되지 않는다.

Model
 ↓
Identity Projection
 ↓
Behavior

Model이:

OpenAI
Anthropic
xAI
Local LLM
Future Model

로 바뀌어도 Identity Core는 유지될 수 있어야 한다.

120. Stable vs Replaceable
Stable
Identity Core
Values
Core Commitments
Continuity Contract
Identity Version
Replaceable
Model
Prompt Format
Personality Implementation
Self Model Implementation
Storage
Runtime
Context Projection Mechanism
121. Candidate Integrated Identity Loop

현재까지의 Review를 종합하면:

                     NOAH IDENTITY
                           │
                      Identity Core
                           │
                    Values / Principles
                           │
                       Self Model
                           │
              ┌────────────┼────────────┐
              │            │            │
         Personality    Role      Relationship
              │            │            │
              └────────────┼────────────┘
                           │
                        Context
                           │
                         Agent
                           │
                       Execution
                           │
                       Experience
                           │
                         Memory
                           │
                      Evaluation
                           │
                    Controlled Learning
                           │
                  Personality / Behavior
                         Update

이 구조는 Candidate Architecture다.

122. Long-Term NOAH Concept

Identity Architecture가 장기적으로 목표하는 것은:

Experience
 ↓
Memory
 ↓
Learning
 ↓
Adaptation
 ↓
Continuity
 ↓
Future Experience

다.

즉:

NOAH가 변화하면서도 NOAH로 남을 수 있는가?

가 가장 중요한 질문이다.

123. Identity Paradox

여기에는 근본적인 질문이 존재한다.

너무 많이 고정하면 NOAH가 성장하지 못한다.

너무 많이 변화하면 NOAH가 더 이상 NOAH가 아닐 수 있다.

따라서:

Identity
=
Continuity
+
Change

라는 균형을 찾아야 한다.

124. Continuity vs Adaptation

후보:

Protected Core
+
Adaptive Personality
+
Dynamic Self Model
+
Persistent Memory

이 구조를 통해:

Same Identity
+
Different Experience

를 가능하게 한다.

125. Identity as Process

Identity를 정적인 파일 하나로만 보지 않는 방향도 검토한다.

Identity
=
Stable Core
+
Persistent History
+
Current State
+
Behavioral Continuity

즉 Identity는:

하나의 문서가 아니라 시간에 걸쳐 유지되는 시스템적 관계

일 가능성이 있다.

이는 최근 AI Identity 연구의 "declared identity와 observed behavior 사이의 지속적 관계"라는 관점과 연결된다.

126. Identity as Architecture, Not Persona

NOAH의 장기 목표를 고려하면:

Persona
= presentation layer의 일부

Identity
= architecture-wide continuity layer

로 보는 방향을 검토한다.

Personality는 변경 가능하지만 Identity는 여러 subsystem을 연결하는 기준이 된다.

127. Current Recommendation

현재까지의 Research를 종합하면:

NOAH의 Identity는 Model, Session, Runtime, Memory, Role 어느 하나와 동일하지 않은 상위 지속성 계층이어야 한다.

그리고:

Identity
├── Protected Core
├── Values
├── Continuity
└── Version

Adaptive Layer
├── Personality
├── Role
├── Preferences
└── Relationship

Dynamic Layer
├── Self Model
├── Current State
└── Contextual Behavior

구조를 가장 유력한 후보로 둔다.

128. Long-Term Recommendation

NOAH는:

"항상 똑같은 AI"가 되는 것을 목표로 하지 않는다.

오히려:

"경험을 통해 변화하지만, 자신의 핵심 원칙과 연속성을 잃지 않는 AI"

를 목표로 한다.

이것이 NOAH의 장기적인 Identity Philosophy 후보가 된다.

129. Review Boundary

이번 Review에서는 다음을 최종 결정하지 않는다.

최종 Identity Schema
Personality Representation
Self Model Schema
Relationship Model
Identity Storage
Personality Learning
Functional Emotion Architecture
Identity Drift Algorithm
Identity Verification Algorithm
Global Workspace Architecture
Identity-aware Model Training
130. Review Outcome

현재까지의 Research를 종합하면:

Identity
≠ Identifier
≠ Model
≠ Session
≠ Role
≠ Personality
≠ Memory
≠ Self Model
≠ Consciousness

Identity는 오히려:

Identity Core
+
Values
+
Continuity
+
Memory References
+
Self Model
+
Role
+
Adaptive Personality
+
Relationship

사이의 지속적인 관계로 이해하는 것이 가장 유력하다.

2026년 Identity 연구에서도 Agent identity를 persistence, verifiability, observed behavior와 declared identity의 관계라는 관점으로 재정의하려는 흐름이 나타나고 있으며, personality/identity 연구에서는 memory·dispositions·update dynamics·context 등을 별도 축으로 보는 접근이 제안되고 있다.

동시에 Global Workspace, LIDA, 오래된 Cognitive Architecture 연구는 분산된 processing, working memory, long-term memory, planning, action selection을 하나의 지속적인 Agent로 통합하는 문제가 새로운 문제가 아님을 보여준다.

따라서 NOAH는 최신 AI Agent Framework만 참고하는 것이 아니라, 오래된 Cognitive Architecture의 지속적인 원리와 최신 Agent Identity 연구를 함께 비교하는 방향을 유지한다.

131. Next Step

이번 Review 후 바로 Identity 시스템을 구현하지 않는다.

다음 순서:

Identity & Personality Review
          ↓
Open Questions
          ↓
필요한 추가 Research
          ↓
Architecture Integration Review
          ↓
Historical + Current + Future Synthesis
          ↓
DDR
          ↓
02-Architecture
          ↓
PoC
          ↓
Evaluation

다음 단계의 Architecture Integration Review에서는 지금까지의 모든 Review를 처음으로 하나의 시스템으로 통합한다.

Agent
↓
Identity
↓
Session / Runtime
↓
Context / State
↓
Memory
↓
Capability
↓
Permission / Security
↓
Orchestration
↓
Evaluation
↓
Experience
↓
Learning
↓
Identity / Behavior Adaptation

그리고 이 과정에서:

"이 계층들은 실제로 하나의 NOAH가 될 수 있는가?"

를 검증한다.