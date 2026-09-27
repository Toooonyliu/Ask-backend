# Ask backend — CMU 15-113 HW4

Ask (速问) is my bilingual Xiao Liu Ren learning and reflection project. HW3 called the Hong Kong Observatory calendar API directly from the browser and calculated readings in JavaScript. HW4 moves the calendar request, input validation, and personal-reading calculation to this Python/Flask backend. The existing frontend displays the response and animates the three counting stages.

Frontend: https://toooonyliu.github.io/projects/xiaoliuren/

Frontend repository: https://github.com/Toooonyliu/toooonyliu.github.io

Backend repository: https://github.com/Toooonyliu/Ask-backend

**Backend deployment:** https://ask-backend-s507.onrender.com

Health check: https://ask-backend-s507.onrender.com/health

Live reading, invalid-input responses, and CORS headers were verified on September 27, 2026. The frontend integration is configured for this URL.

## What runs where

```text
GitHub Pages browser → Ask backend on Render → Hong Kong Observatory
                    ← lunar date + calculation + animation stages
```

The frontend sends only a date, local clock time, and IANA time zone to the reading endpoint. Question text, account tokens, and history are not sent to this backend. Topic matching and written reflections remain in the frontend; this is not an AI interpretation service. Existing Google login and account history continue through Supabase, while guest history stays in localStorage.

## Endpoints

| Method and path | Input | Response |
| --- | --- | --- |
| `GET /` | None | Service name and endpoint list |
| `GET /health` | None | `{"status":"ok","service":"ask-backend"}` |
| `GET /api/calendar?date=2026-09-27` | Gregorian date, `YYYY-MM-DD` | Parsed lunar month, day, leap flag, original text/year, requested date |
| `POST /api/reading` | JSON `date`, `clock`, `timeZone` | Input fields, lunar date, traditional hour, three palace positions, sign, and animation stages |

Example input:

```json
{"date":"2026-09-27","clock":"09:30","timeZone":"America/New_York"}
```

The live upstream lookup for that example returns 八月十七. The reading returns `hourIndex: 6`, `monthPalace: 1`, `dayPalace: 5`, `timePalace: 4`, and `sign: "小吉"`. Positions are zero-based in this order: 大安, 留连, 速喜, 赤口, 小吉, 空亡. Each stage contains `start`, `count`, and `end` for the existing hand animation.

Errors also return JSON:

```json
{"error":{"code":"date","message":"That calendar date does not exist."}}
```

Invalid input returns HTTP 400, malformed/unsupported request bodies return 400/413/415, upstream failures return 502, and upstream timeouts return 504. Successful calendar lookups are cached in memory (up to 512 dates); failures are retryable and are not cached. Simultaneous cache misses can make separate upstream calls. Cache state resets when the service restarts.

## Run locally

Use Python 3.9 or newer; Python 3.12 is configured for Render.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The backend listens at http://127.0.0.1:5050. Leave this terminal running.

```sh
curl http://127.0.0.1:5050/health
curl -X POST http://127.0.0.1:5050/api/reading \
  -H 'Content-Type: application/json' \
  -d '{"date":"2026-09-27","clock":"09:30","timeZone":"America/New_York"}'
```

In a second terminal, from the frontend repository:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173/projects/xiaoliuren/. `backend-config.js` automatically selects the local backend on localhost/127.0.0.1. Other hosts use `DEPLOYED_BACKEND_URL`; configure that value before publishing.

## Frontend communication

`backend-api.js` wraps browser `fetch()`. Page arrival and date changes call `/api/calendar`; clicking Begin calls `/api/reading`. The frontend checks the response shape, uses the returned stages for the hand animation, and uses the returned final position to choose the existing written reflection. It displays bilingual errors and lets the user retry. Requests allow 75 seconds for an idle Render service to wake up. It never substitutes a locally computed reading when the backend fails. Existing saved readings can still be reopened, and the Method page keeps its local teaching examples.

## Configuration and secrets

No calendar API key, paid AI key, or database credential is required by this backend. `PORT` selects the local server port (default 5050). `ALLOWED_ORIGINS` is a comma-separated browser origin allowlist. The local default includes the portfolio and localhost:4173; Render is configured for `https://toooonyliu.github.io` only.

This is a public, read-only calculation service without user authentication. CORS permits the portfolio to read browser responses; it does not prevent non-browser clients from calling public endpoints. Requests are limited to 4 KB, fields and date/time ranges are validated, and the upstream URL is fixed. There is no paid API call or server-side history storage. Standard hosting/access logs may contain connection metadata; do not add request-body logging.

If secrets are introduced later, store them as Render environment variables and local shell variables, never in GitHub or frontend code. `.env` is ignored. `.env.example` documents public settings; the app does not automatically load `.env` files.

## Deploy to Render

1. Create a new public GitHub repository containing this folder's files, with `app.py` at the repository root. Do not upload `.venv` or `.env`.
2. In Render, create a **Web Service**, connect the backend repository, and choose the free instance.
3. Runtime: Python 3. Build: `pip install -r requirements.txt`.
4. Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30`.
5. Set `PYTHON_VERSION=3.12.8`, `ALLOWED_ORIGINS=https://toooonyliu.github.io`, and health check `/health`. Render supplies `PORT`.
6. Deploy. Open the assigned URL plus `/health` and verify `status: ok`.
7. Paste the exact assigned base URL into the frontend's `DEPLOYED_BACKEND_URL`, then publish the frontend changes.
8. Test the public frontend, including a new question, empty input, and a backend failure. Replace the deployment-status paragraph above with the verified backend URL.

`render.yaml` also provides the same configuration for a Render Blueprint deployment. Use either the manual Web Service setup or the Blueprint, not both.

Official deployment guide: https://render.com/docs/deploy-flask

## Calculation conventions

Inclusive counts match HW3: `(month-1)%6`, `(monthPalace+day-1)%6`, `(dayPalace+hourIndex-1)%6`. Civil dates change at midnight, so 23:00 retains the current date but uses 子时. Leap months retain their month number. Spring DST gaps are rejected; repeated autumn hours use the earlier occurrence. No true-solar-time correction is made. These are learning/reflection conventions, not evidence of predictive validity.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests cover all 4,320 valid month/day/hour combinations, independent worked examples, parsing, date/time/DST validation, structured errors, successful cache reuse, retry after upstream failure, request size limits, and CORS. API tests mock the upstream for reproducibility. A separate live request to Hong Kong Observatory was also verified during implementation.

Run the existing frontend tests with `npm test` (Node.js 18+). See `prompt_log.md` for AI use and `DEPLOYMENT_GUIDE_ZH.md` for the beginner walkthrough.
