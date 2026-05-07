# Knowledge Base Skill 아키텍처 및 구현 지침

본 문서는 Pi 에이전트의 지식베이스(Knowledge Base) 스킬 확장을 위한 폴더 구조 및 핵심 아키텍처 결정 사항을 정의합니다. 본 스킬 모듈은 특정 프로젝트 경로에 종속되지 않고 이식 가능(Portable)하도록 설계되었습니다. 에이전트는 해당 스킬을 구현하고 유지보수할 때 이 구조를 준수해야 합니다.

## 1. 디렉토리 구조 (Directory Structure)

지식베이스 스킬은 터미널에서 독립적으로 실행 가능한 파이썬 스크립트 모음으로 구성되며, 스킬 루트 디렉토리를 기준으로 다음과 같이 구성됩니다.
```text
knowledge-base/              # 스킬 루트 디렉토리 (배포/복사 시 이 폴더 전체를 이동)
├── SKILL.md                 # 스킬 명세서: 에이전트가 읽고 동작 방식을 이해하는 문서
├── ARCHITECTURE.md          # 현재 문서 (구조 및 의사결정 기록)
├── requirements.txt         # 의존성: sqlite-vec, tree-sitter, huggingface_hub 등
├── models/                  # 오프라인 GGUF 임베딩 모델 저장 폴더 (자동 다운로드 됨)
└── scripts/                 # 에이전트가 터미널에서 직접 실행할 액션 스크립트
    ├── init_db.py           # [초기화] DB 폴더 생성 및 sqlite-vec 테이블 셋업
    ├── create.py            # [C] 인자: <file_path> | 파싱, 임베딩, DB 삽입
    ├── search.py            # [R] 인자: <query> | 쿼리 임베딩 및 하이브리드 검색
    ├── update.py            # [U] 인자: <file_path> | 기존 청크 삭제 후 재생성
    ├── delete.py            # [D] 인자: <file_path> | 특정 파일/경로의 데이터 삭제
    └── core/                # 공통 모듈 (DRY 원칙 준수)
        ├── db_client.py     # SQLite 커넥션 및 sqlite-vec 확장 로드
        ├── chunker.py       # tree-sitter 기반 AST 파싱/청킹 로직
        └── embedder.py      # llama-cpp-python 임베딩 추출 및 자동 다운로드 로직
```

## 2. 구성 요소 상세 (Component Details)

*   **`SKILL.md` (제어 타워)**: 에이전트의 진입점입니다. 에이전트는 사용자의 CRUD 요청을 분석한 뒤, `scripts/` 디렉토리 내의 적절한 파이썬 스크립트를 인자와 함께 호출하도록 설계되었습니다.
*   **`scripts/` (액션 모듈)**: 에이전트가 동적으로 코드를 생성하여 실행하는 대신, 사전 정의된 스크립트를 CLI 명령어로 호출합니다. 각 스크립트는 실행 결과를 표준 출력(`stdout`)으로 반환하여 에이전트의 컨텍스트로 제공합니다.
*   **`scripts/core/` (공통 모듈)**: 데이터베이스 커넥션 생성이나 무거운 임베딩 모델 로딩과 같은 반복 작업을 모듈화하여 성능과 유지보수성을 확보합니다.

## 3. 아키텍처 결정 사항 (Architectural Decisions)

본 스킬의 구현을 위해 다음과 같이 아키텍처 설계가 확정되었습니다.

1.  **스토리지 격리 수준: 전역 공유 (Global Scope)**
    *   사용자의 모든 프로젝트와 작업 환경에서 단일 지식베이스를 공유하여 활용합니다.
    *   **DB 파일 절대 경로**: `~/.pi/agent-memory/knowledge.db` (사용자 홈 디렉토리 하위의 고정된 위치를 사용합니다.)
2.  **CRUD 실행 인터페이스 (Execution Interface)**
    *   에이전트가 파이썬 코드를 즉석에서 작성하여 실행하는 방식을 엄격히 배제합니다.
    *   반드시 `scripts/` 폴더 내에 사전 구현된 파이썬 스크립트에 터미널 파라미터를 넘겨 실행(예: `python scripts/search.py "검색어"`)하는 방식을 표준으로 채택합니다.
3.  **임베딩 모델 관리: 자동 다운로드 (Auto-Download)**
    *   로컬 임베딩 연산을 위해 가벼운 GGUF 모델(예: Nomic-embed-text)을 사용합니다.
    *   `scripts/core/embedder.py` 또는 `init_db.py` 실행 시, 스킬 내 `models/` 폴더에 지정된 모델 파일이 존재하는지 검사합니다.
    *   파일이 없을 경우, `huggingface_hub` 라이브러리를 활용하여 원격 저장소에서 해당 모델을 자동으로 다운로드하는 로직을 필수로 구현해야 합니다.
