from typing import Union, List
from core.workspace import Workspace

from .web import web_search, fetch_url
from .shell import run_shell, set_approval_callback
from .files import read_file, write_file, list_files
from .workspace_tools import write_report, read_memory, write_memory, init_workspace_tools

ALL_TOOLS = [
    web_search, fetch_url,
    run_shell,
    read_file, write_file, list_files,
    write_report, read_memory, write_memory,
]
_TOOL_MAP = {t.__name__: t for t in ALL_TOOLS}


def get_tools(
    spec: Union[str, List[str]],
    workspace: Workspace,
    approval_callback=None,
) -> list:
    init_workspace_tools(workspace)
    if approval_callback:
        set_approval_callback(approval_callback)
    if spec == "all" or spec == ["all"]:
        return ALL_TOOLS
    if isinstance(spec, list):
        return [_TOOL_MAP[n] for n in spec if n in _TOOL_MAP]
    return ALL_TOOLS
