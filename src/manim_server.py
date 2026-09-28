import subprocess
import tempfile
import os
import sys
import shutil

from mcp.server.fastmcp import FastMCP


# ============================================================
# SERVER CONFIGURATION
# ============================================================

# Directory containing this file.
# This keeps the server portable and avoids machine-specific paths.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Make sure the MCP server always starts from its own project directory.
os.chdir(PROJECT_DIR)


# ============================================================
# DIAGNOSTICS
# ============================================================

print(
    "MANIM_EXECUTABLE =",
    os.environ.get("MANIM_EXECUTABLE"),
    file=sys.stderr,
    flush=True
)

print(
    "PYTHON =",
    sys.executable,
    file=sys.stderr,
    flush=True
)

print(
    "CWD =",
    os.getcwd(),
    file=sys.stderr,
    flush=True
)

print(
    "TEMP =",
    os.environ.get("TEMP"),
    file=sys.stderr,
    flush=True
)


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP("manim-server")


# ============================================================
# MANIM CONFIGURATION
# ============================================================

# Informational only.
#
# Rendering is performed using:
#
#     <current Python> -m manim
#
# Therefore, Manim must be installed in the same Python
# environment that launches this MCP server.
MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE")


# Base directory for MCP-generated files.
BASE_DIR = os.path.join(
    PROJECT_DIR,
    "media"
)

os.makedirs(
    BASE_DIR,
    exist_ok=True
)


# Track temporary directories so they can be cleaned later.
TEMP_DIRS = {}


# ============================================================
# EXECUTE MANIM CODE
# ============================================================

