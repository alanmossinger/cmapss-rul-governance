# First Push — Getting This Repo on GitHub

This file documents the one-time setup. Delete it after you've pushed if you want, or keep it as part of the project history.

## 1. Create the empty repo on GitHub

Go to https://github.com/new and create a **public** repository with:

- **Name:** `cmapss-rul-governance` (or your chosen name — change references in this file if so)
- **Description:** `Production-grade industrial AI: NASA C-MAPSS RUL prediction with full NIST AI RMF + EU AI Act governance layer.`
- **Initialize:** _do not_ initialize with README, LICENSE, or .gitignore — we already have those.

Take note of the URL: `https://github.com/<your-username>/cmapss-rul-governance.git`

## 2. Set repo topics for discoverability

After creation, click the gear icon next to "About" on the repo home page and add these topics:

```
industrial-ai
ai-governance
predictive-maintenance
nist-ai-rmf
eu-ai-act
cnn-lstm
shap
remaining-useful-life
nasa-cmapss
fastapi
mlops
responsible-ai
```

## 3. Push from your desktop

Open a terminal in this folder (`cmapss-rul-governance/`) and run:

```bash
# Initialize and set identity (skip if already configured globally)
git init
git config user.name "Alan Mössinger"
git config user.email "alan.mossinger@vexholding.com"

# Stage everything
git add .

# First commit
git commit -m "feat: initial scaffold — governance-first industrial AI

- Full NIST AI RMF + EU AI Act governance mapping
- Model card, risk register, data card, HITL protocol
- Rollback procedure, drift monitoring spec, audit trail spec
- Python package skeleton with FastAPI service stub
- CI workflows: tests, lint, governance-check gate
- Apache 2.0 license"

# Main branch
git branch -M main

# Remote (replace <your-username>)
git remote add origin https://github.com/<your-username>/cmapss-rul-governance.git

# Push
git push -u origin main
```

## 4. Protect main

After the first push, in GitHub:

- **Settings → Branches → Add rule** for `main`:
  - Require a pull request before merging
  - Require approvals: 1
  - Require status checks to pass: `CI`, `Governance Check`
  - Do not allow bypassing the above settings

Even though you're solo, this discipline shows up in the repo history and signals operating maturity to anyone browsing.

## 5. Verify CI

After the push, the **Actions** tab will show two workflows running:

- `CI` — should pass (smoke test only at this stage)
- `Governance Check` — should pass (all 9 governance docs present)

If either fails, click in to see the log. Most common failure: typo in file path between a `governance/*.md` doc and the workflow's required-list.

## 6. Verify the README looks good

Open `https://github.com/<your-username>/cmapss-rul-governance` and verify:

- The README badges render (CI badge will show "no status" until the first run completes, then turn green)
- The Mermaid architecture diagrams render
- The governance documents are linked correctly

## 7. Optional polish

- Add a banner image to `docs/images/` and reference it at the top of the README
- Pin the repo to your GitHub profile (Profile → Customize your pins)
- Add the repo URL to your LinkedIn featured section
- Update your LinkedIn About to reference "production industrial AI flagship" with link

## You're done

Everything from here is real engineering work — building out the data pipeline, the RF baseline, the LSTM, the CNN-LSTM, SHAP, the API. Each of those should land as its own PR with the governance impact section filled in.
