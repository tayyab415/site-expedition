# Iteration 6 — The email

**Look:** a message the agent would actually send. Inbox chrome, not a dashboard.

**Backend:** stdlib server **8026**. `compose.py` turns a verdict into a mail body with **consequence** lines (not a fake appraisal).

**Harness:** consequence layer on top of existing packets — what the fight *does* to the deal.

**Features:** KILL mail vs KEEP mail. No dollar theater; the ask is “price the contradiction” vs “proceed on the record.”

```bash
cd iteration-6
python3 compose.py
python3 serve.py
# http://127.0.0.1:8026
```
