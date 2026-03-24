# Copilot Instructions for `python_aspendyn_get_data`

## Project Context & Architecture

This codebase manages an automated chemical engineering simulation for a Claus plant using **Aspen Dynamics**. 
The architecture follows an orchestrator-environment pattern similar to reinforcement learning or OpenAI Gym:
- **Environment (`claus_plant_flow_record*.py`)**: Wraps the Aspen Dynamics COM interface (`win32com.client.Dispatch`). It handles getting and setting simulation states (e.g., `get_composition`, `run_step`, `get_initial_setpoints`).
- **Orchestrator (`main_claus_flow_record*.py`)**: The entry points that manage loop variables (`MAX_EP_STEPS`, `dt`, configuration for disturbances) and log telemetry to Pandas DataFrames.
  - *Distinction between versions*: `main_claus_flow_record.py` (and its environment script without "senpai") is explicitly designed to run single-step change experiments (e.g., 1440 steps). Meanwhile, `main_claus_flow_record_senpai.py` is configured for broader multi-variable (MV) random variation experiments over extended episodes (e.g., 5 episodes x 1440 steps).
- **Data Analysis / ML**: Post-processing scripts (e.g., `predict_totalS.py`, `regression_totalS.py`, `plot_*.py`) read output CSVs to train regression models or map correlations.

## Important Conventions & Patterns

### 1. COM Interface Interactions
Interaction with Aspen Dynamics happens exclusively through `win32com.client`. 
- Be aware of the COM IDs used (`'AD Application'`, `'AspenModeler.Application'`, etc.).
- When adding new parameters to read/write, define them systematically in `Env.get_*_composition()` inside the `claus_plant_flow_record` files and ensure they are added to the orchestrator's Pandas `index_columns` list.

### 2. Output and Data Collection
Simulation outputs are consistently captured in large matrices (`numpy` arrays mapped to `pandas` DataFrame) and persisted step-by-step:
- **CSV saving logic**: Look closely at how files and directories are formatted. For repetitive script runs (like `main_claus_flow_record_senpai.py`), we often use automated numbering logic (e.g., parsing folder via `glob` to find the highest integer suffix) instead of overwriting files.
- Remember to maintain the exact alignment between `np.concatenate([...])` dimensions in `Env` and the corresponding `index_columns` arrays in the `main_*.py` files.

### 3. Execution & Workflow
- Use standard Python invocation, usually configured in typical `.venv` environments. Example: `uv run python main_claus_flow_record.py`.
- **Debugging Tip:** Changes in COM automation scripts can crash the Aspen Dynamics process or hang the Python script silently. Ensure the Aspen GUI (`adyn.Visible = True`) is handled properly. Note that `.dynf` and `.apwz` files are located in the `ASPen_file/` directory.

### 4. Naming Guidelines
- Avoid hard-coding repetitive strings. Use variables like `PROJECT_NAME`, `OUTPUT_FILE`, and dynamic folder checks (`os.makedirs` + `glob`) when referencing `csv/` dataset locations.
