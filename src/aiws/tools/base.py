"""Tool installer base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ToolInstaller(ABC):
    """Abstract tool installer interface."""

    @abstractmethod
    def detect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def install(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def uninstall(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def doctor(self) -> list[str]:
        raise NotImplementedError
