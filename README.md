# Manim MCP Server

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

![Manim MCP Demo](Demo-manim-mcp.gif)

An MCP server that lets AI assistants create and render [Manim](https://www.manim.community/) mathematical animations.

It connects an MCP-compatible AI client such as Claude Desktop to Manim: the AI writes a Manim scene, the server renders it, and you get back the path to the generated video.

## Architecture

```
Claude Desktop
       |
       | MCP (stdio)
       v
Manim MCP Server  (src/manim_server.py)
       |
       | python -m manim -ql scene.py
       v
Manim
       |
       v
Generated Animation (.mp4)
```

## Tools

The server exposes exactly two MCP tools.

### `execute_manim_code`

| | |
|---|---|
| **Purpose** | Render a Manim scene and return the resulting video path. |
| **Input** | `manim_code` (string): complete Python source containing one or more Manim scene classes. |
| **Output** | Text with the path of the generated `.mp4` and the output directory, or the return code, stdout and stderr if rendering failed. |
| **Notes** | Renders at low quality (`-ql`). Each request gets its own directory under `src/media/`. Rendering is limited to 60 seconds. |

Example input:

```python
from manim import *

class Demo(Scene):
    def construct(self):
        self.play(Write(Text("Hello")))
```

### `cleanup_manim_temp_dir`

| | |
|---|---|
| **Purpose** | Delete a render directory created by `execute_manim_code`. |
| **Input** | `directory` (string): the "Output directory" path returned by `execute_manim_code`. |
| **Output** | A success, not-found, or error message. |
| **Notes** | Only directories inside the server's `src/media/` folder can be deleted. |

## Requirements

- Python 3.10 or newer (required by the `mcp` package)
- [Manim Community](https://docs.manim.community/en/stable/installation.html) (`manim`)
- `mcp` (includes `FastMCP`)
- Manim's own system dependencies (FFmpeg, Cairo/Pango; see the Manim install guide)
- **Optional:** a LaTeX distribution, only needed for `MathTex`/`Tex`. Scenes that use only `Text`, shapes, axes and graphs do not need it.

**Platform:** developed and tested on **Windows** with Claude Desktop. Linux and macOS have not been tested; the server code itself is plain Python, but paths and commands in this guide may need adjusting.

## Installation

### 1. Clone the repository

```sh
git clone https://github.com/Ankitchopradk/manim-mcp-server.git
cd manim-mcp-server
```

### 2. Create a virtual environment

Windows:

```sh
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS (untested):

```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```sh
pip install -r requirements.txt
```

This installs Manim and the MCP SDK into the same environment. That matters: the server renders by running `python -m manim` with the *same* Python that launches it, so Manim must be installed in that environment.

### 4. Verify Manim

```sh
manim --version
```

You should see a version line such as `Manim Community v0.x.x`.

## Test the server

```sh
python src/manim_server.py
```

On success it prints diagnostics to stderr (including `Starting Manim MCP server...`) and then waits silently for MCP messages on stdin. That is normal; press `Ctrl+C` to stop.

To try the tools interactively, you can use the MCP Inspector (requires the MCP CLI extra, not verified for this project):

```sh
pip install "mcp[cli]"
mcp dev src/manim_server.py
```

## Claude Desktop Configuration

Claude Desktop reads MCP servers from `claude_desktop_config.json`. You can also open it via **Settings > Developer > Edit Config**.

| Installation | Config location |
|---|---|
| Normal installer (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Microsoft Store / MSIX (Windows) | `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude\claude_desktop_config.json` |
| macOS (untested) | `~/Library/Application Support/Claude/claude_desktop_config.json` |

The MSIX package folder name contains an ID that differs per machine; look for a folder beginning with `Claude_` under `%LOCALAPPDATA%\Packages`. Using **Edit Config** in the app opens the correct file for your installation.

### Copy-paste configuration

```json
{
  "mcpServers": {
    "manim-server": {
      "command": "C:\\path\\to\\your\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\manim-mcp-server\\src\\manim_server.py"
      ],
      "env": {
        "MANIM_EXECUTABLE": "C:\\path\\to\\your\\.venv\\Scripts\\manim.exe",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Replace the three `C:\\path\\to\\...` values with the paths on your computer. Do not copy the paths from this example literally.** In JSON, every backslash must be doubled (`\\`).

- `command`: the Python inside the virtual environment where you installed the dependencies.
- `args`: the full path to `src/manim_server.py` in your clone.
- `MANIM_EXECUTABLE`: optional and informational. It is printed in the startup log; rendering itself uses `python -m manim`.

Claude Desktop needs **absolute paths** here; relative paths are not reliable because the app does not launch the server from your project folder.

Find the paths (with the virtual environment activated):

```sh
where python
where manim
```

Or from the repository root in PowerShell: `(Resolve-Path .venv\Scripts\python.exe).Path` and `(Resolve-Path src\manim_server.py).Path`.

Then **fully quit and restart Claude Desktop** (including the tray icon). The `manim-server` tools should then appear in the tools menu.

## Using Manim MCP with Claude

Once connected, just ask in natural language. Claude writes the Manim scene and calls `execute_manim_code`. Try:

- "Create a simple animation showing the Pythagorean theorem."
- "Create a 3D animation explaining vectors."
- "Animate a sine wave and show how its amplitude changes."
- "Create a coordinate system and animate a point moving along a parabola."
- "Explain matrix multiplication visually using Manim."
- "Create a 3D visualization of a vector and its components."

Tip: ask Claude to avoid `MathTex`/`Tex` unless you have LaTeX installed, and to keep scenes short so they finish within the 60 second limit. When you're done, ask Claude to clean up the render folder (`cleanup_manim_temp_dir`).

## Examples

The `examples/` folder has small, fast scenes. To render one locally:

```sh
manim -ql examples/02_function_graph.py FunctionGraph
```

- `01_text_and_shapes.py`: text and shape animation
- `02_function_graph.py`: axes, a parabola, and a moving dot
- `03_simple_3d.py`: a lightweight 3D scene

## Performance notes

- Rendering is always low quality (`-ql`), and each request is limited to 60 seconds.
- `Text`, `Line`, `Dot`, and `VGroup` animations are fast.
- Complex 3D geometry is slower; `Arrow3D` and `Line3D` can be especially expensive.
- Keep scenes short while iterating, and lower surface resolution in 3D scenes.

## Troubleshooting

| Problem | Cause | Solution | Verify |
|---|---|---|---|
| Claude doesn't detect the server | Config not loaded, invalid JSON, or Claude not fully restarted | Fix the JSON, quit Claude completely, reopen | `python -c "import json,sys; json.load(open(sys.argv[1]))" <config path>` |
| Config not loading | Editing the wrong file (normal vs MSIX install) | Use **Settings > Developer > Edit Config** | The `manim-server` entry appears in Claude's developer settings |
| Python executable not found | Wrong `command` path or single backslashes | Use the full path with doubled `\\` | `where python` (venv activated) |
| Manim executable not found / `No module named manim` | Manim is not installed in the Python environment named in `command` | Install `requirements.txt` into that same environment | `<that python> -m manim --version` |
| Permission/path problems on Windows | Repo in a protected or synced folder, or paths with special characters | Clone to a normal user folder | Server starts from the command line |
| Claude times out | Scene takes over 60 seconds | Simplify the scene, use less 3D | Render it locally with `manim -ql` and time it |
| Rendering takes too long | Heavy 3D objects, long scenes | See Performance notes | As above |
| LaTeX / MathTex errors | No LaTeX installed | Install LaTeX or use `Text` instead | `latex --version` |
| Server crashes on startup | Missing dependency or Python < 3.10 | Reinstall requirements; check the Claude MCP log | `python src/manim_server.py` |
| Inspector port problems | Port already in use | Close other inspector instances and retry | Re-run `mcp dev src/manim_server.py` |

### Why `stdin=subprocess.DEVNULL`?

The MCP server talks to Claude over stdin/stdout. If the Manim subprocess inherits that stdin it can consume or block on MCP messages, causing timeouts. The server therefore runs Manim with `stdin=subprocess.DEVNULL` and captured stdout/stderr. Do not remove this.

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b add-feature`
3. Commit your changes and push to your fork.
4. Open a pull request.

## License

MIT License. See [LICENSE](LICENSE).

## Credits

Originally created by [abhiemj](https://github.com/abhiemj) and listed in [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers). Thanks to the [Manim Community](https://www.manim.community/) for the animation library.
