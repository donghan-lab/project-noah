# Connect AI Research

> Project NOAH Reference Research
> Research 대상: Connect AI
> Repository: https://github.com/wonseokjung/connect-ai
> Branch: `main`
> Research Status: Initial Research

---

# 1. Research Purpose

Connect AI를 Project NOAH의 Reference로 분석한다.

본 연구의 목적은 Connect AI의 전체 구현을 복제하는 것이 아니라, 실제 개인 개발 환경에서 Agent, Specialist, Local LLM, Knowledge System, Tool/Action, User Interface를 어떻게 통합하는지 이해하고 Project NOAH의 향후 Architecture Review에 활용할 수 있는 정보를 수집하는 것이다.

Connect AI의 구조를 그대로 채택할지 여부는 본 문서에서 결정하지 않는다.

---

# 2. Research Scope

이번 1차 연구에서는 다음 영역을 중심으로 Connect AI를 조사했다.

* Agent Definition
* Agent Registry
* Agent Role / Specialty
* Agent Persona
* Agent Orchestration 관점
* Local LLM Integration
* Ollama / LM Studio
* Action / Capability Model
* VS Code Extension Integration
* Session / Chat State
* Knowledge / Second Brain
* Local Model Detection
* System Resource Detection
* External Bridge
* Git-based Knowledge Synchronization
* Local-first / Offline Architecture

이번 연구에서는 Connect AI의 전체 기능을 모두 분석하지 않고, Project NOAH의 Agent 및 Runtime Architecture와 관련된 요소를 우선적으로 조사한다.

---

# 3. Research Sources

## Repository

https://github.com/wonseokjung/connect-ai

## README

https://github.com/wonseokjung/connect-ai/blob/main/README.md

## Agent Definition

https://github.com/wonseokjung/connect-ai/blob/main/src/agents.ts

## Extension Integration

https://github.com/wonseokjung/connect-ai/blob/main/src/extension.ts

## System Specification

https://github.com/wonseokjung/connect-ai/blob/main/src/system-specs.ts

## Plaza / Knowledge Integration

https://github.com/wonseokjung/connect-ai/blob/main/src/plaza.ts

---

# 4. Connect AI Overview

Connect AI는 VS Code / Cursor 환경에서 동작하는 로컬 중심 AI 확장 프로그램이다.

현재 README에서는 Connect AI를 로컬 및 오프라인 환경을 중심으로 동작하는 자율 지식 엔진으로 설명하며, 사용자 정보와 지시를 바탕으로 지식을 구조화하고, 로컬 파일 시스템과 Git 기반 지식 저장소를 활용하며, Ollama 또는 LM Studio와 연결하는 방향을 제시한다.

주요 특징은 다음과 같이 정리할 수 있다.

```text
VS Code / Cursor
        ↓
   Connect AI
        ↓
┌───────┼────────┐
│       │        │
Agent   Local LLM Knowledge
│       │        │
│    Ollama /    Second Brain
│    LM Studio
│
└── Actions / File / Terminal / Automation
```

따라서 Connect AI는 OpenCode나 Grok Build처럼 독립적인 대규모 Agent Runtime을 전면에 내세우기보다 **IDE 확장 프로그램 안에서 Agent, Local LLM, Knowledge, Actions를 통합하는 실용적인 시스템**으로 볼 수 있다.

---

# 5. Agent Definition

Connect AI는 `agents.ts`에서 Agent의 공통 정의를 `AgentDef`로 모델링한다.

현재 정의된 주요 속성은:

```text
AgentDef
├── id
├── name
├── role
├── emoji
├── color
├── specialty
├── tagline
├── profileImage?
└── persona?
```

`AGENTS` Registry에는 CEO, YouTube, Instagram, Designer, Developer, Business, Secretary, Editor, Writer, Researcher 등의 Agent가 등록되어 있다.

또한:

```text
AGENT_ORDER
SPECIALIST_IDS
```

