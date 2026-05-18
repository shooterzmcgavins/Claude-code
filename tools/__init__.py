from dataclasses import dataclass
from typing import Callable, Union, List
from core.workspace import Workspace

from .web import web_search, fetch_url
from .shell import run_shell, set_approval_callback
from .files import read_file, write_file, list_files
from .workspace_tools import write_report, read_memory, write_memory, init_workspace_tools


@dataclass
class ToolDef:
    name: str
    description: str
    input_schema: dict
    fn: Callable

    def __call__(self, **kwargs):
        return self.fn(**kwargs)


ALL_TOOLS: list["ToolDef"] = [
    ToolDef(
        name="web_search",
        description="Search the web using DuckDuckGo and return results.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-10).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        fn=web_search,
    ),
    ToolDef(
        name="fetch_url",
        description="Fetch the content of a URL.",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch."},
                "extract_text": {
                    "type": "boolean",
                    "description": "Extract readable text from HTML (True) or return raw content (False).",
                    "default": True,
                },
            },
            "required": ["url"],
        },
        fn=fetch_url,
    ),
    ToolDef(
        name="run_shell",
        description="Execute a shell command and return its output. Always requires user approval.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."},
                "working_dir": {
                    "type": "string",
                    "description": "Directory to run the command in.",
                    "default": ".",
                },
            },
            "required": ["command"],
        },
        fn=run_shell,
    ),
    ToolDef(
        name="read_file",
        description="Read the contents of a file.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read."},
            },
            "required": ["path"],
        },
        fn=read_file,
    ),
    ToolDef(
        name="write_file",
        description="Write content to a file, creating parent directories as needed.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to write."},
                "content": {"type": "string", "description": "Content to write to the file."},
            },
            "required": ["path", "content"],
        },
        fn=write_file,
    ),
    ToolDef(
        name="list_files",
        description="List files in a directory matching an optional glob pattern.",
        input_schema={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to list.",
                    "default": ".",
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g. *.py, **/*.md).",
                    "default": "*",
                },
            },
            "required": [],
        },
        fn=list_files,
    ),
    ToolDef(
        name="write_report",
        description="Write a task report to the workspace reports directory.",
        input_schema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The task ID this report belongs to (e.g. TASK-A1B2C3).",
                },
                "content": {
                    "type": "string",
                    "description": "The markdown content of the report.",
                },
            },
            "required": ["task_id", "content"],
        },
        fn=write_report,
    ),
    ToolDef(
        name="read_memory",
        description="Read a memory entry from the workspace memory store.",
        input_schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Memory key to read. Use 'index' to list all available memory keys.",
                },
            },
            "required": ["key"],
        },
        fn=read_memory,
    ),
    ToolDef(
        name="write_memory",
        description="Persist information to the workspace memory store for future reference.",
        input_schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Memory key (lowercase with hyphens). Overwrites any existing entry.",
                },
                "content": {
                    "type": "string",
                    "description": "Markdown content to store.",
                },
            },
            "required": ["key", "content"],
        },
        fn=write_memory,
    ),
]

_TOOL_MAP = {t.name: t for t in ALL_TOOLS}


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