@mcp.tool()
def execute_manim_code(manim_code: str) -> str:
    """
    Execute Manim code and generate the resulting video.
    """

    # --------------------------------------------------------
    # Create a unique directory for every request
    # --------------------------------------------------------

    tmpdir = tempfile.mkdtemp(
        prefix="manim_",
        dir=BASE_DIR
    )

    script_path = os.path.join(
        tmpdir,
        "scene.py"
    )

    try:

        # ----------------------------------------------------
        # Write the generated Manim code
        # ----------------------------------------------------

        with open(
            script_path,
            "w",
            encoding="utf-8"
        ) as script_file:

            script_file.write(manim_code)


        # ----------------------------------------------------
        # Configure Manim media directory
        # ----------------------------------------------------

        env = os.environ.copy()

        env["MEDIA_DIR"] = os.path.join(
            tmpdir,
            "media"
        )

        os.makedirs(
            env["MEDIA_DIR"],
            exist_ok=True
        )


        # ----------------------------------------------------
        # Manim command
        # ----------------------------------------------------

        command = [
            sys.executable,
            "-m",
            "manim",
            "-ql",
            script_path
        ]


        # ----------------------------------------------------
        # Diagnostics
        # ----------------------------------------------------

        print(
            "",
            file=sys.stderr,
            flush=True
        )

        print(
            "========================================",
            file=sys.stderr,
            flush=True
        )

        print(
            "STARTING MANIM",
            file=sys.stderr,
            flush=True
        )

        print(
            "PYTHON =",
            sys.executable,
            file=sys.stderr,
            flush=True
        )

        print(
            "COMMAND =",
            command,
            file=sys.stderr,
            flush=True
        )

        print(
            "WORKDIR =",
            tmpdir,
            file=sys.stderr,
            flush=True
        )

        print(
            "MEDIA_DIR =",
            env["MEDIA_DIR"],
            file=sys.stderr,
            flush=True
        )

        print(
            "STDIN REDIRECTED = DEVNULL",
            file=sys.stderr,
            flush=True
        )


        # ----------------------------------------------------
        # Run Manim
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # stdin=subprocess.DEVNULL prevents the Manim child
        # process from inheriting the MCP server's stdin.
        #
        # This is important when the MCP server is running
        # through a stdio-based MCP client such as Claude.
        # ----------------------------------------------------

        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmpdir,
            env=env,
            timeout=60
        )


        # ----------------------------------------------------
        # Manim finished
        # ----------------------------------------------------

        print(
            "MANIM FINISHED",
            file=sys.stderr,
            flush=True
        )

        print(
            "MANIM RETURN CODE =",
            result.returncode,
            file=sys.stderr,
            flush=True
        )

        print(
            "MANIM STDOUT =",
            result.stdout,
            file=sys.stderr,
            flush=True
        )

        print(
            "MANIM STDERR =",
            result.stderr,
            file=sys.stderr,
            flush=True
        )


        # ----------------------------------------------------
        # Successful execution
        # ----------------------------------------------------

        if result.returncode == 0:

            TEMP_DIRS[tmpdir] = True


            # ------------------------------------------------
            # Find final generated MP4 files
            # ------------------------------------------------
            #
            # Manim creates intermediate files inside:
            #
            #     partial_movie_files
            #
            # These are NOT the final video.
            #
            # We therefore exclude that directory.
            # ------------------------------------------------

            video_files = []

            for root, dirs, files in os.walk(tmpdir):

                # Prevent os.walk from entering Manim's
                # intermediate partial movie directory.
                dirs[:] = [
                    directory
                    for directory in dirs
                    if directory != "partial_movie_files"
                ]

                for filename in files:

                    if filename.lower().endswith(".mp4"):

                        video_files.append(
                            os.path.join(
                                root,
                                filename
                            )
                        )


            # ------------------------------------------------
            # Display generated videos for diagnostics
            # ------------------------------------------------

            print(
                "GENERATED VIDEOS =",
                video_files,
                file=sys.stderr,
                flush=True
            )


            # ------------------------------------------------
            # Return final video
            # ------------------------------------------------

            if video_files:

                # Because partial_movie_files has been excluded,
                # the remaining MP4 should be the final combined
                # Manim video.

                video_path = video_files[0]

                return (
                    "Execution successful. Video generated.\n\n"
                    f"Video: {video_path}\n\n"
                    f"Output directory: {tmpdir}"
                )


            # ------------------------------------------------
            # No MP4 found
            # ------------------------------------------------

            else:

                return (
                    "Manim completed successfully, "
                    "but no MP4 file was found.\n\n"
                    f"Output directory: {tmpdir}\n\n"
                    f"STDOUT:\n{result.stdout}"
                )


        # ----------------------------------------------------
        # Manim failed
        # ----------------------------------------------------

        return (
            "Execution failed.\n\n"
            f"Return code: {result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


    # --------------------------------------------------------
    # Timeout
    # --------------------------------------------------------

    except subprocess.TimeoutExpired as e:

        print(
            "MANIM TIMEOUT",
            file=sys.stderr,
            flush=True
        )

        return (
            "Manim execution timed out after 60 seconds.\n\n"
            f"Temporary directory:\n{tmpdir}\n\n"
            f"Partial stdout:\n{e.stdout or ''}\n\n"
            f"Partial stderr:\n{e.stderr or ''}"
        )


    # --------------------------------------------------------
    # Other errors
    # --------------------------------------------------------

    except Exception as e:

        print(
            "MCP MANIM ERROR =",
            repr(e),
            file=sys.stderr,
            flush=True
        )

        return (
            "Error during Manim execution:\n"
            f"{repr(e)}\n\n"
            f"Temporary directory:\n{tmpdir}"
        )


# ============================================================
# CLEANUP TOOL
# ============================================================

@mcp.tool()
def cleanup_manim_temp_dir(directory: str) -> str:
    """
    Clean up a Manim temporary directory after execution.
    """

    try:

        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------
        #
        # Only directories inside the server's media directory
        # are allowed to be deleted.
        # ----------------------------------------------------

        target = os.path.realpath(directory)
        base = os.path.realpath(BASE_DIR)

        if (
            os.path.commonpath([target, base]) != base
            or target == base
        ):

            return (
                "Refusing to delete a directory outside the "
                f"server media folder: {directory}"
            )


        # ----------------------------------------------------
        # Delete directory
        # ----------------------------------------------------

        if os.path.exists(directory):

            shutil.rmtree(directory)

            TEMP_DIRS.pop(
                directory,
                None
            )

            return (
                f"Cleanup successful for directory: {directory}"
            )


        else:

            return (
                f"Directory not found: {directory}"
            )


    except Exception as e:

        return (
            f"Failed to clean up directory: {directory}. "
            f"Error: {str(e)}"
        )


# ============================================================
# START MCP SERVER
# ============================================================

if __name__ == "__main__":

    print(
        "Starting Manim MCP server...",
        file=sys.stderr,
        flush=True
    )

    mcp.run(
        transport="stdio"
    )