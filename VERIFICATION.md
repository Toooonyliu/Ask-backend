# Verification — September 27, 2026

## Passed

- 10 Python backend tests, including exhaustive comparison of all 4,320 valid lunar-month/day/traditional-hour combinations with independent iterative counting.
- 23 Node frontend tests, including the existing account isolation, OAuth, history, calculation, and new API-client checks.
- Live Hong Kong Observatory request through the Flask backend: 2026-09-27 09:30 America/New_York returned 八月十七 and 小吉 with the expected three stages.
- Local Gunicorn service on port 5050 and static frontend server on port 4173.
- DOM integration using the actual `index.html`, `app.js`, bundled Supabase client, and a real local backend. Verified empty-input rejection, time-only POST payload, server-result rendering, language switching, visible network errors, and successful retry. Used an isolated in-memory DOM and reduced-motion mode; no real user history was changed.
- Git whitespace/error check for frontend changes.

## Not yet verified

- Actual browser rendering, browser-enforced CORS, and full animated timing after this migration. DOM checks are not a visual browser review.
- Live Render deployment, GitHub Pages update, and public end-to-end requests. Render account access is still needed to complete deployment.
- Live Google sign-in and cross-device history after deployment; existing account code was preserved and regression-tested.
- Assignment video and submission form.

`DEPLOYED_BACKEND_URL` is intentionally empty until Render assigns a real URL. Do not publish the frontend before setting and verifying it.
