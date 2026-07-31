"""Structured reporting helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

LOGGER = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class ReportGenerator:
    """Render structured diagnostics as Rich text or JSON."""

    def render_rich(self, report: dict[str, Any]) -> str:
        from rich.console import Console
        from rich.table import Table

        LOGGER.info("Report generation started")
        console = Console(record=True, width=120)
        table = Table(title=report.get("title", "AI Workstation Report"))
        table.add_column("Section")
        table.add_column("Details", overflow="fold")
        for key, value in report.items():
            if key == "title":
                continue
            table.add_row(key.replace("_", " ").title(), self._format_value(value))
        console.print(table)
        LOGGER.info("Report generation completed")
        return console.export_text()

    def render_json(self, report: dict[str, Any]) -> str:
        LOGGER.info("Report generation started")
        rendered = json.dumps(report, indent=2, sort_keys=True, default=str)
        LOGGER.info("Report generation completed")
        return rendered

    def _format_value(self, value: Any) -> str:
        if isinstance(value, dict):
            return json.dumps(value, indent=2, sort_keys=True, default=str)
        if isinstance(value, list):
            return "\n".join(self._format_value(item) for item in value) or "[]"
        return str(value)
