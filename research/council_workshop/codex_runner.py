"""One isolated, structured decision through the user's ChatGPT login."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


MODELS = ("gpt-6.2-astra", "gpt-6.2-sol", "gpt-6-astra", "gpt-6.1-sol")


def subscription_env():
    # Inherit only what the CLI needs to find the executable and saved login.
    names = ("PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG", "LC_ALL", "USER",
             "SystemRoot", "LOCALAPPDATA", "APPDATA")
    return {name: os.environ[name] for name in names if name in os.environ}


def failure_detail(root, stderr):
    """Prefer a provider error from the CLI event stream over a generic exit code."""
    messages = [line for line in stderr.splitlines() if line.startswith("ERROR:")]
    for line in (root / "events.jsonl").read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # A timeout can interrupt the last event.
        if event.get("type") == "error":
            messages.append(event.get("message", ""))
        elif event.get("type") == "turn.failed":
            messages.append(event.get("error", {}).get("message", ""))
    return next((message[:400] for message in reversed(messages) if message), "")


class CodexRunner:
    def __init__(self, model, executable=None, timeout=360):
        if model not in MODELS:
            raise ValueError(f"Unsupported model: {model}")
        self.model = model
        self.timeout = timeout
        desktop = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")
        self.executable = executable or (str(desktop) if desktop.is_file() else shutil.which("codex"))
        if not self.executable:
            raise RuntimeError("Install the Codex CLI or pass --codex /path/to/codex.")
        self.executable = str(Path(self.executable).resolve())
        self.env = subscription_env()
        status = subprocess.run([self.executable, "login", "status"], env=self.env, timeout=20,
                                capture_output=True, text=True)
        lines = (status.stdout + "\n" + status.stderr).splitlines()
        if status.returncode or "Logged in using ChatGPT" not in (line.strip() for line in lines):
            raise RuntimeError("Run 'codex login' and select ChatGPT subscription sign-in.")

    def __call__(self, prompt, schema):
        with tempfile.TemporaryDirectory(prefix="council-codex-") as directory:
            root = Path(directory)
            (root / "schema.json").write_text(json.dumps(schema))
            command = [
                self.executable, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                "--skip-git-repo-check", "--sandbox", "read-only", "--model", self.model,
                "-c", 'forced_login_method="chatgpt"', "-c", 'model_provider="openai"',
                "-c", 'web_search="disabled"', "-c", 'model_reasoning_effort="low"',
                "--disable", "shell_tool", "--disable", "unified_exec",
                "--disable", "multi_agent", "--disable", "plugins",
                "--json", "--output-schema", "schema.json", "--output-last-message", "answer.json", "-",
            ]
            try:
                with (root / "events.jsonl").open("w") as events:
                    result = subprocess.run(command, cwd=root, env=self.env, input=prompt, text=True,
                                            stdout=events, stderr=subprocess.PIPE, timeout=self.timeout)
            except subprocess.TimeoutExpired as error:
                detail = failure_detail(root, (error.stderr or b"").decode(errors="replace"))
                raise RuntimeError(f"{self.model} timed out after {self.timeout} seconds. {detail}".strip()) from error
            if result.returncode:
                detail = failure_detail(root, result.stderr) or f"exit code {result.returncode}"
                raise RuntimeError(f"Codex failed for {self.model}: {detail}")
            return json.loads((root / "answer.json").read_text())
