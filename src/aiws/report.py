"""Markdown report infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MarkdownReport:
    """Simple Markdown report builder."""

    title: str
    sections: list[str] = field(default_factory=list)

    def add_section(self, content: str) -> None:
        self.sections.append(content)

    def render(self) -> str:
        body = "\n\n---\n\n".join(self.sections)
        return f"# {self.title}\n\n{body}\n" if body else f"# {self.title}\n"
