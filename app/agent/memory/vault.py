import re
import yaml
from datetime import datetime
from pathlib import Path


class Vault:
    def __init__(self, vault_dir: str = "data/vault"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def save(self, title: str, story: str, keywords: list[str]) -> Path:
        related_titles = self._find_related_by_keywords(keywords, exclude=title)
        self._add_backlinks(new_title=title, to=related_titles)

        frontmatter = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": keywords,
            "related": [f"[[{t}]]" for t in related_titles],
        }
        path = self.vault_dir / f"{_slugify(title)}.md"
        path.write_text(_render(frontmatter, story, related_titles), encoding="utf-8")
        return path

    def load(self, title: str) -> dict | None:
        path = self.vault_dir / f"{_slugify(title)}.md"
        return _parse(path.read_text(encoding="utf-8")) if path.exists() else None

    def load_all(self) -> list[dict]:
        return [_parse(p.read_text(encoding="utf-8")) for p in self.vault_dir.glob("*.md")]

    def get_linked_stories(self, title: str) -> list[str]:
        data = self.load(title)
        if not data:
            return []
        return [_extract_title(link) for link in data["frontmatter"].get("related", [])]

    def _find_related_by_keywords(self, keywords: list[str], exclude: str = "") -> list[str]:
        kw_set = {k.lower() for k in keywords}
        related = []
        for path in self.vault_dir.glob("*.md"):
            data = _parse(path.read_text(encoding="utf-8"))
            fm = data["frontmatter"]
            if fm.get("title") == exclude:
                continue
            file_kws = {k.lower() for k in fm.get("keywords", [])}
            if kw_set & file_kws:
                related.append(fm["title"])
        return related

    def _add_backlinks(self, new_title: str, to: list[str]):
        new_link = f"[[{new_title}]]"
        for title in to:
            path = self.vault_dir / f"{_slugify(title)}.md"
            if not path.exists():
                continue
            data = _parse(path.read_text(encoding="utf-8"))
            fm = data["frontmatter"]
            existing = fm.get("related", [])
            if new_link in existing:
                continue
            fm["related"] = existing + [new_link]
            related_titles = [_extract_title(r) for r in fm["related"]]
            path.write_text(_render(fm, data["story"], related_titles), encoding="utf-8")


def _render(frontmatter: dict, story: str, related_titles: list[str]) -> str:
    fm = dict(frontmatter)
    fm["related"] = [f"[[{t}]]" for t in related_titles]
    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()
    parts = [f"---\n{fm_str}\n---", story.strip()]
    if related_titles:
        links = "\n".join(f"- [[{t}]]" for t in related_titles)
        parts.append(f"## Related\n{links}")
    return "\n\n".join(parts)


def _parse(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        return {"frontmatter": {}, "story": text.strip()}
    fm = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()
    story = re.split(r"\n## Related\b", body, maxsplit=1)[0].strip()
    return {"frontmatter": fm, "story": story}


def _extract_title(link: str) -> str:
    m = re.match(r"\[\[(.+?)\]\]", link)
    return m.group(1) if m else link


def _slugify(title: str) -> str:
    return re.sub(r"[^\w-]", "-", title.lower()).strip("-")
