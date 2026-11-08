# 1.4.0 — 2026-11-06

- Optional DirectML image backend, separate GUI backend/adapter controls and opt-in install action. CPU default; LFM3 device selection independent.
- Image GPU packages installed in app-local .venv-image, leaving CPU ONNX/PyTorch .venv unchanged; same pinned Tiny-SD model files, shared/reusable wheelhouse, local-first dependency resolution and offline setup support.
- One-shot isolated GPU process relays image progress; DirectML sequential/no-memory-pattern configuration and provider-presence checks. On failure explicit logged CPU retry and fallback metadata.
- CLI -image-backend cpu|directml / -image-gpu 0..31; Setup.ps1 -ImageGpuOnly; MCP chat follows image settings. No GPU package download in default setup.
- PNG metadata includes configured providers, adapter and generation duration; does not imply every operator executes on GPU.
- User v1.3.1 output confirms ONNX CPU image backend and successful CUDA-enabled core setup; user confirms corrected speech. Speech path unchanged.
- 99 backend tests, 46 C# assertions and PowerShell checks; Windows-x64 rebuilt. Native DirectML/device execution and target UI/performance untested here.

# 1.3.1 — 2026-11-06

- Deterministic German/English speech-only measurement verbalization before sentence/chunk splitting; numbers, decimal digits, signs, shared-unit ranges, Celsius/Fahrenheit, percentages, wind, precipitation and pressure.
- Remove Markdown presentation markers, expand max/min near measurements, approximation/comparison signs and German fog/rain chance labels. Other languages only receive typography cleanup.
- Preserve displayed/raw answers, tool data and histories; apply at the common audio rendering boundary for generated and explicit TTS input. No dependency/model changes.
- Versioned audio manifest now records source_text, prepared_text and preparation revision alongside actual spoken fragment texts.
- 85 backend tests and 40 C# CLI/persistence/display assertions passed; Windows-x64 application rebuilt. No native Windows or real-model listening validation here.

# 1.3.0 — 2026-11-06

- Default-on GUI option to hide URL/file destinations while retaining captions, raw archived transcripts and model history; immediate reversible rendering, export follows current display.
- Weather enabled by default for new settings/CLI; explicit disable remains available. Web/wiki/MCP defaults unchanged.
- Fetch three recent past days alongside forecasts; cache per-location reports for up to three retrieval days/72h with dates, units and attribution.
- On network/TLS/provider failure or offline mode, return explicit unavailable status plus recent matching historical data; never label stale forecasts as live. Add app-owned offline/cache-date transcript notice and model instructions for uncertain estimates only.
- Independent offline-mode setting/CLI flag blocks online tools and missing-model downloads; weather can still read its cache.
- Reuse weather cache JSON from predecessor releases without modifying sources.
- 70 backend, 40 CLI/persistence/display checks, PowerShell syntax/arguments and reuse tests passed. Windows app rebuilt; actual UI/model response quality not evaluated here. No dependencies/model changes.

# 1.2.0 — 2026-11-06

- Persistent left-hand chat list and visible New Chat action; independent serialized model histories, transcript/draft/media restoration, atomic JSON saves under output/chats.
- Short independent speech calls, fragment WAVs/manifest when saving is enabled, bounded RMS level matching, silence gaps/fades and final peak ceiling. Audio frame budget independent of text token setting.
- Hide obsolete tool-access refusals from model context when the corresponding tool is now available; remove matching contradictory current refusals after successful tool calls without rewriting the visible old transcript.
- Reinforce multi-tool chains; verify two sequential dispatched tools and chat history isolation in regressions.
- Fix remaining attachment Remove button row height and default button dimensions, normalize button-caption whitespace and log additional controls.
- Version/type/timestamp headers for app logs and worker sessions; versioned speech manifest.
- 58 backend and 31 CLI/persistence checks passed. Windows app rebuilt; target UI and actual LFM3 listening test remain outstanding. Dependencies/models unchanged.

# 1.1.5 — 2026-11-06