를 별도로 관리하여 Agent의 전체 순서와 Specialist 집합을 구분한다.

---

# 6. Agent Registry

Connect AI의 Agent 구조는 다음과 같이 표현할 수 있다.

```text
Agent Registry
│
├── CEO
│
├── YouTube
├── Instagram
├── Designer
├── Developer
├── Business
├── Secretary
├── Editor
├── Writer
└── Researcher
```

CEO는 오케스트레이션, 작업 분해, 종합 판단 및 다음 Action 결정을 담당하는 상위 역할로 정의되어 있다.

나머지 Agent는 특정 분야를 전문적으로 담당하는 Specialist 역할을 갖는다.

---

# 7. Agent Role and Specialty

각 Agent는 역할과 전문 영역을 명시적으로 갖는다.

예를 들어 Developer Agent는:

* 코드 작성
* 코드 편집
* 디버깅
* 자동화
* API 통합
* 데이터 파이프라인
* Git workflow

등을 전문 영역으로 정의한다.

Researcher는:

* 트렌드 조사
* 경쟁 분석
* 데이터 수집
* 자료 요약
* 사실 확인

등을 담당한다.

따라서 Connect AI에서는 Agent를 단순 모델 인스턴스라기보다 **역할 중심의 전문 인력/전문가 추상화**로 표현하는 경향이 관찰된다.

---

# 8. Agent Persona

일부 Agent는 `persona`를 별도로 가진다.

Persona는 Agent가 어떤 말투와 행동 성향을 사용할지를 정의하며, Agent의 전문 영역과 별개로 표현된다.

개념적으로:

```text
Agent
├── Role
├── Specialty
└── Persona
```

가 된다.

즉 역할(Role)과 전문성(Specialty)과 성격/말투(Persona)를 하나의 Agent Definition 안에서 관리한다.

---

# 9. Agent Architecture Character

Connect AI에서 관찰되는 Agent 구조는 OpenCode나 Grok Build와 성격이 다르다.

OpenCode에서는 Agent가 Runtime의 실행 단위에 가까웠고,

Grok Build에서는 Agent Runtime과 Session Runtime이 강하게 연결된다.

Connect AI에서는 현재 확인한 코드 기준으로:

```text
Agent Registry
      ↓
Role / Specialty
      ↓
Persona
      ↓
Extension / Prompt Integration
```

이라는 **Role / Persona 중심의 Agent 모델**이 두드러진다.

따라서 Connect AI는 Agent Runtime 자체보다 **Agent Organization / Specialist Model**을 연구하기 위한 Reference로서 가치가 있다.

---

# 10. Local LLM Architecture

Connect AI는 Local LLM 환경을 주요 실행 대상으로 사용한다.

README에서는 Ollama와 LM Studio를 지원하고 설치된 모델을 자동으로 검색하여 UI에서 선택할 수 있는 구조를 설명한다.

개념적으로:

```text
Connect AI
   │
   ├── Ollama
   │
   └── LM Studio
          ↓
       Local LLM
```

따라서 특정 Cloud Model Provider에 강하게 종속되는 구조보다 **Local Model Endpoint abstraction**을 사용하는 방향이 관찰된다.

---

# 11. Dynamic Model Detection

`system-specs.ts`는 사용자의 실행 환경을 측정한다.

측정 정보에는 다음이 포함된다.

* Total RAM
* Free RAM
* CPU Model
* CPU Core Count
* Platform
* Architecture
* Apple Silicon 여부
* Safe Model Budget

또한 모델 ID에서 파라미터 크기와 양자화 정보를 추정하여 대략적인 모델 메모리 사용량을 계산한다.

이를 통해 Connect AI는 단순히 모델 목록을 보여주는 것보다:

```text
System Hardware
      ↓
Available Memory
      ↓
Model Memory Estimate
      ↓
Safe Model Selection
```

이라는 **Hardware-aware Model Selection** 방향을 갖는다.

---

# 12. Action / Capability Model

