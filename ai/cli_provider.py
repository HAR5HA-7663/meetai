"""AI provider that shells out to CLI tools: claude, codex, gemini."""

import subprocess
import logging
import shutil
import threading
from ai.provider import AIProvider

logger = logging.getLogger(__name__)


class CLIProvider(AIProvider):
    """Runs AI queries through locally installed CLI tools."""

    TOOL_COMMANDS = {
        "claude": {
            "text": ["claude", "-p", "{prompt}"],
            "image": ["claude", "-p", "{prompt}"],  # Claude supports image refs in prompt
        },
        "codex": {
            "text": ["codex", "exec", "{prompt}"],
            "image": ["codex", "exec", "{prompt}"],
        },
        "gemini": {
            "text": ["gemini", "-p", "{prompt}"],
            "image": ["gemini", "-p", "{prompt}"],
        },
    }

    def __init__(self, tool: str = "claude"):
        self.tool = tool
        if not shutil.which(self._get_binary()):
            logger.warning(f"CLI tool '{tool}' not found in PATH")

    def _get_binary(self) -> str:
        return self.tool

    def _build_prompt(self, prompt: str, context: str = "") -> str:
        if context:
            return f"{context}\n\n---\n\n{prompt}"
        return prompt

    def _run_cli(self, args: list[str], timeout: int = 120) -> str:
        """Run a CLI command and return stdout."""
        try:
            logger.info(f"Running: {args[0]} (prompt length: {len(args[-1])} chars)")
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=None,  # Inherit parent env (has API keys etc.)
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if stderr:
                    logger.error(f"CLI error: {stderr[:500]}")
                # Still return stdout if available
                if result.stdout.strip():
                    return result.stdout.strip()
                return f"Error: {stderr[:200]}" if stderr else "Error: CLI command failed"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"CLI command timed out after {timeout}s")
            return "Error: AI response timed out"
        except FileNotFoundError:
            logger.error(f"CLI tool '{args[0]}' not found")
            return f"Error: '{args[0]}' not installed or not in PATH"
        except Exception as e:
            logger.error(f"CLI execution failed: {e}")
            return f"Error: {str(e)}"

    def get_response(self, prompt: str, context: str = "") -> str:
        full_prompt = self._build_prompt(prompt, context)
        cmd = [self._get_binary(), "-p" if self.tool != "codex" else "exec", full_prompt]
        if self.tool == "codex":
            cmd = ["codex", "exec", full_prompt]
        return self._run_cli(cmd)

    def analyze_image(self, image_path: str, prompt: str, context: str = "") -> str:
        """Analyze an image using the CLI tool.

        For Claude: we reference the image path in the prompt.
        Claude CLI can handle image paths when passed correctly.
        """
        full_prompt = self._build_prompt(prompt, context)

        if self.tool == "claude":
            # Claude Code can read images when given a file path
            image_prompt = f"Look at this screenshot: {image_path}\n\n{full_prompt}"
            cmd = ["claude", "-p", image_prompt]
        elif self.tool == "gemini":
            image_prompt = f"Analyze the image at {image_path}:\n\n{full_prompt}"
            cmd = ["gemini", "-p", image_prompt]
        else:
            # Codex doesn't support images well, fall back to claude
            image_prompt = f"Look at this screenshot: {image_path}\n\n{full_prompt}"
            cmd = ["claude", "-p", image_prompt]

        return self._run_cli(cmd, timeout=180)

    def stream_response(self, prompt: str, context: str = "", callback=None) -> str:
        """Stream response by reading stdout line-by-line."""
        full_prompt = self._build_prompt(prompt, context)
        cmd = [self._get_binary()]
        if self.tool == "codex":
            cmd += ["exec", full_prompt]
        else:
            cmd += ["-p", full_prompt]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            full_response = []
            for line in process.stdout:
                line = line.rstrip("\n")
                full_response.append(line)
                if callback:
                    callback(line + "\n")

            process.wait(timeout=180)
            return "\n".join(full_response)
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            return f"Error: {str(e)}"


def get_provider(tool: str = "claude") -> CLIProvider:
    """Factory function to get a CLI provider."""
    return CLIProvider(tool=tool)
