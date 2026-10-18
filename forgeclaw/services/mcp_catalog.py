"""Built-in MCP tool catalog; executable tools live in forgeclaw.mcp_server."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MCPToolInfo:
    name: str
    description: str
    safety: str


BUILTIN_MCP_TOOLS: tuple[MCPToolInfo, ...] = (
    MCPToolInfo("workspace_tree", "List project files while excluding caches and secrets.", "read-only"),
    MCPToolInfo("read_file", "Read a text file contained inside the configured workspace.", "read-only; path sandboxed"),
    MCPToolInfo("search_files", "Search project text files for a query.", "read-only; bounded results"),
    MCPToolInfo("git_status", "Read the current Git status and branch.", "read-only"),
    MCPToolInfo("git_diff", "Read a bounded Git diff for review.", "read-only"),
    MCPToolInfo("run_tests", "Run only configured test commands such as pytest.", "execution; allowlisted commands only"),
)


def list_mcp_tools() -> list[dict[str, str]]:
    return [asdict(tool) for tool in BUILTIN_MCP_TOOLS]
