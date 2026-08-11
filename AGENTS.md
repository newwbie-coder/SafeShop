# AGENTS.md

## Cursor Cloud specific instructions

SafeShop has three surfaces:
- Backend: FastAPI rule-based food scorer (`backend/`). Main runnable/testable surface.
- Browser extension: `extension/` (Chrome, injects a score card on BigBasket pages).
- Android app: `android/` (Kotlin/Compose companion; camera OCR + screen-overlay tap-to-scan).

### Backend
- Run (dev): `.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`.
- Endpoints: `POST /analyze` ({name, ingredients, nutrition_text}) and `POST /analyze_text`
  ({name, raw_text}); the latter is what the Android app calls with a raw OCR blob. Both share
  `score_product(...)` in `backend/main.py`.
- Tests: run as `.venv/bin/python -m pytest` (NOT the bare `pytest` binary) so the repo root is
  on `sys.path`; otherwise collection fails with `No module named 'backend'`.
- There is no linter configured.

### Android app (`android/`)
- Build tooling is NOT installed by the startup update script. To build in a fresh cloud VM,
  install the Android SDK once (JDK 17+ is already present):
  - Download Android command-line tools, then:
    `sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"` (accept licenses).
  - Point the project at the SDK: create `android/local.properties` with `sdk.dir=<ANDROID_HOME>`
    (this file is gitignored).
- Build a debug APK: `cd android && ./gradlew :app:assembleDebug`
  (output: `app/build/outputs/apk/debug/app-debug.apk`). The Gradle wrapper is committed.
- The app targets `BuildConfig.BASE_URL` (default `http://127.0.0.1:8000/`). For a device/emulator
  to reach a locally running backend, run `adb reverse tcp:8000 tcp:8000`. Cleartext is allowed only
  for localhost/10.0.2.2 via `res/xml/network_security_config.xml`.

### Cloud constraint: no Android emulator
- Cloud VMs have no `/dev/kvm`, so the Android emulator cannot boot here. Do NOT try to run the app
  in an emulator in the cloud. Verify the app by building the debug APK (compile/package check) and
  by exercising the backend contract (`POST /analyze_text`) directly; run the actual GUI on a
  physical device (`./gradlew installDebug` with `adb reverse` and the backend running).