Connect AI는 로컬 환경에서 Agent가 수행할 수 있는 작업을 Action 개념으로 표현한다.

README에서 명시하는 대표 기능은:

* 파일 생성
* 파일 수정
* 파일 삭제
* 파일 읽기
* 디렉터리 탐색
* 터미널 명령 실행

등이다.

따라서:

```text
Agent
  ↓
Action
  ↓
Local Environment
```

라는 구조가 존재한다.

---

# 13. Action-driven Execution

Connect AI는 OpenCode처럼 모든 Tool을 정교한 Registry / Definition / Permission Service 계층으로 추상화하는 것과는 다른 접근을 보인다.

현재 확인한 구현에서는 LLM의 지시 및 Action 표현을 VS Code Extension이 해석하고 실제 파일/터미널 작업과 연결하는 방식이 중요한 역할을 한다.

개념적으로:

```text
LLM / Agent
      ↓
Action
      ↓
Extension
      ↓
Filesystem / Terminal / External API
```

이 구조는 Runtime abstraction을 상대적으로 단순화할 수 있지만, 장기적으로 Capability와 Permission을 확장할 경우 별도의 정책 계층이 필요할 가능성이 있다.

---

# 14. VS Code Extension as Integration Layer

Connect AI의 중심 실행 환경은 VS Code Extension이다.

따라서 Extension은 단순 UI가 아니라:

```text
Extension
├── Agent
├── Local LLM
├── Chat State
├── File System
├── Terminal
├── Knowledge
├── Model Configuration
├── External Bridge
└── Automation
```

을 연결하는 통합 계층 역할을 한다.

이는 OpenCode/Grok Build의 독립 Runtime 구조와 비교할 때 Connect AI의 중요한 설계 특징이다.

---

# 15. Chat State and Session

Connect AI는 VS Code Extension 내부에서 Chat History와 Display Message 상태를 관리한다.

즉 Conversation State가 별도의 독립적인 Durable Runtime으로 완전히 분리되어 있다기보다는 Extension의 상태 관리와 결합되어 있는 구조로 보인다.

개념적으로:

```text
VS Code Extension
      ↓
Chat State
      ↓
Chat History
      ↓
Local Persistence
```

이 구조는 개인용 IDE Agent를 빠르게 구현하는 데는 단순하지만, 장기적으로 복잡한 Session Runtime이나 분산 실행을 지원하려면 별도의 Session 계층이 필요할 수 있다.

---

# 16. Knowledge / Second Brain

Connect AI의 매우 중요한 특징 중 하나는 Local Knowledge 구조를 별도의 핵심 기능으로 취급한다는 점이다.

README에서는 `~/.connect-ai-brain`을 로컬 지식 공간으로 사용하고, 원시 데이터와 Wiki/Skill 형태의 Markdown 구조로 지식을 정리하는 방향을 제시한다.

개념적으로:

```text
User Information
      ↓
Agent
      ↓
Knowledge Structuring
      ↓
Markdown Knowledge
      ↓
Local Brain
```

이 부분은 단순 Coding Agent와 비교했을 때 Connect AI의 중요한 차별점이다.

---

# 17. Knowledge Synchronization

README에서는 로컬에서 생성된 파일을 Git을 이용해 자동으로 `add`, `commit`, `push`하는 Auto-Git Sync 기능을 제시한다.

개념적으로:

```text
Knowledge Created
      ↓
Local Markdown
      ↓
Git Add
      ↓
Git Commit
      ↓
Git Push
```

따라서 Knowledge Storage와 Version Control을 결합하는 접근을 확인할 수 있다.

---

# 18. System-aware Local Inference

`system-specs.ts`는 단순 환경 표시를 넘어 모델을 안전하게 실행하기 위한 메모리 예산을 계산한다.

예를 들어:

```text
Machine
 ↓
RAM / CPU Detection
 ↓
Safe Model Budget
 ↓
Model Memory Estimate
 ↓
Model Selection
```

