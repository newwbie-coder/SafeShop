# Deploying the SafeShop backend (for live user testing)

For real user testing you want the API on a persistent public HTTPS URL, so testers just
install the APK and scan - no laptop, no `adb`, no same-WiFi requirement.

The API is tiny (only `fastapi` + `uvicorn` + `pydantic`; see [deploy/requirements.txt](deploy/requirements.txt))
and ships with a [Dockerfile](Dockerfile), so any container host works.

## Option 1: Render (free, recommended to start)

1. Push this repo to GitHub (already done).
2. Go to https://render.com -> New + -> Blueprint, and select this repository.
   Render reads [render.yaml](render.yaml) and builds the [Dockerfile](Dockerfile).
   (Or: New + -> Web Service -> pick the repo -> Runtime "Docker" -> Plan "Free".)
3. Deploy. You get a URL like `https://safeshop-backend.onrender.com`.
4. Smoke-test it:
   ```bash
   curl https://safeshop-backend.onrender.com/
   curl -X POST https://safeshop-backend.onrender.com/analyze_text \
     -H "Content-Type: application/json" \
     -d '{"name":"test","raw_text":"Ingredients: Sugar, Palm Oil. NUTRITION Energy 500 kcal Sugars 30 g Sodium 700 mg"}'
   ```

Note: the free plan sleeps after inactivity, so the first request after idle can take
~30-60s to wake. Fine for testing; use a paid instance for always-on.

Other hosts that use the same Dockerfile: Railway, Fly.io, Google Cloud Run.

## Point the Android app at the hosted URL

Two ways (the URL is HTTPS, so no cleartext config is needed):

- Per-tester, no rebuild: open the app -> "Backend connection" -> paste the URL -> Save.
- Baked-in tester APK (nicer for handing out): build with the URL compiled in:
  ```bash
  cd android
  ./gradlew assembleDebug -PsafeshopBackendUrl=https://safeshop-backend.onrender.com
  # -> app/build/outputs/apk/debug/app-debug.apk
  ```

## Run the container locally (optional sanity check)

```bash
docker build -t safeshop-backend .
docker run --rm -p 8000:8000 safeshop-backend
curl http://127.0.0.1:8000/
```