- Prepare generated speech separately: preserve Markdown link/image labels, omit URLs and local file destinations (including quoted paths, spaces, parentheses and exact generated image locations).
- Apply before TTS with or without tools; preserve display/history/export text. Translate cleaned speech when needed and clean translation again. Explicit task=tts remains verbatim input reading.
- Add seven speech regressions, including real worker request capture with fake inference/audio codec for chat, ASR and translation. 50 backend tests and 25 CLI assertions passed.
- Republished framework-dependent Windows x64 executable using .NET SDK. No dependency/model changes.
- User confirms 1.1.4 fresh Windows setup and image/speech operation; supplied log confirms full Mini ZIM download and embedded checksum validation. New real LFM3 speech behavior still needs target-system listening verification.

# 1.1.4 — 2026-11-05

- Explicit verified HTTPS contexts: Windows native truststore plus certifi; default system trust plus certifi elsewhere. Apply to Kiwix catalog/HEAD/ZIM requests, Tiny-SD downloads and opt-in online text/weather tools. No verification bypass or global SSL injection.
- Declare certifi/truststore explicitly; keep application-private venv and wheel reuse.
- Details button opens a resizable themed exception window with copy/open-log/close actions instead of merely selecting the existing log tab.
- Document fresh version-folder installation with retained source assets, new own venv and no deletion of predecessor/source data.
- Optional Wikipedia setup retries once, then warns and continues core setup. Missing/invalid offline archives hide corresponding model tools automatically; preserved valid archives remain usable.
- Add independent opt-in online Wikipedia lookup/read tools via fixed de/en MediaWiki endpoints, GUI toggle, CLI -wiki-online and MCP permission checks.
- 43 backend tests and 25 CLI assertions passed including actual local TLS rejection/acceptance/hostname checks; Windows sources/apphost rebuilt. Native Windows runtime/UI not executed here.

# 1.1.3 — 2026-11-05

- Fix incremental wheel collection for PEP 508 environment markers such as the user's missing MCP pydantic dependency. Parse complete requirements using pip's bundled packaging parser; retain name/extras/version bounds, reject direct URLs, fetch only the missing package.
- Give error-banner Details button explicit DPI/font-aware size, a full-height table row and matching banner height/column width; include it in UI layout diagnostics.
- 34 backend tests pass including the exact user log, invalid URL/requirement cases and actual pip resolution of a conditional missing dependency with controlled wheel delivery.
- Recompiled Windows app; full Windows install and visual banner verification not run here. No requirements/model changes.

# 1.1.2 — 2026-11-05

- Theme-colored animated tile indicator and dedicated image progress panel in Chat, independent from the general model status bar.
- Indeterminate model loading, prompt encoding, decoding and saving; actual sampler steps and percent during denoising, starting at zero.
- Keep completed image state visible while the model continues text/speech; stop animation on image failure/cancellation and reset on next operation.
- Recompiled Windows app. 31 backend tests passed; native Windows UI not run. No dependency/model changes.

# 1.1.1 — 2026-11-05

- Read/write Tiny-SD text assets with explicit UTF-8. Both real tokenizer files fail CP1252 decoding; prior OS-default decoding could prevent image generation on Windows.
- Show actual tool failures in GUI conversation and CLI stderr; log tool arguments and full Python traceback.
- Instruct model to report tool errors and only announce a retry when issuing a corrected call.
- 31 backend tests passed including simulated CP1252 defaults and failed-image diagnostics. Real Tiny-SD CPU inference produced a 256×384 PNG with two steps. Windows C# rebuilt; native Windows execution not performed.
- No requirements or model changes relative to 1.1.0.

# 1.1.0 — 2026-11-05

- Default German Wikipedia Mini ZIM download; optional full nopic edition in Settings, existing-file picker, direct libzim lookup/read, same-model automatic factual lookup, separate source display.
- Resume ZIM downloads, validate new archive checksums once, reuse one predecessor archive without unpacking or duplicating search indexes.
- Add independent opt-in web search/page reading and Open-Meteo current weather/forecast tools. CLI requires explicit online flags every invocation.
- Add opt-in MCP stdio server, per-call permission checks, client configuration export and -mcp / -mcp-config entry points. No listening port.
- Add GUI/localized settings and CLI help; preserve native WinForms button rendering from 1.0.4.
- New dependencies installed only in application .venv with incremental wheel reuse.
- User confirmed working chat/speech before this release. New verification: 29 Python tests, 22 CLI assertions, PowerShell argument/syntax and predecessor-reuse suites; Windows GUI not executed here.

