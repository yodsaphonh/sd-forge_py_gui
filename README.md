# Stable Diffusion Forge Desktop GUI

A PyQt-based desktop interface for driving a running Stable Diffusion Forge instance through its REST API. The application mirrors the common WebUI workflows while providing a native experience with themed tabs for text-to-image, image-to-image, and image inspection.

## Prerequisites

- Python 3.10 or later
- A Stable Diffusion Forge installation configured to expose the API (launch the WebUI with `COMMANDLINE_ARGS= --api` or include `--api` in your start script)
- Model files (checkpoints, VAEs, embeddings, etc.) already installed in your Forge environment

## Installation

1. (Recommended) Create and activate a Python virtual environment.
2. Install the required Python dependencies:

   ```bash
   pip install PyQt6 requests
   ```

3. Clone or download this repository.

## Running the application

1. Ensure your Stable Diffusion Forge server is running with the API enabled and reachable. By default the GUI expects the API at `http://127.0.0.1:7860`.
2. Launch the desktop GUI:

   ```bash
   python -m sdforge_gui.gui.application
   ```

   or run the convenience entry point:

   ```bash
   python main.py
   ```

3. (Optional) If your Forge instance listens on a different host or port, provide the base URL:

   ```bash
   python main.py --api-url http://192.168.0.42:7860
   ```

## Text-to-Image workflow

- Fill in the prompt and negative prompt fields.
- Select models and samplers from the combo boxes (leave on "Auto" to use the Forge defaults).
- Adjust generation parameters such as steps, CFG scale, width, height, batch size/count, seed, clip skip, and GPU weight budget.
- Press **Generate** to start a job. A progress bar and status line will update using the Forge `/progress` endpoint.
- When finished, the preview image, seed, and full metadata are displayed on the right-hand panel. Use the tabs to switch to Image-to-Image or Image Info workflows.

## Troubleshooting

- If the GUI immediately reports an API error, confirm that the Forge server is running and the API flag is enabled.
- Progress polling relies on the `/sdapi/v1/progress` endpoint. Some community builds may disable it; in that case the progress bar may stay at 0 until completion.
- Use the terminal where you launched the GUI to inspect detailed Python tracebacks when reporting issues.
