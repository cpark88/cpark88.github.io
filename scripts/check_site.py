#!/usr/bin/env python3
"""Check index.html against the site conventions in CLAUDE.md.

  python3 scripts/check_site.py            errors and warnings; exit 1 if there are errors
  python3 scripts/check_site.py --strict   before publishing: placeholders, missing linked files and
                                           a stale "Last updated" line also count as errors
  python3 scripts/check_site.py --hook     Claude Code PostToolUse hook: reads the hook JSON on stdin,
                                           runs only after index.html changes, exits 2 with errors on stderr

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
PRIVATE_TERMS = ROOT / ".claude" / "private-terms.txt"
OWNER = "Chung Park"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FULL_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
MAX_NEWS = 8
PUB_TYPES = ("Conference", "Journal", "Workshop", "Preprint")
# Wording that must never reach the public page. Names of unpublished papers and internal
# projects go in .claude/private-terms.txt instead: this script is public, that file is gitignored.
BLOCKED_PHRASES = ["under review", "under submission", "in submission", "submitted to",
                   "anonymous submission", "double-blind", "confidential", "internal only",
                   "대외비", "사내 한정"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
NO_TEXT = {"script", "style"}
ATTRS_WITH_TEXT = ("href", "src", "alt", "title", "aria-label", "data-label", "content")


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "line")

    def __init__(self, tag, attrs, parent, line):
        self.tag = tag
        self.attrs = {k: (v or "") for k, v in attrs}
        self.children = []
        self.parent = parent
        self.line = line

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    def walk(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()

    def find_all(self, tag=None, cls=None):
        return [n for n in self.walk()
                if (tag is None or n.tag == tag) and (cls is None or cls in n.classes)]

    def find(self, tag=None, cls=None):
        found = self.find_all(tag, cls)
        return found[0] if found else None

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", [], None, 0)
        self.stack = [self.root]
        self.problems = []      # (line, message) for tag nesting
        self.texts = []         # (line, text) visible text
        self.attr_texts = []    # (line, value) attribute values that reach readers

    def _add(self, tag, attrs):
        line = self.getpos()[0]
        node = Node(tag, attrs, self.stack[-1], line)
        self.stack[-1].children.append(node)
        for key, value in attrs:
            if value and key in ATTRS_WITH_TEXT:
                self.attr_texts.append((line, value))
        return node

    def handle_starttag(self, tag, attrs):
        node = self._add(tag, attrs)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._add(tag, attrs)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        line = self.getpos()[0]
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                for unclosed in self.stack[i + 1:]:
                    self.problems.append((unclosed.line, f"<{unclosed.tag}> is not closed before </{tag}> on line {line}"))
                del self.stack[i:]
                return
        self.problems.append((line, f"</{tag}> has no matching opening tag"))

    def handle_data(self, data):
        self.stack[-1].children.append(data)
        if data.strip() and not any(n.tag in NO_TEXT for n in self.stack):
            self.texts.append((self.getpos()[0], data))

    def close(self):
        super().close()
        for node in self.stack[1:]:
            self.problems.append((node.line, f"<{node.tag}> is never closed"))


class Report:
    def __init__(self):
        self.errors, self.warnings, self.notes = [], [], []

    def error(self, line, msg):
        self.errors.append((line, msg))

    def warn(self, line, msg):
        self.warnings.append((line, msg))

    def note(self, line, msg):
        self.notes.append((line, msg))


def year_of(node):
    m = re.search(r"(?<!\d)(?:19|20)\d{2}(?!\d)", node.text()) if node is not None else None
    return int(m.group(0)) if m else None


def label_of(node):
    pid = node.attrs.get("id")
    return f'"{pid}"' if pid else f"entry on line {node.line}"


def check_entry(node, label, rep):
    title = node.find(cls="pub-title")
    link = title.find("a") if title is not None else None
    if link is None or not link.attrs.get("href"):
        rep.error(node.line, f"{label}: the title needs a link (paper page, or the code repo if there is no paper yet)")

    authors = node.find(cls="authors")
    if authors is None:
        rep.error(node.line, f'{label}: missing <p class="authors">')
    else:
        has_todo = any("todo" in n.classes for n in authors.walk())
        bold = [s.text().strip() for s in authors.find_all("strong")]
        if OWNER not in bold and not has_todo:
            rep.error(authors.line, f"{label}: the author list must include <strong>{OWNER}</strong>")
        if any(b != OWNER for b in bold):
            rep.error(authors.line, f"{label}: only {OWNER} is bold in author lists")
        if authors.text().count(OWNER) > bold.count(OWNER):
            rep.error(authors.line, f"{label}: {OWNER} appears without <strong>")

    venue = node.find(cls="venue")
    if year_of(venue) is None:
        rep.error(node.line, f'{label}: <p class="venue"> needs the venue and a year, e.g. <em>ICLR</em> 2026')

    kind = venue.find(cls="pub-type") if venue is not None else None
    if kind is None or kind.text().strip() not in PUB_TYPES:
        rep.error(node.line, f'{label}: the venue line starts with <span class="pub-type">, one of {", ".join(PUB_TYPES)}')

    links = node.find(cls="pub-links")
    if links is None or not links.find_all("a"):
        rep.error(node.line, f'{label}: <p class="pub-links"> needs at least one link (Paper, arXiv or Code)')

    for impact in node.find_all(cls="impact"):
        if impact.find(cls="live-dot") is None:
            rep.error(impact.line, f'{label}: an impact line starts with <span class="live-dot" aria-hidden="true"></span>')


def check_order(entries, what, rep):
    previous = None
    for node in entries:
        year = year_of(node.find(cls="venue"))
        if year is None:
            continue
        if previous and year > previous[1]:
            rep.error(node.line, f"{what}: {label_of(node)} ({year}) is below {previous[0]} ({previous[1]}); newest goes first")
        previous = (label_of(node), year)


def check_publications(root, rep):
    pubs = root.find_all("article", "pub")
    if not pubs:
        rep.error(0, 'no <article class="pub"> entries found')
    for art in pubs:
        pid = art.attrs.get("id", "")
        label = label_of(art)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pid):
            rep.error(art.line, f'{label}: needs a lowercase id such as id="duelrec" (it also names the teaser file)')
        teaser = art.find("a", "teaser")
        if teaser is None:
            rep.error(art.line, f'{label}: missing <a class="teaser" data-label="..."> before the text')
        else:
            if not teaser.attrs.get("data-label"):
                rep.error(teaser.line, f"{label}: the teaser needs data-label (the short name shown until a figure exists)")
            img = teaser.find("img")
            expected = f"images/teasers/{pid}.png"
            if img is None or img.attrs.get("src") != expected:
                rep.error(teaser.line, f'{label}: the teaser image must be <img src="{expected}" alt="">')
        check_entry(art, label, rep)
    check_order(pubs, "Publications", rep)


def check_news(root, rep):
    news = root.find("ol", "news")
    if news is None:
        rep.error(0, 'missing <ol class="news">')
        return []
    items = [c for c in news.children if isinstance(c, Node) and c.tag == "li"]
    dates, previous = [], None
    for li in items:
        t = li.find("time")
        m = re.fullmatch(r"(\d{4})-(\d{2})", t.attrs.get("datetime", "")) if t is not None else None
        if not m or not 1 <= int(m.group(2)) <= 12:
            rep.error(li.line, 'news items start with <time datetime="YYYY-MM">Mon YYYY</time>')
            continue
        y, mo = int(m.group(1)), int(m.group(2))
        shown = f"{MONTHS[mo - 1]} {y}"
        if t.text().strip() != shown:
            rep.error(t.line, f'news date reads "{t.text().strip()}" but datetime is {y}-{mo:02d}; write "{shown}"')
        if previous and (y, mo) > previous:
            rep.error(li.line, f"news goes newest first: {shown} is below an older item")
        previous = (y, mo)
        dates.append((y, mo))
    if len(items) > MAX_NEWS:
        rep.warn(news.line, f"{len(items)} news items; keep at most {MAX_NEWS} by deleting the oldest")
    return dates


def check_ids_and_anchors(root, rep):
    seen = {}
    for node in root.walk():
        node_id = node.attrs.get("id")
        if not node_id:
            continue
        if node_id in seen:
            rep.error(node.line, f'duplicate id="{node_id}" (also on line {seen[node_id]})')
        else:
            seen[node_id] = node.line
    for a in root.find_all("a"):
        href = a.attrs.get("href", "")
        if href.startswith("#") and len(href) > 1 and href[1:] not in seen:
            rep.error(a.line, f'link to "{href}" but nothing has id="{href[1:]}"')


def private_terms():
    if not PRIVATE_TERMS.exists():
        return []
    lines = PRIVATE_TERMS.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def contains(text, term):
    if term.isascii():
        pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
        return re.search(pattern, text, re.IGNORECASE) is not None
    return term.lower() in text.lower()


def check_blocked(parser, rep):
    terms = BLOCKED_PHRASES + private_terms()
    for line, text in parser.texts + parser.attr_texts:
        for term in terms:
            if contains(text, term):
                rep.error(line, f'"{term}" must not appear on the public page (CLAUDE.md, content rules)')


def check_placeholders(root, rep, strict):
    for node in root.walk():
        if "todo" in node.classes:
            msg = f'placeholder still on the page: "{node.text().strip()[:50]}"'
            (rep.error if strict else rep.warn)(node.line, msg)


def check_local_files(root, rep, strict):
    for node in root.walk():
        for attr in ("href", "src"):
            value = node.attrs.get(attr)
            if not value or re.match(r"^(https?:|mailto:|tel:|#|data:|//)", value):
                continue
            if (ROOT / value.split("#")[0].split("?")[0]).exists():
                continue
            parent = node.parent.classes if node.parent is not None else set()
            if node.tag == "img" and parent & {"teaser", "portrait"}:
                rep.note(node.line, f"{value} not found; its placeholder tile is shown")
            else:
                (rep.error if strict else rep.warn)(node.line, f"{value} is linked but the file does not exist")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_images(root, rep):
    ids = {a.attrs.get("id") for a in root.find_all("article", "pub")}
    for path in sorted((ROOT / "images").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        kb = path.stat().st_size / 1024
        if kb > 500:
            rep.warn(0, f"{rel} is {kb:.0f} KB; re-run scripts/make_teaser.py or compress it (under 300 KB is plenty)")
        if path.parent.name == "teasers":
            if path.stem not in ids:
                rep.warn(0, f"{rel} matches no publication id")
            size = png_size(path) if path.suffix.lower() == ".png" else None
            if size and size[1]:
                ratio = size[0] / size[1]
                if not 1.4 <= ratio <= 3.2:
                    rep.warn(0, f"{rel} is {ratio:.1f}:1; teasers sit in a 2:1 box, so it will look small (crop with make_teaser.py --crop)")


def check_typography(parser, rep):
    for line, text in parser.texts:
        if re.search(r"[A-Za-z]'[A-Za-z]", text):
            rep.warn(line, f"straight apostrophe in “{text.strip()[:50]}”; use ’")


def check_footer(root, rep, strict, news_dates, today):
    footer = root.find("footer")
    m = re.search(r"Last updated (" + "|".join(FULL_MONTHS) + r") (\d{4})\.", footer.text()) if footer is not None else None
    if not m:
        rep.error(footer.line if footer is not None else 0, 'footer must read "Last updated <Month> <YYYY>."')
        return
    stamp = (int(m.group(2)), FULL_MONTHS.index(m.group(1)) + 1)
    if news_dates and max(news_dates) > stamp:
        rep.warn(footer.line, "the footer date is older than the newest news item")
    if stamp != (today.year, today.month):
        msg = f'footer says "Last updated {m.group(1)} {m.group(2)}"; set it to {FULL_MONTHS[today.month - 1]} {today.year} when publishing'
        (rep.error if strict else rep.warn)(footer.line, msg)


def check_external_links(root, rep):
    for a in root.find_all("a"):
        if a.attrs.get("href", "").startswith("http://"):
            rep.warn(a.line, f'use https: {a.attrs["href"]}')


def run(strict=False, hook=False, today=None):
    rep = Report()
    if not INDEX.exists():
        rep.error(0, f"{INDEX} not found")
        return rep
    parser = PageParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    parser.close()
    root = parser.root
    for line, msg in parser.problems:
        rep.error(line, msg)
    check_ids_and_anchors(root, rep)
    check_publications(root, rep)
    news_dates = check_news(root, rep)
    check_blocked(parser, rep)
    check_placeholders(root, rep, strict)
    check_local_files(root, rep, strict)
    if not hook:
        check_images(root, rep)
        check_typography(parser, rep)
        check_footer(root, rep, strict, news_dates, today or dt.date.today())
        check_external_links(root, rep)
    return rep


def hook_main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        return 0
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(payload.get("cwd") or ".") / path
    try:
        if path.resolve() != INDEX.resolve():
            return 0
    except OSError:
        return 0
    rep = run(hook=True)
    if not rep.errors:
        return 0
    print("scripts/check_site.py found problems in index.html after this edit:", file=sys.stderr)
    for line, msg in sorted(rep.errors):
        print(f"  line {line}: {msg}", file=sys.stderr)
    print("Fix these before continuing. Rules: CLAUDE.md and .claude/rules/page-markup.md.", file=sys.stderr)
    return 2


def main():
    ap = argparse.ArgumentParser(description="Check index.html against the site conventions.")
    ap.add_argument("--strict", action="store_true", help="pre-publish: placeholders, missing files and a stale footer fail")
    ap.add_argument("--hook", action="store_true", help="run as a Claude Code PostToolUse hook")
    args = ap.parse_args()
    if args.hook:
        return hook_main()
    rep = run(strict=args.strict)
    print(f"check_site.py: {INDEX.relative_to(ROOT)}" + (" (strict)" if args.strict else ""))
    for kind, items in (("ERROR", rep.errors), ("WARN ", rep.warnings), ("note ", rep.notes)):
        for line, msg in sorted(items):
            where = f"line {line}: " if line else ""
            print(f"  {kind} {where}{msg}")
    print(f"{len(rep.errors)} errors, {len(rep.warnings)} warnings, {len(rep.notes)} notes")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
