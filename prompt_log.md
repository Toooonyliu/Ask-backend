# HW4 AI prompt log

Date: September 27, 2026

Tool: Codex (GPT-6-based coding agent in this session). Used for repository inspection, implementation, tests, documentation, and step-by-step explanations. No AI model is called by the deployed application.

## Key user prompts

1. “So I need to do a new assignment for my AI effective coding class, may you review the assignment description on the website and give me a breakdown and explanation on what I need to do?” — with the HW4 assignment URL.
2. “我们可以把我上一个项目HW3 Ask，变成backend部署的吗？” — with the portfolio GitHub repository URL.
3. “OK那你帮我开始操作吧，我希望你操作的同时能够以一个老师的角色介绍一下你在做什么，为什么要这么做，把我当作一个完全不了解代码也不了解如何部署后端的学生，以最通俗易懂的语言解释清楚”

## Decisions shaped by these prompts

- Extend the existing Ask interface instead of designing another project.
- Move real calendar requests and personal-reading calculation into a separate Flask backend for Render.
- Preserve the original three-stage hand animation, bilingual text, guest history, and Supabase account flow.
- Send only date, clock, and time zone to the backend; keep question matching in the frontend.
- Validate inputs and return structured errors; do not invent data or silently fall back to local calculation.
- Explain local servers, endpoints, JSON, CORS, GitHub repositories, and deployment in plain Chinese.

## Verification and remaining work

Backend unit tests and frontend regression tests were run, and a real calendar request succeeded. The user created the GitHub repository and deployed the backend through Render with guided setup. Live backend requests and CORS headers passed. Codex configured and published the frontend integration. Live-browser verification, video recording, and course form submission remain separate steps.