# 1.0.4 — 2026-11-05

- Remove custom button painting entirely; use standard WinForms caption rendering and centering.
- Remove AutoSize plus Dock.Fill from toolbar buttons. Give each button an explicit DPI-scaled height and measured caption width; constrain toolbar rows to their parent's fixed height.
- Add theme-colored vector icons and shorter button captions. Icons are rendered by standard WinForms Button.Image, with no icon-font dependency or extra downloads.
- Keep disabled native button text readable with lighter themed backgrounds.
- Write actual toolbar/control dimensions to output/logs/ui-layout.log on show/resize for target-system diagnosis.
- User's 1.0.3 screenshot disproves the earlier assumption that switching GDI to GDI+ alone solved the blank captions. This release changes layout constraints and native painting. It compiles here; actual Windows rendering is still not confirmed.

# 1.0.3 — 2026-11-05

- Bounded discovery of direct and nested sibling Lfm3Desk releases before model/package downloads; optional explicit -ReuseFrom source.
- Reuse predecessor model, wheelhouse and tool files directly in canonical target directories; preserve existing target files and do not copy .venv or user settings.
- Recreate private venv at new location; resolve complete local wheel sets without a network index, fetch only individually missing requirements and stop on dependency conflicts rather than broad updates.
- Disable extra pip caching for package collection/install. Reuse predecessor .NET runtime only if an installed/current runtime is unavailable.
- Add predecessor-copy and local pip-resolution regression tests and shared installer policy documentation. Windows app version rebuilt; full native Windows install still not executed here.

# 1.0.2 — 2026-11-05

- Replace custom button caption rendering with GDI+ DrawString on the same graphics surface used for the background/border; explicitly invalidate on caption changes and enable buffered user painting. This addresses the user's blank-button screenshot in 1.0.1.
- Draw literal ampersands in tab titles/choices and disable or escape mnemonic processing for labels, buttons, checkboxes and group titles. "Einrichtung & Protokoll" no longer consumes the ampersand as a keyboard mnemonic.
- Recompiled Windows host and managed assembly. C# compile passed; actual Windows rendering remains to be confirmed. Installation logic and dependency requirements are unchanged from 1.0.1.

# 1.0.1 — 2026-11-05

- Fixed the reported PowerShell-5.1-style Python probe failure: file-based probe, explicit Windows native argument quoting, stdout/stderr separation and nonfatal candidate failures.
- Shared GUI/CLI setup runner with streamed logs, real exit-code/error-tail reporting and cancellation. Setup can be cancelled from its own tab.
- Strict app-local Python 3.12 x64 `.venv` verification; doctor and worker reject foreign environments. Pip operations remain tied to `.venv/Scripts/python.exe`.
- Rebuilt GUI around File/Model/View/Help menus and Chat/Settings/Setup tabs. Fixed label/control grids, grouped settings, labeled conversation/input/media, translated task/output/voice choices and readable disabled buttons.
- Versioned Windows host rebuilt. Added native process/probe regression checks and actual private-venv tests. See VALIDATION_1.0.1.md for limits.

# 1.0.0 — 2026-11-05

Initial C# WinForms / command-line release. Local official LFM3 Omni Transformers worker; text/image/audio/video inputs; text/model speech outputs; male/female voice controls; independent input/text/speech languages; ASR, translation and literal TTS tasks; bounded offline tools; audio persistence/playback controls; microphone capture; cancellation; EN/DE labels; eight themes; repeatable setup, wheelhouse and self-contained Windows publish script. Same pinned TinySDDesk 434.4 MiB INT8/ONNX image model downloaded at setup; generate_image tool, CPU image inference, GUI preview and PNG/JSON output. Precompiled framework-dependent Windows-x64 host and managed assembly included. See VALIDATION.md for tested and untested paths.
