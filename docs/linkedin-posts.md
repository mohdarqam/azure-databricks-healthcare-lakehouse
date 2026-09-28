# 3-day LinkedIn launch — Healthcare Lakehouse project

A build-in-public arc: **Day 1 the problem + architecture, Day 2 the engineering guts, Day 3 the
result + repo.** This structure earns more reach than one big post, because each day gives people a
reason to come back, and the repo link lands on Day 3 when the project is actually finished.

**Posting mechanics**
- Post mid-morning on weekdays (Tue–Thu land best; you're starting Mon 29 Sep, which is fine).
- First comment = your link (architecture image on Day 1/2, repo on Day 3). Links in the first comment,
  not the body, keep reach up.
- Reply to every comment in the first 2 hours.
- Keep hashtags to 3–5, specific ones.
- **Day 3 must include the finished repo + screenshots** — don't post it until the run works.

---

## DAY 1 — The problem & the architecture

> 🏥 I built a metadata-driven healthcare data platform on Azure + Databricks. Here's the "why" before the "how".
>
> Healthcare data is scattered — hospital databases, lab partners, insurance feeds — and stitching it
> together is usually manual and error-prone. Reports go stale and nobody notices until a number is wrong.
>
> So over the last few days I built a lakehouse that fixes that, end to end:
>
> 🔹 Azure Data Factory ingests from PostgreSQL + CSV partner feeds
> 🔹 ADLS Gen2 as the landing zone
> 🔹 Databricks processes it Bronze → Silver → Gold on Delta Lake
> 🔹 Unity Catalog for governance, Key Vault for secrets, GitHub for CI/CD
>
> The design goal that made it click for me: **onboarding a new table should be a config change, not a
> new pipeline.** More on how I pulled that off tomorrow.
>
> Architecture diagram in the comments 👇
>
> #DataEngineering #Azure #Databricks #HealthcareData #Lakehouse

*First comment:* architecture diagram image + "Full walkthrough coming over the next 2 days."

---

## DAY 2 — The engineering (metadata-driven + medallion)

> ⚙️ Yesterday I shared the *what*. Today, the part I'm proudest of — how the pipeline scales without
> me writing new code.
>
> Every table the platform ingests is **one row** in a control table:
> source system · load type · watermark column · merge keys · active flag.
>
> ADF's main pipeline looks up the active tables → a ForEach runs an inner pipeline per table → lands
> data on a timestamped path in ADLS. Add a new source? Insert a row. That's it.
>
> Then Databricks takes over with a medallion architecture on Delta:
> 🥉 Bronze — raw + audit columns (never lose source fidelity)
> 🥈 Silver — cleaned, typed, deduplicated; full / append / **merge (Delta MERGE upsert)** by config
> 🥇 Gold — business-ready marts the dashboards actually read
>
> The bit that taught me the most: incremental loads. Watermark columns + a control table so each run
> only reads what changed, and a Delta MERGE handles the upserts.
>
> Tomorrow: the finished result + the full repo so you can build it yourself. 👀
>
> #DataEngineering #PySpark #Databricks #Azure #DeltaLake #ETL

*First comment:* a screenshot of the ADF pipeline canvas or the medallion flow.

---

## DAY 3 — The result + the repo

> ✅ It's live and it's yours. The full metadata-driven healthcare lakehouse — every SQL script, ADF
> design, and PySpark notebook — is on GitHub.
>
> What it does, end to end:
> 🔹 Config-driven ingestion (PostgreSQL + CSV → ADLS Gen2) via Azure Data Factory
> 🔹 Bronze → Silver → Gold on Delta Lake with full / append / merge loads
> 🔹 Watermark-based incrementals + a full audit log
> 🔹 Unity Catalog governance (access connector → external location → volume — the classic interview Q)
> 🔹 Key Vault secrets + GitHub CI/CD
>
> I built it on entirely synthetic data to learn the ADF ⇄ Databricks orchestration flow properly —
> and to close the one gap I had, orchestrating Databricks jobs from ADF. [Add your one honest line:
> "The thing that broke the most was ___, and fixing it taught me ___."]
>
> Everything's documented so you can stand it up on free tiers in a day. Repo in the comments 👇
> Happy to answer anything — and if your team hires data engineers on this stack, I'd love to chat.
>
> #DataEngineering #Azure #Databricks #PySpark #Snowflake #HealthcareAnalytics #OpenToWork

*First comment:* the GitHub repo link + 2–3 screenshots (pipeline run, gold KPIs, audit log).

---

## Reusable tips

- Swap the bracketed lines for something real you experienced — specifics are what make it credible.
- If a post underperforms, don't delete it; the arc still works for people who find Day 3 first.
- After Day 3, add the repo to **LinkedIn Featured** and your CV Projects section.
