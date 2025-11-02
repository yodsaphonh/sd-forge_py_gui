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
   pip install -r requirements.txt
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

   On Windows you can double-click **run.bat** to start the GUI with the default settings.

3. (Optional) If your Forge instance listens on a different host or port, provide the base URL:

   ```bash
   python main.py --api-url http://192.168.0.42:7860
   ```

   The batch script also forwards any extra arguments, so you can run `run.bat --api-url http://192.168.0.42:7860`.

   You can also adjust the API endpoint after launch using the **API base URL** field located above the tabs. The GUI updates its
   connection immediately and remembers the last address you entered for the next session.

## Text-to-Image workflow

- Fill in the prompt and negative prompt fields.
- Select models and samplers from the combo boxes (leave on "Auto" to use the Forge defaults).
- Adjust generation parameters such as steps, CFG scale, width, height, batch size/count, seed, clip skip, and GPU weight budget.
- Press **Generate** to start a job. A progress bar and status line will update using the Forge `/progress` endpoint.
- When finished, the preview image, seed, and full metadata are displayed on the right-hand panel. Use the tabs to switch to Image-to-Image or Image Info workflows.

### Prompt tag auto-completion

- The prompt and negative prompt editors include popup suggestions compatible with the [a1111 tag complete](https://github.com/DominikDoom/a1111-sd-webui-tagcomplete) format.
- A curated starter list of tags ships in `sdforge_gui/data/tagcomplete/tags.csv`. Replace or extend it with your own CSV/JSON/TXT files to customize the vocabulary.
- To reuse the full tag set from the upstream WebUI extension, copy its `tags` directory into `sdforge_gui/data/tagcomplete/` or point the environment variable `SDFORGE_TAGCOMPLETE_PATH` at the extracted repository. Multiple directories can be provided by separating paths with your platform’s path separator (e.g., `;` on Windows, `:` on macOS/Linux).
- Press `Ctrl+Space` inside a prompt box to force the suggestion popup if it does not appear automatically.

### Managing LoRAs

- The **LoRAs** row lists every LoRA reported by `/sdapi/v1/loras` and lets you search by name or alias. Start typing in the dropdown to filter or use the buttons to add the highlighted entry.
- Selected LoRAs appear below the picker with individual weight controls (0.0–2.0 in 0.05 steps) and remove buttons. Adjust weights to fine-tune each network without editing the prompt manually.
- Use **Remove** to drop the highlighted LoRA or **Clear** to empty the entire list. The GUI remembers your last selections and weights between sessions.

### UI customization with `ui-config.json`

- Edit the top-level `ui-config.json` file to toggle controls or preload values without modifying the source code.
- Entries follow the pattern `"<tab>/<control>/<property>"`. For example, the Text-to-Image prompt visibility can be forced with:

  ```json
  {
    "txt2img/Prompt/visible": true,
    "txt2img/Sampling method/value": "Euler a",
    "txt2img/Sampling steps/value": 25,
    "txt2img/CFG scale/value": 6.5
  }
  ```

- Supported properties include `visible`, `enabled`, `value`, `minimum`, `maximum`, and `step`. Control names are matched loosely, so `"Sampling method"` and `"Sampler"` resolve to the same combo box.
- Leave the file as `{}` to keep the default layout. Any configuration errors are reported when the application launches.

## Troubleshooting

- If the GUI immediately reports an API error, confirm that the Forge server is running and the API flag is enabled.
- Progress polling relies on the `/sdapi/v1/progress` endpoint. Some community builds may disable it; in that case the progress bar may stay at 0 until completion.
- Use the terminal where you launched the GUI to inspect detailed Python tracebacks when reporting issues.

## Updating

Run `update.bat` to pull the latest code (when cloned via git) and install/upgrade the Python dependencies listed in `requirements.txt`.
