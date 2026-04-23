# Permission 결정 트리

## 개요

Claude Code는 도구 실행 전 권한을 확인합니다. 어떤 모드에서 실행 중인지, 어떤 도구가 호출되는지에 따라
자동 승인, ML 분류, 또는 사용자 프롬프트 중 하나를 선택합니다.

---

## 1. 5가지 Permission 모드

| 모드 | 설명 | 적합 상황 |
|------|------|----------|
| `bypass` | 모든 도구 실행 승인, 권한 확인 없음 | 완전히 신뢰된 자동화 환경 |
| `auto` | 안전 화이트리스트 → ML 분류기 자동 판단 | 일반 개발 작업 |
| `default` | 새 도구 첫 실행 시 사용자에게 묻고 기억 | 기본값 |
| `plan` | 실행 전 전체 계획을 사용자에게 제시 후 일괄 승인 | 복잡한 멀티스텝 작업 |
| `dontAsk` | 현재 세션에서 동일 도구 재확인 생략 | 반복 작업 세션 |

### 모드 설정 방법

CLI 플래그:
```bash
claude --permission-mode auto
claude --permission-mode bypass   # 완전 자동화 시
claude --permission-mode plan     # 계획 검토 후 실행
```

`settings.json`:
```json
{
  "permissionMode": "auto"
}
```

에이전트 frontmatter:
```yaml
permissionMode: bypass   # 해당 에이전트만 bypass
```

---

## 2. Auto 모드 결정 흐름

`auto` 모드는 2단계로 도구 실행 여부를 결정합니다.

```
도구 실행 요청 (auto 모드)
    │
    ▼
1단계: 안전 화이트리스트 확인
    │
    ├─ 화이트리스트 해당 → 즉시 승인 (예: Read, Grep, Glob)
    │
    └─ 화이트리스트 미해당
            │
            ▼
    2단계: Haiku ML 분류기 실행 (YOLO 모드)
            │
            ├─ 안전 판정 → 자동 승인
            └─ 위험 판정 → 사용자 확인 요청
```

> YOLO: "You Only Live Once" — 위험도가 낮다고 판단되면 확인 없이 실행하는 적극적 자동화 모드.
> ML 분류기로 Haiku 모델을 사용하므로 비용이 매우 낮습니다.

### 안전 화이트리스트 (자동 승인 도구)

- `Read` - 파일 읽기
- `Grep` - 패턴 검색
- `Glob` - 파일 탐색
- `WebSearch` - 웹 검색 (읽기 전용)
- `WebFetch` - URL 가져오기 (읽기 전용)
- `ToolSearch` - 도구 검색

---

## 3. 연속 거부 시 인터랙티브 폴백

자동 모드에서 사용자가 연속으로 도구 실행을 거부하면 자동 판단을 중단하고 사용자에게 직접 묻습니다.

```
60초 이내에 3번 연속 거부 감지
    │
    ▼
인터랙티브 폴백 활성화
    │
    ▼
이후 모든 비화이트리스트 도구 → 사용자 확인 요청
(세션 종료 또는 명시적 재설정까지 유지)
```

이 메커니즘은 사용자의 의도치 않은 연속 거부(예: 실수로 연속 클릭)를 감지하여
자동화가 잘못된 방향으로 진행하는 것을 방지합니다.

---

## 4. Bash 도구 특별 처리: AST 파싱

Bash 명령은 다른 도구와 달리 **Tree-sitter AST(Abstract Syntax Tree) 파싱**을 수행합니다.

### 파싱 목적

1. **커맨드 인젝션 감지**: 사용자 입력이 쉘 커맨드에 삽입되는 패턴 탐지
2. **서브커맨드 추출**: 명령에 포함된 서브커맨드 목록화
3. **위험 패턴 식별**: `rm -rf`, `curl | bash`, `eval` 등 고위험 패턴

### 서브커맨드 분석 한도

```
최대 서브커맨드 분석 수: 50개
```

