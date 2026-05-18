import subprocess
from typing import Optional, Callable

_BLOCKED = {"rm -rf /", ":(){ :|:& };:", "mkfs", "dd if=/dev/zero", "> /dev/sda"}
_approval_callback: Optional[Callable[[str, str, str], bool]] = None


def set_approval_callback(fn: Optional[Callable[[str, str, str], bool]]) -> None:
    """Set a callback that approves shell commands before execution.

    The callback receives (agent_name, action_type, details) and returns True to allow.
    """
    global _approval_callback
    _approval_callback = fn


def run_shell(command: str, working_dir: str = ".") -> str:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to execute.
        working_dir: Directory to run the command in (defaults to current directory).
    """
    for blocked in _BLOCKED:
        if blocked in command:
            return f"Blocked: command contains dangerous pattern '{blocked}'"

    if _approval_callback:
        allowed = _approval_callback("agent", "shell", command)
        if not allowed:
            return "Command rejected."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=working_dir,
        )
        output = result.stdout + result.stderr
        return output[:5000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Command failed: {e}"
