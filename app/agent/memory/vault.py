import re
import yaml
from datetime import datetime
from pathlib import Path


class Vault:
    def __init__(self, vault_dir: str = "data/vault"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def save(self, title: str, story: str, keywords: list[str], subdir: str = "") -> Path:
        related_titles = self._find_related_by_keywords(keywords, exclude=title)
        self._add_backlinks(new_title=title, to=related_titles)

        frontmatter = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": keywords,
            "related": [f"[[{t}]]" for t in related_titles],
        }
        dir_path = self.vault_dir / subdir if subdir else self.vault_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        path = dir_path / f"{slugify(title)}.md"
        path.write_text(_render(frontmatter, story, related_titles), encoding="utf-8")
        return path

    def load(self, title: str) -> dict | None:
        path = self._find_file(title)
        return _parse(path.read_text(encoding="utf-8")) if path else None

    def load_all(self) -> list[dict]:
        results = []
        for p in self.vault_dir.rglob("*.md"):
            data = _parse(p.read_text(encoding="utf-8"))
            rel = p.parent.relative_to(self.vault_dir)
            data["subdir"] = "" if rel.as_posix() == "." else rel.as_posix()
            results.append(data)
        return results

    def get_linked_stories(self, title: str) -> list[str]:
        data = self.load(title)
        if not data:
            return []
        return [_extract_title(link) for link in data["frontmatter"].get("related", [])]

    def _find_file(self, title: str) -> Path | None:
        matches = list(self.vault_dir.rglob(f"{slugify(title)}.md"))
        return matches[0] if matches else None

    def _find_related_by_keywords(self, keywords: list[str], exclude: str = "") -> list[str]:
        kw_set = {k.lower() for k in keywords}
        related = []
        for path in self.vault_dir.rglob("*.md"):
            data = _parse(path.read_text(encoding="utf-8"))
            fm = data["frontmatter"]
            if fm.get("title") == exclude:
                continue
            file_kws = {k.lower() for k in fm.get("keywords", [])}
            if kw_set & file_kws:
                related.append(fm["title"])
        return related

    def list_worlds(self) -> list[dict]:
        """Return one entry per world directory (dir whose name matches its world-setting file)."""
        worlds = []
        for subdir in sorted(self.vault_dir.iterdir()):
            if not subdir.is_dir():
                continue
            world_file = subdir / f"{subdir.name}.md"
            if not world_file.exists():
                continue
            data = _parse(world_file.read_text(encoding="utf-8"))
            fm = data["frontmatter"]
            worlds.append({
                "slug": subdir.name,
                "title": fm.get("title", subdir.name),
                "intro": _extract_intro(data["story"]),
            })
        return worlds

    def rename_world(self, old_title: str, new_title: str) -> bool:
        """Rename a world: update frontmatter, rename the file and directory, fix wikilinks."""
        old_slug = slugify(old_title)
        new_slug = slugify(new_title)
        old_dir = self.vault_dir / old_slug

        if not old_dir.is_dir():
            return False
        new_dir = self.vault_dir / new_slug
        if new_dir.exists() and new_slug != old_slug:
            return False

        # 1. Rewrite the world-setting file's frontmatter with the new title
        world_file = old_dir / f"{old_slug}.md"
        new_world_file = old_dir / f"{new_slug}.md"
        if world_file.exists():
            data = _parse(world_file.read_text(encoding="utf-8"))
            fm = data["frontmatter"]
            fm["title"] = new_title
            related_titles = [_extract_title(r) for r in fm.get("related", [])]
            world_file.write_text(_render(fm, data["story"], related_titles), encoding="utf-8")
            if old_slug != new_slug:
                world_file.rename(new_world_file)

        # 2. Update [[old_title]] wikilinks in every other vault file
        if old_title != new_title:
            old_link = f"[[{old_title}]]"
            new_link = f"[[{new_title}]]"
            skip = new_world_file.resolve()
            for path in self.vault_dir.rglob("*.md"):
                if path.resolve() == skip:
                    continue
                content = path.read_text(encoding="utf-8")
                if old_link in content:
                    path.write_text(content.replace(old_link, new_link), encoding="utf-8")

        # 3. Rename the directory itself
        if old_slug != new_slug:
            old_dir.rename(new_dir)

        return True

    def _add_backlinks(self, new_title: str, to: list[str]):
        new_link = f"[[{new_title}]]"
        for title in to:
            path = self._find_file(title)
            if not path:
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


def _extract_intro(content: str) -> str:
    """Return text before the first ## heading (the introduction paragraph)."""
    m = re.search(r"\n##\s", content)
    return content[: m.start()].strip() if m else content.strip()


def _extract_title(link: str) -> str:
    m = re.match(r"\[\[(.+?)\]\]", link)
    return m.group(1) if m else link


def slugify(title: str) -> str:
    return re.sub(r"[^\w-]", "-", title.lower()).strip("-")
