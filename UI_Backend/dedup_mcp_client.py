import asyncio
import hashlib
import json
import logging
from mcp_use import MCPAgent, MCPClient

logger = logging.getLogger(__name__)

# -------------------------------
# Deduplication MCP Client
# -------------------------------
class DedupMCPClient(MCPClient):
    """
    MCPClient subclass with request-level deduplication.
    Skips duplicate POST/GET/DELETE requests within a short TTL window.
    """
    _dedup_cache = {}
    _cache_lock = asyncio.Lock()
    _CACHE_TTL = 5.0  # seconds

    def _hash_request(self, method: str, endpoint: str, payload: dict | None):
        """Normalize payload and generate a hash key."""
        if payload is None:
            payload = {}

        # Remove transient fields that change each request
        norm_payload = json.loads(json.dumps(payload))
        for key in ["sessionId", "startedAt", "expiresAt", "timestamp", "createdAt", "updatedAt"]:
            if key in norm_payload:
                norm_payload[key] = "<normalized>"

        normalized = json.dumps({
            "method": method.upper(),
            "endpoint": endpoint.strip().lower(),
            "payload": norm_payload,
        }, sort_keys=True)

        return hashlib.md5(normalized.encode()).hexdigest()

    async def _cleanup_cache(self):
        """Remove expired cache entries."""
        async with self._cache_lock:
            now = asyncio.get_event_loop().time()
            expired_keys = [
                key for key, (_, t) in self._dedup_cache.items()
                if now - t > self._CACHE_TTL
            ]
            for key in expired_keys:
                self._dedup_cache.pop(key, None)

    async def _dedup_call(self, method, endpoint, payload=None, *args, **kwargs):
        key = self._hash_request(method, endpoint, payload)
        await self._cleanup_cache()

        async with self._cache_lock:
            if key in self._dedup_cache:
                fut, _ = self._dedup_cache[key]
                logger.info(f"🔄 Deduplicating {method} {endpoint}")
                return await fut

            fut = asyncio.Future()
            self._dedup_cache[key] = (fut, asyncio.get_event_loop().time())

        try:
            result = await super()._send_request(method, endpoint, payload, *args, **kwargs)
            fut.set_result(result)
            return result
        except Exception as e:
            fut.set_exception(e)
            raise
        finally:
            asyncio.create_task(self._cleanup_cache())

    # --- Override MCPClient methods ---
    async def get(self, endpoint, *args, **kwargs):
        return await self._dedup_call("GET", endpoint, None, *args, **kwargs)

    async def post(self, endpoint, payload=None, *args, **kwargs):
        return await self._dedup_call("POST", endpoint, payload, *args, **kwargs)

    async def delete(self, endpoint, payload=None, *args, **kwargs):
        return await self._dedup_call("DELETE", endpoint, payload, *args, **kwargs)


# -------------------------------
# Deduplication MCP Agent
# -------------------------------
class DedupMCPAgent(MCPAgent):
    """
    MCPAgent subclass with query-level deduplication.
    Prevents running the same logical query multiple times concurrently.
    """
    _active_queries = {}
    _lock = asyncio.Lock()

    async def run(self, query_str: str):
        key = hashlib.md5(query_str.strip().encode()).hexdigest()

        async with self._lock:
            if key in self._active_queries:
                logger.info(f"🔄 Deduplicating agent run for query {key[:8]}...")
                return await self._active_queries[key]

            fut = asyncio.Future()
            self._active_queries[key] = fut

        try:
            result = await super().run(query_str)
            fut.set_result(result)
            return result
        except Exception as e:
            fut.set_exception(e)
            raise
        finally:
            async with self._lock:
                self._active_queries.pop(key, None)


# -------------------------------
# Factory function for Quart app
# -------------------------------
async def create_dedup_agent(mcp_url: str, system_prompt, llm):
    """
    Returns a DedupMCPAgent with DedupMCPClient.
    """
    client = DedupMCPClient({
        "mcpServers": {
            "http": {"url": mcp_url}
        }
    })
    await client.create_session("http")

    agent = DedupMCPAgent(
        client=client,
        system_prompt=system_prompt,
        llm=llm,
        verbose=True
    )
    return agent
