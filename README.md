# Process Mining Project

This repository contains code and resources for a Process Mining project.

## Project Structure

- `src/`: Source code for process mining algorithms and utilities.
    - `llm/llm_client.py`: Client for interacting with LLM for sub-process naming.
    - `miner/process_miner`: Core process mining algorithms.
    - `ui/visualizalizer`: Visualization created using Streamlit.
- `main.py`: Entry point for running the application.
- `requirements.txt`: List of Python dependencies required for the project.
- `README.md`: Project overview and documentation.

## How to run

1. Clone the repository:
   ```bash
   git clone https://github.com/MarcinZ20/process_lens.git
   ```
2. Navigate to the project directory:
   ```bash
    cd process_lens
    ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
4. Run the application:
   ```bash
   streamlit run src/main.py
   ```
5. Open your web browser and go to `http://localhost:8501` to access the application.