이라는 구조를 사용한다.

이는 NOAH가 Local Inference를 주요 실행 방식 중 하나로 채택할 경우 참고할 수 있는 방향이다.

---

# 19. External Bridge

Connect AI README는 로컬 환경의 `4825` 포트를 통해 외부 Agent University 웹 플랫폼과 통신하고 지식을 로컬 Brain에 주입하는 구조를 설명한다.

따라서:

```text
External Web
      ↓
Local HTTP Bridge
      ↓
Connect AI Extension
      ↓
Local Knowledge
```

와 같은 구조를 사용한다.

이는 Local-first 시스템에서도 외부 Interface를 선택적으로 연결할 수 있음을 보여준다.

---

# 20. Observed Overall Architecture

현재까지 확인한 구조를 단순화하면 다음과 같다.

```text
                         Connect AI

                      VS Code / Cursor
                            │
                            ▼
                     Connect AI Extension
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     Agent Registry      Local LLM        Chat State
          │                 │                 │
          │            Ollama / LM          │
          │              Studio             │
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                       Action Layer
                      /      |      \
                     /       |       \
                Filesystem Terminal Knowledge
                            │
                            ▼
                    Local Knowledge Brain
                            │
                            ▼
                       Git Sync / Bridge
```

---

# 21. Strengths Observed

## 21.1 Simple Agent Model

Agent를 Role + Specialty + Persona로 직관적으로 표현한다.

## 21.2 Specialist Organization

CEO와 Specialist Agent를 구분하여 사람 조직과 유사한 역할 분담 구조를 만든다.

## 21.3 Local-first Architecture

Ollama와 LM Studio를 사용하여 Local LLM 실행을 주요 방식으로 지원한다.

## 21.4 Knowledge-centric Design

Coding Assistant를 넘어 지식 수집과 구조화를 시스템의 중요한 기능으로 취급한다.

## 21.5 Hardware-aware Model Selection

사용자의 RAM/CPU 환경을 측정하고 모델 메모리 사용량을 추정하는 기능을 제공한다.

## 21.6 Tight IDE Integration

VS Code 내부에서 Agent, 파일, 터미널, 지식 시스템을 직접 연결하기 때문에 개인 개발 환경에 빠르게 통합할 수 있다.

---

# 22. Potential Trade-offs

## 22.1 Runtime Abstraction

OpenCode나 Grok Build처럼 Session / Runner / Tool / Permission을 독립 계층으로 강하게 분리하는 구조보다 Extension 통합도가 높다.

따라서 시스템이 커질 경우 책임 분리가 어려워질 가능성이 있다.

## 22.2 Action / Permission Complexity

Action을 단순하고 직접적으로 연결하는 방식은 초기 구현에는 유리하지만, Agent 수와 Capability가 증가할 경우 Permission과 Policy를 독립 계층으로 발전시킬 필요가 있을 수 있다.

## 22.3 Session Coupling

Chat State와 Extension 상태가 밀접하게 연결되어 있어 장기적인 Autonomous Runtime이나 다중 Session 실행을 위해서는 별도 Session Architecture가 필요할 가능성이 있다.

## 22.4 Persona / Capability Coupling

현재 Agent Definition 안에서 Role, Specialty, Persona가 함께 관리된다.

규모가 커지면:

```text
Identity
Role
Capability
Personality
Permission
```

등을 별도 개념으로 분리할 필요가 있을 수 있다.

---

# 23. Implementation vs Design Status

이번 Research에서는 다음을 구분한다.

### Observed / Implemented

현재 Repository 코드에서 직접 확인된 구조.

### Designed

README 또는 코드 구조에서 설계 의도가 확인되는 부분.

### Partial

일부 기능만 조사했거나 일부 구현만 확인한 부분.

### Not Yet Investigated

다음 단계에서 확인할 필요가 있는 부분.

현재 특히 다음 영역은 전체 분석을 수행하지 않았다.

