"""Dependency-light source contract for resource-backed Skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mcp.server.context import ServerRequestContext
from typing_extensions import override

from fastmcp.skills.models import Skill

if TYPE_CHECKING:
    from fastmcp.server.providers.proxy import ClientFactoryT
    from fastmcp.server.server import FastMCP


@dataclass(frozen=True)
class _Catalog:
    skills: list[Skill]
    identities: tuple[str, ...]
    owners: dict[str, ClientFactoryT | FastMCP] = field(default_factory=dict)


@dataclass(frozen=True)
class _Lookup:
    matches: int = 0
    skill: Skill | None = None
    owner: ClientFactoryT | FastMCP | None = None


class _SkillSource(ABC):
    """Keep identity before authorization alongside the visible skills."""

    async def _is_supported(self, context: ServerRequestContext[Any, Any]) -> bool:
        return True

    def _validate_skill_source(self) -> None:
        """Reject source configurations that cannot publish a Skills catalog."""
        return None

    async def _owns_skill_resource(self, uri: str) -> bool:
        return False

    @abstractmethod
    async def _list_skill_entries(
        self, context: ServerRequestContext[Any, Any]
    ) -> _Catalog: ...

    @abstractmethod
    async def _get_skill_entry(
        self, uri: str, context: ServerRequestContext[Any, Any]
    ) -> _Lookup: ...


class SkillSource(_SkillSource):
    """Publish Skills entries for files a provider serves as resources.

    Mix into a `Provider` and pass that provider to
    `SkillsExtension(providers=[...])`. Its entries are combined with other
    sources and proxied backends. An entry is hidden when any file in its
    manifest is missing from the server or unreadable by the caller, so each
    manifest's sizes and digests must describe the bytes the provider serves.
    """

    @abstractmethod
    async def list_skills(self) -> Sequence[Skill]:
        """Return the entries to advertise through `skills/list`."""

    async def get_skill(self, uri: str) -> Skill | None:
        """Return the entry for `uri`, or `None`; searches `list_skills()` by default.

        Override to look up one entry without listing, or to serve entries
        that `list_skills()` does not advertise.
        """
        skills = await self.list_skills()
        return next((skill for skill in skills if skill.uri == uri), None)

    @override
    async def _list_skill_entries(
        self, context: ServerRequestContext[Any, Any]
    ) -> _Catalog:
        skills = list(await self.list_skills())
        return _Catalog(skills, tuple(skill.uri for skill in skills))

    @override
    async def _get_skill_entry(
        self, uri: str, context: ServerRequestContext[Any, Any]
    ) -> _Lookup:
        skill = await self.get_skill(uri)
        return _Lookup(matches=int(skill is not None), skill=skill)


def _manifest_uris(skill: Skill) -> list[str]:
    if isinstance(skill.resources, list):
        return [resource.uri for resource in skill.resources]
    return [skill.uri]
