# Interview Module Architecture Foundation

## Goals
- Provide a **production-ready architecture foundation** for interview practice.
- Enforce **framework independence** for business logic.
- Keep **business logic out of React components**.
- Support **dependency injection** between loaders and providers.
- Enable future extension for:
  - backend APIs (question sourcing, session persistence)
  - AI generation (not implemented here)
  - scoring (not implemented here)

## Folder Structure
```
frontend/src/modules/interview/
  components/
  pages/
  context/
  hooks/
  services/
    providers/
    data/questions/
    utils/
    types/
    constants/
  ARCHITECTURE.md
```

## Data Models (Single Source of Truth)
All models live in the services layer and are imported by other module services.

- `Question`
- `Category`
- `InterviewSession`
- `SessionAnswer`
- `PracticeMode`
- `SessionStatus`

## Dependency Injection (DI)
### DI chain (required)
```
InterviewContext
  -> SessionEngine (framework-independent)
       -> QuestionLoader
            -> QuestionProvider (abstraction)
                 -> LocalQuestionProvider
                 -> CloudQuestionProvider (stub)
```

### Provider rule
- The SessionEngine **never** knows where questions come from.

## Question Flow (Data Flow Diagram)
```
QuestionLoader.loadQuestions(filters, number)
  1) Ask all providers for questions
  2) Merge results
  3) Remove duplicates by `question.id`
  4) Filter by category/topic/difficulty
  5) Randomize order
  6) Return `number` questions
```

## Session Flow (Data Flow Diagram)
```
SessionEngine
  createSession(mode)
  startSession()
  pauseSession()
  resumeSession()
  skipQuestion()
  submitAnswer(answer)
  finishSession()
  generateSummary()  // no scoring yet
```

## Session Engine Independence
- `SessionEngine` is implemented as a plain JS/TS class.
- It has **no React, no router, no timers**.
- It accepts collaborators via constructor injection.

## React Layer Rules
- React components must depend only on `InterviewContext`.
- React components must not call providers or QuestionLoader directly.
- React components must not contain session business logic.

## Extension Points
### Providers
- Add additional providers (e.g., backend provider) implementing `QuestionProvider`.

### Summary / Scoring
- Extend `generateSummary()` later to include scoring.

### AI
- Add a future AI service/provider that produces questions or coaching content.
  - Not implemented in this foundation.

## Build Verification Checklist
- Confirm frontend builds successfully.
- Confirm `/interview` route renders without runtime errors.
- Confirm React components have no business logic.
- Confirm SessionEngine has no React framework imports.

