import os
import shutil
import subprocess
import sys
import tempfile

from mcp.server.fastmcp import FastMCP

# Always run from the project directory (portable, no machine-specific paths).
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

# Base directory for MCP-generated files.
BASE_DIR = os.path.join(PROJECT_DIR, "media")
os.makedirs(BASE_DIR, exist_ok=True)


def log(*args) -> None:
    """Diagnostics go to stderr; stdout is reserved for the MCP stdio protocol."""
    print(*args, file=sys.stderr, flush=True)


log("MANIM_EXECUTABLE =", os.environ.get("MANIM_EXECUTABLE"))
log("PYTHON =", sys.executable)
log("CWD =", os.getcwd())
log("TEMP =", os.environ.get("TEMP"))

mcp = FastMCP("manim-server")


@mcp.tool()
def execute_manim_code(manim_code: str) -> str:
    """
    Execute Manim code and generate the resulting video.
    """
    # Unique directory for every request
    tmpdir = tempfile.mkdtemp(prefix="manim_", dir=BASE_DIR)
    script_path = os.path.join(tmpdir, "scene.py")

    try:
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(manim_code)

        env = os.environ.copy()
        env["MEDIA_DIR"] = os.path.join(tmpdir, "media")
        os.makedirs(env["MEDIA_DIR"], exist_ok=True)

        # Rendering uses the current Python, so Manim must be installed
        # in the same environment that launches this server.
        command = [sys.executable, "-m", "manim", "-ql", script_path]

        log("\n" + "=" * 40)
        log("STARTING MANIM")
        log("PYTHON =", sys.executable)
        log("COMMAND =", command)
        log("WORKDIR =", tmpdir)
        log("MEDIA_DIR =", env["MEDIA_DIR"])

        # stdin=DEVNULL stops the Manim child process from inheriting the
        # MCP server's stdin (important for stdio clients such as Claude).
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmpdir,
            env=env,
            timeout=60,
        )

        log("MANIM FINISHED")
        log("MANIM RETURN CODE =", result.returncode)
        log("MANIM STDOUT =", result.stdout)
        log("MANIM STDERR =", result.stderr)

        if result.returncode == 0:
            # Skip partial_movie_files: those are intermediate, not the final video.
            video_files = []
            for root, dirs, files in os.walk(tmpdir):
                dirs[:] = [d for d in dirs if d != "partial_movie_files"]
                video_files += [
                    os.path.join(root, name)
                    for name in files
                    if name.lower().endswith(".mp4")
                ]

            log("GENERATED VIDEOS =", video_files)

            if video_files:
                return (
                    "Execution successful. Video generated.\n\n"
                    f"Video: {video_files[0]}\n\n"
                    f"Output directory: {tmpdir}"
                )

            return (
                "Manim completed successfully, but no MP4 file was found.\n\n"
                f"Output directory: {tmpdir}\n\n"
                f"STDOUT:\n{result.stdout}"
            )

        return (
            "Execution failed.\n\n"
            f"Return code: {result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    except subprocess.TimeoutExpired as e:
        log("MANIM TIMEOUT")
        return (
            "Manim execution timed out after 60 seconds.\n\n"
            f"Temporary directory:\n{tmpdir}\n\n"
            f"Partial stdout:\n{e.stdout or ''}\n\n"
            f"Partial stderr:\n{e.stderr or ''}"
        )

    except Exception as e:
        log("MCP MANIM ERROR =", repr(e))
        return (
            "Error during Manim execution:\n"
            f"{repr(e)}\n\n"
            f"Temporary directory:\n{tmpdir}"
        )


@mcp.tool()
def cleanup_manim_temp_dir(directory: str) -> str:
    """
    Clean up a Manim temporary directory after execution.
    """
    try:
        # Safety check: only directories inside the media folder may be deleted.
        target = os.path.realpath(directory)
        base = os.path.realpath(BASE_DIR)

        if os.path.commonpath([target, base]) != base or target == base:
            return (
                "Refusing to delete a directory outside the "
                f"server media folder: {directory}"
            )

        if os.path.exists(directory):
            shutil.rmtree(directory)
            return f"Cleanup successful for directory: {directory}"

        return f"Directory not found: {directory}"

    except Exception as e:
        return f"Failed to clean up directory: {directory}. Error: {str(e)}"


if __name__ == "__main__":
    log("Starting Manim MCP server...")
    mcp.run(transport="stdio")
