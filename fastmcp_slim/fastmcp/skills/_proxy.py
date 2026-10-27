"""Skills discovery forwarded to the backend of a `ProxyProvider`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mcp.server.context import ServerRequestContext

from fastmcp.server.dependencies import get_context
from fastmcp.server.providers.base import Provider
from fastmcp.server.providers.proxy import ProxyProvider, ProxyResource, ProxyTemplate
from fastmcp.skills._routing import _may_read, _resolve_read
from fastmcp.skills.models import MCPSkill


class _ProxiedSkills:
    """A skill source that asks a proxy's backend for its Skills entries.

    Entries pass through unchanged. One is kept only when this server serves
    every file in its manifest from the same backend and the caller may read
    each of them, so discovery never advertises a file the caller can't fetch.
    Discovery checks routing without reading any file.
    """

    def __init__(self, provider: ProxyProvider) -> None:
        self._provider = provider

    def _validate_skill_source(self) -> None:
        return None

    def _owns_skill_resource(self, uri: str) -> bool:
        return uri.startswith("skill://")

    async def _skill_uris(self, uri: str | None = None) -> Sequence[str]:
        if uri is None:
            return [entry.uri for entry in await self._listed()]
        entry = await self._fetched(uri)
        return [] if entry is None else [entry.uri]

    async def _list_skill_entries(
        self, context: ServerRequestContext[Any, Any]
    ) -> Sequence[MCPSkill]:
        return [entry for entry in await self._listed() if await self._is_served(entry)]

    async def _get_skill_entry(
        self, uri: str, context: ServerRequestContext[Any, Any]
    ) -> MCPSkill | None:
        entry = await self._fetched(uri)
        if entry is None or not await self._is_served(entry):
            return None
        return entry

    async def _listed(self) -> Sequence[MCPSkill]:
        # skills/list asks for identities and entries separately; one backend
        # call per request answers both.
        state = get_context()._request_state
        key = f"_fastmcp_proxied_skills:{id(self._provider)}"
        if key not in state:
            state[key] = await self._provider._list_skills()
        return state[key]

    async def _fetched(self, uri: str) -> MCPSkill | None:
        state = get_context()._request_state
        key = f"_fastmcp_proxied_skill:{id(self._provider)}:{uri}"
        if key not in state:
            state[key] = await self._provider._get_skill(uri)
        return state[key]

    async def _is_served(self, entry: MCPSkill) -> bool:
        if entry.resources == "dynamic":
            return False
        server = get_context().fastmcp
        for record in entry.resources:
            component = await _resolve_read(server, record.uri)
            # Creating a resource from a proxied template reads the backend, so
            # the template itself counts.
            if not (
                isinstance(component, ProxyResource | ProxyTemplate)
                and component._client_factory is self._provider.client_factory
                and await _may_read(server, record.uri)
            ):
                return False
        return True


def _proxied_source(provider: Provider) -> _ProxiedSkills | None:
    if (
        isinstance(provider, ProxyProvider)
        and provider._skills
        and not provider.transforms
    ):
        return _ProxiedSkills(provider)
    return None
