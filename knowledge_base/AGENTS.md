# 프로젝트 개요 (WHAT & WHY)
- **프로젝트명**: Pi Agent Knowledge Base Skill Integration
- **목적**: Pi 코딩 에이전트가 로컬 환경의 코드와 문서를 분석하고, SQLite 및 `sqlite-vec`을 활용하여 자체적으로 지식을 CRUD(생성, 조회, 수정, 삭제) 할 수 있도록 하는 확장 스킬을 구현합니다.

# 작업 방식 (HOW)
- **개발 환경**: Python 기반이며, 비동기(`asyncio`)와 타입 힌트를 적극 사용합니다.
- **로컬 우선 주의**: 외부 클라우드 DB 없이 인프로세스(in-process)로 작동하는 `sqlite-vec`과 로컬 임베딩(`llama-cpp-python`)을 사용합니다.
- **참조 문서**: 전체 구현 계획과 진행 상황은 `@PLAN.md`를 참조하여 파악하세요. 지식베이스 제어 규격은 `@.pi/skills/knowledge-base/SKILL.md`를 참조하세요.

# 아키텍처 및 폴더 구조 지침
- 본 프로젝트의 상세 폴더 디렉토리 구조(예: `scripts/core/` 등)와 스토리지 격리 수준 등 핵심 설계 의사결정 사항은 `@ARCHITECTURE.md` 파일(또는 `@.pi/skills/knowledge-base/ARCHITECTURE.md`)에 정의되어 있습니다. 
- 새로운 CRUD 스크립트를 작성하거나 공통 모듈을 수정하기 전, **반드시 `@ARCHITECTURE.md` 파일을 먼저 읽고** 정해진 규격과 구조를 준수하여 구현하세요.

# Git 워크플로우 (Commit & Push)
- 에이전트는 하나의 논리적 작업 단위(예: 스키마 생성, 스크립트 작성 등)가 완료되고 테스트를 통과할 때마다 반드시 Git 커밋을 수행해야 합니다.
- 커밋 메시지는 Conventional Commits 형식(예: `feat: add SQLite vector schema`)을 준수합니다.
- 로컬 커밋이 완료되고 시스템 변경 사항이 안정적이라 판단되면, 현재 브랜치에 `git push`를 실행하여 원격 저장소에 동기화하세요.
