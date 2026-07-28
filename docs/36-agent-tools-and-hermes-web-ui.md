# Agent Tools And Hermes Web UI

Claude Code가 agent tooling, remote gateway, desktop app, embedded Web UI를
함께 다룰 때의 운영 가이드다. Hermes Agent Desktop과 Office/Claw3D
Web UI 점검에서 확인한 패턴을 기준으로 정리한다.

## 목적

Claude Code의 멀티 에이전트 도구는 작업 분해와 리뷰에 유용하지만, Hermes
같은 agent runtime은 다음 네 가지 layer가 동시에 엮인다.

| Layer | 대표 요소 | 확인 기준 |
|---|---|---|
| Agent runtime | Hermes Agent gateway | `doctor`, `status`, `/health` |
| Remote access | Tailscale, SSH tunnel | host alias, local/remote port |
| Web UI | Hermes Office, Claw3D | direct browser URL, `/office` route |
| Desktop shell | Electron app, webview | webview lifecycle, size, readiness |

브라우저에서 Web UI가 정상이어도 desktop app 내부 webview는 별도 실패 지점을
가질 수 있다. 원인을 “서버가 안 됨”으로 단정하지 말고 layer별로 분리한다.

## 진단 순서

1. `hermes doctor --fix`와 `hermes status`로 runtime 상태를 확인한다.
2. SSH/Tailscale alias와 tunnel health를 확인한다.
3. `http://localhost:<port>/office`를 일반 브라우저에서 확인한다.
4. Electron app 내부 webview의 URL, 크기, overlay 상태를 확인한다.
5. Start 직후 race와 hidden-tab `0x0` 로딩을 의심한다.
6. 필요할 때만 CDP를 켜고, 검증 후 일반 실행으로 되돌린다.

## Hermes Desktop / Office 체크리스트

| 항목 | 확인 |
|---|---|
| Gateway | local tunnel의 `/health`가 200인지 확인 |
| Adapter | `HERMES_API_URL`이 tunnel URL을 보는지 확인 |
| API key | config/env로만 전달하고 문서에는 원문 기록 금지 |
| Office server | `/office`가 200인지 확인 |
| Webview URL | root redirect가 아니라 `/office` 직접 로드 |
| Webview size | visible tab에서 non-zero width/height |
| Overlay | `dom-ready`/`did-finish-load` 후 overlay가 제거되는지 확인 |

## App 내부 blank의 흔한 원인

| 현상 | 원인 | 대응 |
|---|---|---|
| 브라우저 `/office`는 정상, app은 blank | Electron webview lifecycle 문제 | webview target, size, overlay를 확인 |
| app overlay가 계속 `Loading` | load event listener 누락 또는 너무 일찍 부착 | running/visible/url 변화를 listener effect에 포함 |
| `chrome-error://chromewebdata` | dev server readiness 전에 webview mount | main process가 `/office` ready 이후 success 반환 |
| hidden tab 진입 후 blank | webview가 숨겨진 탭에서 `0x0`으로 먼저 로드 | visible tab일 때만 mount |
| chat/agent 연결 실패 | adapter가 remote gateway가 아닌 local default를 봄 | SSH mode에서 tunnel URL과 key를 env/settings에 주입 |

## Claude Code 작업 분해 기준

Hermes Web UI 같은 cross-layer 문제는 subagent를 남발하지 않는다.

| 작업 | 권장 실행 |
|---|---|
| health/tunnel/process 확인 | main agent가 직접 처리 |
| Electron webview 원인 분석 | explorer 1명까지 허용 |
| renderer/main process 동시 수정 | 파일 영역이 분리될 때만 병렬화 |
| 최종 검증 | main agent가 직접 실행하고 screenshot/CDP 증거 확인 |

다음 조건이면 단일 실행으로 충분하다.

- 변경 파일이 1-3개다.
- webview lifecycle, env propagation, CSS 같은 한 흐름의 버그다.
- 다음 단계가 agent 결과에 막혀 있다.

## 검증 기준

최소 검증:

```bash
npm run typecheck
npm test -- tests/office-webview-url.test.ts tests/office-start.test.ts tests/office-env.test.ts
npm run build:unpack
```

Runtime 검증:

```bash
curl -sS -o /dev/null -w 'gateway=%{http_code}\n' \
  -H 'Authorization: Bearer <redacted>' \
  http://127.0.0.1:<tunnelPort>/health

curl -sS -o /dev/null -w 'office=%{http_code}\n' \
  http://127.0.0.1:3000/office
```

CDP는 임시 검증용이다.

```bash
ENABLE_CDP=1 CDP_PORT=9222 ./dist/mac-arm64/Hermes\ Agent.app/Contents/MacOS/Hermes\ Agent
curl http://127.0.0.1:9222/json/list
```

검증 후에는 CDP 없는 일반 app 실행으로 되돌린다.

## 문서화 기준

- API key, private key, raw `.env`, 사설 IP는 guide 문서에 남기지 않는다.
- host alias, port role, health endpoint, 검증 명령은 남긴다.
- `doctor --fix` 결과는 “자동 수정”, “manual intervention”, “optional dependency warning”으로 나눠 기록한다.
- 완료 브리핑은 app PID, tunnel PID, test/build 결과, 남은 uncommitted files를 포함한다.

## 관련 문서

- [관련 프로젝트](08-related-projects.md)
- [하네스 엔지니어링](29-harness-engineering.md)
- [서브에이전트 효율성](33-subagent-efficiency.md)
