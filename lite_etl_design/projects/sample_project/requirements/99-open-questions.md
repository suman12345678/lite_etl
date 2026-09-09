# 99 - Open questions & assumptions

> Produced by `/gather-requirements`, updated by `/finalize-requirements` on
> 2026-09-03. Phase 2 treats every open item's interim assumption as a design
> assumption (see `design/architecture-overview.md` section 5).

| Q# | Question | Why it matters | Interim assumption | Owner | Status |
|----|----------|----------------|--------------------|-------|--------|
| Q1 | Final list of BCBS 239 mandatory fields per regulated feed, and the Oracle/CRM data-dictionary exports. | Drives completeness DQ rules and the curated model's non-null constraints. | Use the draft list from discovery (account id, customer id, balance, currency, product, status, post date, amount); everything else nullable + flagged. | Regulatory Reporting lead | **open** - due at design sign-off |
| Q2 | Can `curated_build` sign-off be automated (recon PASS ⇒ auto-publish) or must a human approve before 06:00? | Determines whether a person is on the critical path nightly. | ~~Human approval required~~ → **Resolved 2026-09-03:** auto-publish on recon PASS; human sign-off becomes a same-day review, not a gate. Alert if not reviewed by 09:00. | Head of Risk Data | **answered** |
| Q3 | Will the card processor offer intraday / multiple files per day within the roadmap horizon? | Affects whether the design should be micro-batch-ready for cards now. | No intraday in the next 12 months; design for daily file, keep the landing path file-count-agnostic. | Cards product owner | **open** - roadmap review Q4 2026 |
| Q4 | DPO sign-off on the UAT test of the GDPR erasure (crypto-shred) path. | Erasure process must be proven before go-live. | ~~Pending~~ → **Resolved 2026-09-03:** DPO approved the crypto-shred + `CURATED_SENSITIVE` row-delete approach; UAT test to be evidenced. | DPO | **answered** |
| Q5 | Are source read replicas / exports available in all three environments (dev/uat/prod), or is dev pointed at a subset/synthetic? | Affects dev testability and the backfill plan. | dev uses a synthetic subset; uat and prod use real replicas. | Data Platform | **open** - infra request raised |

## Answered log

| Q# | Answer | Date | Answered by |
|----|--------|------|-------------|
| Q2 | Auto-publish on reconciliation PASS; sign-off downgraded to a same-day review with a 09:00 CET escalation. Reflected in `07-scheduling-and-orchestration.md` and `00-project-brief.md` success criteria. | 2026-09-03 | Head of Risk Data |
| Q4 | Crypto-shred of the tokenisation key mapping + delete of the `CURATED_SENSITIVE` row approved; aggregates keep only `customer_sk`. Reflected in `08-security-and-compliance.md`. | 2026-09-03 | DPO |
