import subprocess
import glob
import os
import urllib.request
import urllib.parse
import json
from html.parser import HTMLParser
from anthropic import beta_tool

BLOCKED_COMMANDS = {"rm -rf /", ":(){ :|:& };:", "mkfs", "dd if=/dev/zero"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip_tags = {"script", "style", "head", "nav", "footer"}
        self._current_skip = 0
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._current_skip += 1

    def handle_endtag(self, tag):
        if tag in self._skip_tags and self._current_skip > 0:
            self._current_skip -= 1

    def handle_data(self, data):
        if self._current_skip == 0:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


@beta_tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (1-10).
    """
    max_results = min(max(1, max_results), 10)
    encoded = urllib.parse.quote_plus(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ClaudeAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return f"Search failed: {e}"

    results = []
    if data.get("AbstractText"):
        results.append(f"Summary: {data['AbstractText']}")
        if data.get("AbstractURL"):
            results.append(f"Source: {data['AbstractURL']}")

    for item in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(item, dict) and item.get("Text"):
            text = item["Text"][:200]
            url_link = item.get("FirstURL", "")
            results.append(f"- {text}\n  {url_link}")

    return "\n".join(results) if results else f"No results found for: {query}"


@beta_tool
def fetch_url(url: str, extract_text: bool = True) -> str:
    """Fetch the content of a URL.

    Args:
        url: The URL to fetch.
        extract_text: If True, extract readable text from HTML. If False, return raw content.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ClaudeAgent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

    if extract_text and "html" in content_type.lower():
        parser = _TextExtractor()
        parser.feed(raw)
        text = " ".join(parser.text_parts)
        return text[:5000] + ("..." if len(text) > 5000 else "")

    return raw[:5000] + ("..." if len(raw) > 5000 else "")


@beta_tool
def run_shell(command: str, working_dir: str = ".") -> str:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to run.
        working_dir: Directory to run the command in (defaults to current directory).
    """
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return f"Blocked: command contains dangerous pattern '{blocked}'"

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


@beta_tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > 5000:
            return content[:5000] + f"\n... (truncated, file is {len(content)} chars)"
        return content
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Failed to read {path}: {e}"


@beta_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: Path to the file to write.
        content: Content to write to the file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Failed to write {path}: {e}"


@beta_tool
def list_files(directory: str = ".", pattern: str = "*") -> str:
    """List files in a directory matching an optional glob pattern.

    Args:
        directory: Directory to list files in.
        pattern: Glob pattern to filter files (e.g., '*.py', '**/*.txt').
    """
    try:
        matches = glob.glob(os.path.join(directory, pattern), recursive=True)
        matches.sort()
        if not matches:
            return f"No files matching '{pattern}' in {directory}"
        return "\n".join(matches[:100])
    except Exception as e:
        return f"Failed to list files: {e}"


ALL_TOOLS = [web_search, fetch_url, run_shell, read_file, write_file, list_files]
