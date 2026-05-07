#!/bin/bash
# install_skill.sh - Pi 에이전트 지식베이스 스킬 전역 배포용

# 1. 경로 정의
# pi-mono는 사용자의 홈 디렉토리 내 .pi/skills 폴더를 전역 스킬 저장소로 인식합니다.
LOCAL_SKILL_DIR="./.pi/skills/knowledge-base"
GLOBAL_SKILL_DIR="$HOME/.pi/skills/knowledge-base"

echo "🔍 지식베이스 스킬 배포를 시작합니다..."

# 2. 로컬 디렉토리 확인
if [ ! -d "$LOCAL_SKILL_DIR" ]; then
    echo "❌ 오류: 로컬 스킬 경로($LOCAL_SKILL_DIR)를 찾을 수 없습니다."
    echo "현재 위치가 프로젝트 루트인지 확인해 주세요."
    exit 1
fi

# 3. 전역 디렉토리 구조 준비
mkdir -p "$HOME/.pi/skills"

# 4. 기존 버전 제거 및 새 버전 복사
if [ -d "$GLOBAL_SKILL_DIR" ]; then
    echo "🔄 기존에 설치된 전역 스킬을 발견했습니다. 최신 버전으로 갱신합니다."
    rm -rf "$GLOBAL_SKILL_DIR"
fi

cp -r "$LOCAL_SKILL_DIR" "$HOME/.pi/skills/"
echo "✅ 파일 복사가 완료되었습니다: $GLOBAL_SKILL_DIR"

# 5. 실행 권한 부여 및 의존성 설치
# 에이전트가 스크립트를 직접 실행할 수 있도록 권한을 설정합니다.
chmod +x "$GLOBAL_SKILL_DIR/scripts/"*.py 2>/dev/null || true

if [ -f "$GLOBAL_SKILL_DIR/requirements.txt" ]; then
    echo "📦 필요한 파이썬 의존성 패키지를 설치합니다..."
    pip install -r "$GLOBAL_SKILL_DIR/requirements.txt" --quiet
fi

echo "🚀 전역 배포가 완료되었습니다!"
echo "이제 어느 작업 디렉토리에서든 'knowledge-base' 스킬을 호출할 수 있습니다."
