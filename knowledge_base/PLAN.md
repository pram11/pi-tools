# Knowledge Base CRUD 스킬 구현 계획 (PLAN)

## 1단계: 기반 스토리지 및 인프라 셋업 ✅
- [x] SQLite 데이터베이스 파일 위치 정의 (`~/.pi/agent-memory/knowledge.db`).
- [x] `sqlite-vec` 가상 테이블 및 FTS5 하이브리드 검색을 위한 초기화 SQL 스크립트 작성.

## 2단계: 파싱 및 임베딩 파이프라인 ✅
- [x] `tree-sitter`를 이용한 AST 기반 논리적 코드 청킹 스크립트 작성.
- [x] `llama-cpp-python`과 GGUF 임베딩 모델(nomic-embed-text-v1.5 Q4) 연동 인터페이스 구현.

## 3단계: 지식 기반 CRUD 로직(Skill Scripts) 구현 ✅
- [x] **Create (등록)**: 파일 경로를 입력받아 청킹 후 임베딩하여 DB에 `INSERT`하는 스크립트.
- [x] **Read (조회)**: 검색 쿼리를 임베딩하여 코사인 유사도 기반으로 `SELECT`하는 하이브리드 검색 스크립트.
- [x] **Update (수정)**: 기존 파일 수정 시, DB 내 해당 파일 경로의 기존 청크를 삭제하고 재생성하는 로직.
- [x] **Delete (삭제)**: 특정 파일이나 디렉토리 경로에 해당하는 벡터/메타데이터를 `DELETE`하는 스크립트.

## 4단계: 테스트 및 에이전트 연동
- [x] `.pi/skills/knowledge-base/` 폴더 내 스킬 등록 및 로드 확인.
- [x] 터미널에서 CRUD 명령 테스트.
- [x] Git 동기화 (remote 설정 완료).
