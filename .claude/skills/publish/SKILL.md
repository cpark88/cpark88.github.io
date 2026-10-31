---
name: publish
description: Use when homepage changes should go live, or when the user asks to publish, deploy, commit, push, "올려줘", "반영해줘", or whether the site is ready to publish.
argument-hint: "[commit message]"
---

# Publishing the homepage

Commit message from the user, if any: $ARGUMENTS

## 1. Check

Run `python3 scripts/check_site.py --strict` and continue only at 0 errors.

- Structure errors: fix them.
- A placeholder (`todo`) or a missing linked file: ask the user for the fact or the file. Do not invent a value, and do not delete the field to make the check pass.
- Footer date: set "Last updated <Month> <YYYY>." to the current month.

## 2. Look

Run `python3 scripts/screenshot.py`.

- If it exits with code 3, Playwright is missing. Tell the user once and skip this step.
- Otherwise open these with the Read tool:
  - `.preview/desktop-light-top.png`
  - `.preview/mobile-light-top.png`
  - `.preview/desktop-dark-top.png`
  - the full-page shot around the part you changed
- Look for overlapping text, broken or squashed images, and colors that break in dark mode. Fix them, then repeat this step.

## 3. Stage and review

1. Run `git add -A`, then `git diff --cached --stat`.
2. Unstage any private file with `git restore --staged <path>`, and make sure `.gitignore` lists it:
   - `.claude/private-terms.txt`
   - `CLAUDE.local.md`
   - anything under `.preview/`
3. Tell the user what changed in 2–4 lines.

## 4. Commit

`git commit -m "<message>"`. Use the user's message if there is one. Otherwise write a short imperative summary, for example `Add CURE (NeurIPS 2026)` or `Update news and footer`.

## 5. Push after an explicit yes

Ask: "Push to GitHub? The site updates at https://cpark88.github.io within a few minutes."

- Run `git push` only when the user says yes.
- Never force-push.
- After pushing, tell the user that GitHub Pages can take up to 10 minutes to show the change.
