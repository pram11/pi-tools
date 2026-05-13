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

---

## 5단계: Rust 마이그레이션 계획 ✅

### 목표
Python 스크립트를 **단일 Rust 바이너리**로 대체. `cmake`/C++ 컴파일 없이 **동적 링크** 방식으로 구축.

### 라이브러리 전략: `libllama.so` (Pre-built)
- **출처**: `https://github.com/ggml-org/llama.cpp/releases/tag/b9128`
- **파일을 다운로드 및 추출**: `llama-b9128-bin-ubuntu-x64.tar.gz` → `libllama.so`
- **저장 위치**: 스킬 디렉토리 내부 `bin/` 폴더.
- **동적 링크**: Rust 빌드 시 `LLAMA_LIB_DIR=./bin` 환경 변수로 연결.

### 프로젝트 구조
```
knowledge-base/
├── bin/
│   └── libllama.so              # Pre-built binary (install 시 다운로드)
├── Cargo.toml
├── src/
│   ├── main.rs                  # Clap CLI entry
│   ├── cli.rs                   # Subcommand definitions
│   ├── db.rs                    # Rusqlite + sqlite-vec
│   ├── chunker.rs               # Tree-sitter AST parsing
│   └── embedder.rs              # llama-cpp-rs wrapper
└── install_skill.sh             # Binary download logic 추가
```

### Phase 1: Scaffold & SQLite ✅
- **Rusqlite**: `rusqlite` + `bundled` feature.
- **sqlite-vec**: `sqlite3_auto_extension` FFI 또는 crate.
- **CLI**: `clap` (Init, Create, Search, Update, Delete).

### Phase 2: Chunking (Tree-sitter) ✅
- **Crate**: `tree-sitter` + per-lang crates (py, js, ts, rust, go).
- **Logic**: Python 로직 1:1 포트 (AST node 수집, fallback line-chunking).

### Phase 3: Embedding (llama-cpp-rs) ✅
- **Crate**: `llama-cpp-2 = { features = ["dynamic-link"] }`
- **Model**: 동일 (`nomic-embed-text-v1.5 Q4_K_M`).
- **Implementation**: `Llama::load_from_file` → `Context::new` → Embedding generation.
- **Normalization**: Manual f32 L2 norm (no numpy).
- **Bugfix**: `n_ubatch` default(512) → `MAX_CTX(2048)`, token truncation safety.

### Phase 4: CRUD ✅
- Python 로직 동일하게 포트. `INSERT OR REPLACE`, `DELETE`, Hybrid Search (vec + fts5).

### Phase 5: Build & Deploy ✅
- **Build**: `LLAMA_LIB_DIR=./bin cargo build --release`
- **Binary**: `target/release/knowledge-base` → `bin/knowledge-base`
- **CRUD verified**: init→create→search→delete all working.
- **SKILL.md Update**: pending (Python cmds → `./bin/knowledge-base`)

### Risk & Mitigation
| Risk | Mitigation |
|---|---|
| `libllama.so` ABI mismatch | Specific commit hash (`b9128`) pinned |
| Dynamic load failure | `LD_LIBRARY_PATH` 설정 또는 `rpath` 사용 |
| Tree-sitter Rust API | Python 1:1 로직 유지 |
| n_ubatch < n_tokens crash | ✅ Fixed: `MAX_CTX=2048`, token truncation |

### Estimate
- **Total**: 12-18 hrs
- **Build Time**: < 1 min (No C++ compile)

---

## 6단계: Remaining
- [ ] SKILL.md update (Python → Rust binary commands)
- [ ] Suppress llama.cpp verbose logging
- [ ] Embedding context reuse (create once, batch all chunks)
- [ ] Add `rpath` to binary (eliminate `LD_LIBRARY_PATH` requirement)
