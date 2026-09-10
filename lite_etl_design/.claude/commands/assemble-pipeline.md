---
description: Phase 4 - wire components into orchestrator pipelines, plan IaC + CI/CD + git workflow, scaffold infra/ and CI skeletons
argument-hint: [optional focus, e.g. "GitLab CI not GitHub" or "one repo per domain"]
---

Start (or resume) **Phase 4 - Pipeline & Git** of the ETL data-harness design.

Invoke the `assemble-etl-pipeline` skill and follow it exactly:

1. Resolve the active workspace `<WS>` from `state/active-workspace` (stop if none).
2. Confirm Phase 3 is done - read `<WS>/progress.json`, `<WS>/design/`,
   `<WS>/build/` and list `<WS>/build/repo/`. If the build scaffold is missing,
   stop and tell me to run `/build-components`.
3. Settle the assembly choices: repo model, orchestrator deployment + how the
   reconciliation gate is expressed, IaC module set + apply order + state
   backend, the CI/CD workflows (PR / main / promote) + OIDC, the git workflow,
   and config layering.
4. Write to `<WS>/pipeline/`: `repo-layout.md`, `orchestration-wiring.md`,
   `iac-plan.md`, `cicd-plan.md`, `git-workflow.md`, `environments-and-config.md`,
   `README.md`. Templates come from the harness `pipeline/templates/`.
5. Scaffold skeletons inside `<WS>/build/repo/`: `infra/modules/*` +
   `infra/envs/*`, the orchestrator project (one file per pipeline, tasks +
   edges + retries + gate), `.github/workflows/{pr,main,promote}.yml` (or the
   chosen CI), `.pre-commit-config.yaml`, `CODEOWNERS`, `config/*.yml`.
   Skeletons and `TODO`s only - no real account ids, ARNs, hostnames, tokens, or
   business logic. Do not run terraform, deploy, or push.
6. Walk me through the repo tree, one pipeline wired end to end, the IaC apply
   order and the CI/CD flow; revise on feedback. Suggest `/validate-config`.
7. Update `<WS>/progress.json` (phase 4 status, deliverables, `active_phase` ->
   `5_full_testing_and_hardening`).

Optional heavy lifting: run the `pipeline-assembler` subagent (pass it `<WS>`).

Focus note, if any: $ARGUMENTS
