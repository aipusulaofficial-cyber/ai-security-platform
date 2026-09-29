# GitHub Workflow Guide

This repository uses GitHub Actions as executable engineering evidence.

## Workflow model

Workflows are stored in `.github/workflows/`. A trigger starts a workflow; jobs run on runners; steps execute the concrete commands and actions.

**Evidence flow**

`Trigger → Runner → Setup → Quality Gates → Domain Evidence → Tests → Security/Build Checks → Artifacts → Result`

## What the Actions UI proves

- **Run:** the commit and event that generated the evidence.
- **Job:** an isolated verification unit.
- **Step:** the exact command/action.
- **Gate:** a pass/fail boundary that controls downstream verification.
- **Artifact:** persistent machine-readable evidence such as coverage, test results, benchmarks, or reports.

## Repository-specific evidence focus

**Prompt-security inspection, authorization boundaries, audit context, tests, and security evidence.**

A green run means the configured checks passed for that commit. It should not be interpreted as an unbounded production guarantee.

## Failure diagnosis

Start with the first failed step. Downstream skipped steps generally reflect that earlier failure. Fix the root cause, commit it, and verify the complete workflow set for the new commit.

## Reproducibility and artifacts

Verification commands should remain runnable from the repository. Important outputs should be preserved as artifacts so the result can be inspected after the runner exits.

## Portfolio signal

This repository is part of the AIPUSULA enterprise AI platform portfolio. Its workflow turns its domain contract into repeatable executable evidence.

See `docs/PORTFOLIO_EVIDENCE.md` for the domain proof chain.