* Agent selection / orchestration 전체 흐름
* Action execution 전체 구현
* Permission의 모든 세부 규칙
* Second Brain 전체 데이터 모델
* External bridge 전체 lifecycle
* Agent 간 실제 delegation 흐름

---

# 24. NOAH-Relevant Questions

아래는 NOAH에 대한 결정이 아니라, Connect AI에서 얻은 Architecture 질문이다.

## Agent

* Agent의 Role과 Persona를 분리하는 것이 좋은가?
* Agent Identity와 Capability는 분리해야 하는가?
* Specialist Agent Registry가 NOAH에도 필요한가?

## Orchestration

* CEO와 Specialist 같은 조직 모델이 실제 Agent 협업에 유용한가?
* Agent 간 delegation은 어떤 형태로 표현하는 것이 좋은가?
* 역할 기반 Agent와 작업 기반 Agent 중 어느 쪽이 더 일반적인가?

## Local Model

* Local-first Model Provider abstraction을 NOAH에 어느 수준까지 적용할 것인가?
* Hardware-aware Model Selection이 필요한가?
* Model routing에 System Resource를 고려해야 하는가?

## Capability

* Action 기반 접근과 Tool 기반 접근을 어떤 수준에서 결합할 것인가?
* Capability와 Permission을 어떻게 분리할 것인가?

## Knowledge

* Knowledge와 Memory를 동일한 개념으로 볼 것인가?
* Markdown 기반 Knowledge가 장기 Memory의 일부가 될 수 있는가?
* Git을 Knowledge Versioning Layer로 사용할 가치가 있는가?

## Runtime

* IDE Extension을 Runtime의 중심으로 둘 것인가?
* 아니면 독립 Runtime과 Client를 분리하는 것이 장기적으로 유리한가?

---

# 25. Research Boundary

이번 Research에서는 다음을 결정하지 않았다.

* NOAH가 Connect AI의 Agent 구조를 채택할지 여부
* CEO / Specialist 구조의 채택 여부
* Persona Architecture
* Local LLM Architecture
* Action Architecture
* Knowledge Storage Architecture
* Git-based Memory / Knowledge Versioning
* VS Code Extension 중심 Runtime 여부

Connect AI는 NOAH의 설계를 직접 정의하는 시스템이 아니라 하나의 Reference다.

---

# 26. Comparison Position

이번 1차 Research에서 확인한 세 Reference는 서로 상당히 다른 방향을 보여준다.

```text
OpenCode
→ Agent Runtime / Session / Tool 중심

Grok Build
→ Session Actor / Agent Harness / Lifecycle 중심

Connect AI
→ Agent Organization / Local LLM / Knowledge 중심
```

따라서 세 프로젝트를 단순히 "어느 것이 더 좋은가"로 비교하는 것은 적절하지 않다.

각각이 서로 다른 문제를 강하게 해결하고 있다.

---

# 27. Research Conclusion

Connect AI는 대규모 Agent Runtime을 추상적으로 분리하기보다는 **VS Code Extension이라는 단일 실행 환경 안에서 Agent, Local LLM, Action, Knowledge, UI를 긴밀하게 통합하는 접근**을 보여준다.

특히 다음 요소가 중요한 Research 대상이다.

```text
Agent Registry
+
Role / Specialty / Persona
+
Local Model Integration
+
Hardware-aware Model Selection
+
Action-based Capability
+
Knowledge Brain
+
Git Synchronization
+
IDE Integration
```

OpenCode와 Grok Build가 보여주는 복잡한 Agent Runtime과는 다른 방향의 Reference라는 점에서 의미가 있다.

그러나 Connect AI의 구조가 NOAH에 적합하다는 결정은 아직 이루어지지 않았다.

본 문서는 Research 결과를 보존하는 문서이며, 최종 Architecture 결정은 OpenCode 및 Grok Build와의 Architecture Review를 거친 후 Decision을 통해 수행한다.
