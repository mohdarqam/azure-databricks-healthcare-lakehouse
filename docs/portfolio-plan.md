# Turning this into a portfolio piece

A GitHub repo is the foundation. A *portfolio* is the repo plus the evidence that you built and
understand it. Here's how to make this land with recruiters and hiring managers.

## 1. The repo is the anchor (done)

- Clear README with an architecture diagram (already in place).
- Runnable code, honest credits, MIT license.
- **Pin it** on your GitHub profile.

## 2. Add proof you actually ran it

Screens beat claims. Capture and drop into `docs/images/` and embed in the README:

- ADF pipeline canvas (main + inner) and a successful run in Monitor.
- The `landing/` folder tree with timestamped parquet.
- Databricks: bronze/silver/gold tables in the catalog + a `display()` of gold KPIs.
- One `control.audit_log` screenshot showing success rows.
- The Databricks SQL dashboard and one Genie natural-language question.

> A README with 5–6 real screenshots reads as "this person shipped it," which is the whole game.

## 3. Make it *yours* (interview insurance)

The architecture is a taught pattern — differentiate so it's not a clone and you can defend every line:

- **Rename** the domain entity (Meridian Health Network → your own) and tweak the schema.
- **Add one thing of your own.** Highest-value options, in order:
  1. A **data quality gate** in Silver (row counts, null checks, referential checks) writing pass/fail
     to `audit_log` — directly matches the JDs you're targeting ("data quality, reconciliation").
  2. A real **incremental run**: insert/update a few Postgres rows, re-run, and show the merge only
     touched changed rows. Screenshot before/after.
  3. A **gold KPI** that's genuinely healthcare-analytical (e.g. abnormal-lab-result rate by hospital).
- Write a short **"what broke and how I fixed it"** section — hiring managers love this more than a
  flawless demo.

## 4. Where the portfolio lives

- **GitHub** — pinned repo (primary).
- **LinkedIn Featured** — link the repo; attach the architecture image so it renders a preview.
- **A one-page write-up** — optional: publish `architecture.md` as a LinkedIn article or a short
  GitHub Pages page, so non-technical recruiters get the story without reading code.
- **On your CV** — the project block from `add-to-resume.md`, with the repo URL.

## 5. Optional: a portfolio site later

Once you have 2–3 projects (this + the Medicare EDA you already use + one more), a tiny static site
(`yourname.github.io`) that lists them with the architecture image and a one-line result each is worth
an afternoon. Not needed for this one project — a pinned, screenshot-rich repo does the job now.

## Sequencing with the 3-day launch

- **Before Day 1 post:** repo public, README + diagram done.
- **Before Day 3 post:** the full run finished, screenshots added, your one differentiator built. Day 3
  is where you link the repo, so it must be complete by then.
