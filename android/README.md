# SafeShop Android app

Android companion for SafeShop. It keeps ordering inside your shopping app (for example
BigBasket) and surfaces the SafeShop health score in-context through two capture modes,
both of which reuse the existing FastAPI scoring backend:

- Live camera scan: point at a product's ingredients / nutrition panel. On-device OCR
  (Google ML Kit) reads the text and the backend scores it.
- Screen overlay: a floating bubble sits on top of any app. Open a product in your
  shopping app, tap the bubble, and it screen-captures the current screen, OCRs it, and
  shows the score card. You dismiss it and keep ordering in that app.

The phone never structures the text itself. It sends the raw OCR blob to
`POST /analyze_text`, and the backend splits ingredient vs nutrition sections and scores it.

## Prerequisites

- Android Studio (Koala or newer) or the Android command-line SDK.
- JDK 17+.
- A device or emulator running Android 8.0 (API 26) or newer.
- The SafeShop backend running locally (from the repo root):
  `.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`

## Point the app at the backend

The backend URL is editable at runtime on the app's home screen (persisted), defaulting to
`BuildConfig.BASE_URL` = `http://127.0.0.1:8000/`. Pick whichever connection fits:

### Option A - WiFi (no cable)

1. Start the backend bound to all interfaces:
   `.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000`
2. Find your computer's LAN IP (e.g. `192.168.1.5`): `ipconfig` (Windows) / `ifconfig` or
   `ip addr` (macOS/Linux).
3. Put the phone on the same WiFi network as the computer.
4. In the app's "Backend connection" field, enter `http://<your-computer-ip>:8000` and tap Save.

The debug build permits cleartext HTTP to any host (see
[res/xml/network_security_config.xml](app/src/main/res/xml/network_security_config.xml)), so a
plain `http://` LAN IP works. If it can't connect, allow port 8000 through your computer's firewall.

### Option B - USB (adb reverse)

Keep the default `http://127.0.0.1:8000/` and forward the port over USB:

```bash
adb reverse tcp:8000 tcp:8000
```

(For the standard emulator you can instead use `http://10.0.2.2:8000/`. Later, point it at a
hosted HTTPS URL.)

## Build and install

```bash
cd android
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## Permissions the app requests

- Camera - for the live scan mode.
- Display over other apps (overlay) - for the floating bubble.
- Screen capture (MediaProjection) - granted per session when you first tap the bubble.
- Notifications - for the foreground-service notification shown during a capture.

## Notes

- Cleartext HTTP is allowed only for `127.0.0.1`, `10.0.2.2`, and `localhost` via
  [res/xml/network_security_config.xml](app/src/main/res/xml/network_security_config.xml);
  a production build should use HTTPS to a hosted backend.
- Passive auto-detection of product screens (AccessibilityService) is intentionally not
  included in this version; the overlay is tap-to-scan to stay reliable and reduce policy risk.
