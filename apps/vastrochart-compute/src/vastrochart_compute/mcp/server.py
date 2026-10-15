"""FastMCP server instance. `tools` is imported at the bottom purely for
its import-time side effect (the @mcp.tool decorators registering each
tool on this instance) - keep that import last, after `mcp` exists.
"""

from fastmcp import FastMCP

mcp = FastMCP(name="VAstroChart", version="0.1.0")

from vastrochart_compute.mcp import tools  # noqa: E402,F401
