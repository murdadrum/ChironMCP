# Git Workflow (Default)

This repo follows a strict, PR-based workflow to keep `main` releasable, traceable, and stable.

## Core Rules

- `main` is always releasable.
- All changes go through PRs (no direct pushes to `main`).
- Use short-lived feature branches.
- Update `CHANGELOG.md` for user-facing changes.

## Branching

- Feature branch: `feature/<area>-<short-desc>`
  - Example: `feature/blender-full-access`
- Sub-feature branches (optional):
  - `feature/blender-full-access/tool-api`
  - `feature/blender-full-access/editor-hooks`

## PR Requirements (Strict)

A PR may be merged only when:

- It has at least one approval.
- Required checks pass.
- `CHANGELOG.md` updated for user-facing changes.
- The PR template checklist is completed.

## Release Tags

- Tag releases on `main`.
- Use `v0.1.x` (SemVer-ish) until 1.0.
- Example: `v0.1.19`.

## GitHub Branch Protection (Apply in repo settings)

Protect `main` with:

- Require a pull request before merging.
- Require at least 1 approval.
- Require status checks to pass.
- Dismiss stale approvals when new commits are pushed.
- Restrict who can push to `main` (optional but recommended).

## Suggested PR Flow

1) Create branch
   - `git checkout -b feature/<area>-<short-desc>`

2) Work and commit
   - Keep commits focused.

3) Update `CHANGELOG.md`

4) Open PR using the template

5) Merge after approval + checks

