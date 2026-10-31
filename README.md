# cpark88.github.io

Source for [cpark88.github.io](https://cpark88.github.io), the homepage of Chung Park (박정).

Plain HTML and CSS with no build step. To preview locally:

```bash
python3 -m http.server 8000           # then open http://localhost:8000
python3 scripts/check_site.py         # check the page against the conventions in CLAUDE.md
```

Maintained with Claude Code: `CLAUDE.md` holds the conventions, `.claude/skills/` the workflows
(`/add-paper`, `/publish`), and a hook runs `scripts/check_site.py` after every edit to `index.html`.

Fonts: Source Serif 4 and Source Sans 3, licensed under the SIL Open Font License (`fonts/OFL.txt`).