파이프(`|`), 서브쉘(`$()`), 세미콜론(`;`), AND(`&&`), OR(`||`)로 연결된 명령을 개별 파싱합니다.
50개를 초과하면 전체 명령을 단일 위험 명령으로 분류하여 사용자 확인을 요청합니다.

### 인젝션 감지 예시

```bash
# 안전: 정적 커맨드
ls -la /tmp

# 위험: 변수 인젝션 패턴
rm -rf "$USER_INPUT"

# 위험: eval 사용
eval "$DYNAMIC_COMMAND"

# 경고: 외부 스크립트 실행
curl https://example.com/script.sh | bash
```

---

## 5. settings.json 권한 설정 예시

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git *)",
      "Read(*)",
      "Write(src/**)",
      "Edit(src/**)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl * | bash)",
      "Write(.env*)",
      "Write(**/*.key)"
    ],
    "ask": [
      "Bash(docker *)",
      "Bash(sudo *)",
      "Write(/etc/**)"
    ]
  }
}
```

### 패턴 문법

| 패턴 | 의미 |
|------|------|
| `Tool(*)` | 해당 도구의 모든 호출 |
| `Bash(npm *)` | `npm`으로 시작하는 모든 Bash 명령 |
| `Write(src/**)` | `src/` 하위 모든 경로에 대한 Write |
| `Read(.env*)` | `.env`로 시작하는 파일 읽기 거부 |

`allow` > `deny` > `ask` 순서로 우선순위가 적용됩니다.
(`deny`가 `allow`보다 우선합니다.)

---

## 6. Hook `if` 조건을 활용한 세밀한 제어

`settings.json`의 Hook 시스템에서 `if` 조건을 사용하면 특정 상황에서만 권한 검사를 수행할 수 있습니다.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "if": "tool_input.command.startsWith('rm')",
        "hooks": [
          {
            "type": "command",
            "command": "echo '위험: rm 명령 감지됨' && exit 1"
          }
        ]
      },
      {
        "matcher": "Write",
        "if": "tool_input.file_path.includes('.env')",
        "hooks": [
          {
            "type": "command",
            "command": "echo '.env 파일 수정 차단됨' && exit 1"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "if": "tool_response.exit_code !== 0",
        "hooks": [
          {
            "type": "command",
            "command": "logger -t claude-code 'Bash 실행 실패'"
          }
        ]
      }
    ]
  }
}
```

### `if` 조건에서 사용 가능한 변수

| 변수 | PreToolUse | PostToolUse | 설명 |
|------|-----------|------------|------|
| `tool_name` | O | O | 도구 이름 (`"Bash"`, `"Write"` 등) |
| `tool_input` | O | O | 도구 입력 파라미터 객체 |
| `tool_response` | X | O | 도구 실행 결과 객체 |

---

## 7. Permission 결정 트리 전체

```
도구 실행 요청
    │
    ▼
settings.json deny 패턴 확인
    │
    ├─ deny 매칭 → 즉시 차단
    │
    └─ deny 미매칭
            │
            ▼
    settings.json allow 패턴 확인
            │
            ├─ allow 매칭 → 즉시 승인
            │
            └─ allow 미매칭
                    │
                    ▼
            현재 Permission 모드 확인
                    │
                    ├─ bypass → 즉시 승인
                    │
                    ├─ auto → 안전 화이트리스트?
                    │           ├─ 예 → 즉시 승인
                    │           └─ 아니오 → Haiku ML 분류 → 안전? → 승인/확인
                    │
                    ├─ default → 첫 실행? → 사용자 확인 후 기억
                    │
                    ├─ plan → 계획 단계에서 일괄 확인
                    │
                    └─ dontAsk → 세션 내 기억된 결정 적용
```

---

## 관련 문서

- [Settings 전체 스키마](20-settings-schema-reference.md) - `permissions` 필드 전체 옵션
- [Agent Frontmatter 스키마](22-agent-frontmatter-schema.md) - 에이전트별 `permissionMode` 설정
- [환경변수 레퍼런스](17-environment-variables.md) - 권한 관련 환경변수
