# Quill: Intelligent Financial Assistant (built on ARIA)

 Quill is a GenAI-powered financial assistant designed for portfolio managers, investment strategists, and risk officers in capital markets and investment management. It helps users navigate and act on regulatory, compliance, and market risks by unifying structured and unstructured data, delivering actionable insights, and automating repetitive compliance and research workflows. Quill can ingest documents, extract key questions, and generate high‑quality, contextual answers. Quill is built on the ARIA framework built by Rafi Kurlansik. 


## How Quill relates to ARIA

- **Quill**: Financial domain experience, workflows, and UX.
- **ARIA (platform)**: Shared building blocks including document processing, question extraction, answer generation, state management, and Databricks integration.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Features

- **Financial document ingestion**: Upload CSV and HTML sources (e.g., compliance requirements, disclosures, Q&A banks)
- **AI question extraction**: Identify and categorize questions from uploaded content
- **Contextual answer generation**: Produce tailored, referenceable responses using LLMs
- **Real-time progress**: Live status across steps with a guided stepper UI
- **Export results**: Download answers and datasets as CSV or HTML
- **Ad‑hoc questions**: Ask standalone questions with optional context

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see Configuration)
4. Start the app: `streamlit run app.py`

## Configuration

Create a `.env` file in the project root (see `env.dev` for examples):

```bash
# Databricks configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_personal_access_token

# Model endpoints
QUESTION_EXTRACTION_MODEL=databricks-claude-sonnet-4
ANSWER_GENERATION_MODEL=your_answer_generation_model

# Optional settings
APP_DEBUG=true
APP_DEVELOPMENT_MODE=true
VOLUME_PATH=/tmp/aria_dev/
```

## Architecture

Quill uses ARIA’s modular architecture with a clear separation of concerns:

```
src/aria/
├── config/           # Configuration management
├── core/             # Core utilities (logging, exceptions, types)
├── services/         # Domain-agnostic AI services
├── ui/               # Streamlit UI (components, pages, state)
└── utils/            # Utility functions (reserved/future)
```

### Key components (from ARIA)

- **Document Processor** (`services/document_processor.py`): Uploads and preprocesses files
- **Question Extraction** (`services/question_extraction.py`): AI-powered extraction and grouping
- **Answer Generation** (`services/answer_generation.py`): LLM-backed response generation
- **State Manager** (`ui/state_manager.py`): Multi-step state handling
- **UI Pages** (`ui/pages/*`): Stepwise flows and ad‑hoc Q&A

## Usage

### Step 1: Upload or use sample CSV
- Upload CSV or use Sample CSV with regulatory questions

### Step 2: Extract questions
- AI extraction and categorization
- Manual review and edits

### Step 3: Generate answers
- Select questions and customize prompts
- Real-time generation with progress tracking

### Step 4: Download
- Export results in CSV or HTML

### Ad‑hoc questions
- Use the dedicated page for ad-hoc single‑question workflows

## Project structure

```
.
├── app.py
├── src/aria/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── logging_config.py
│   │   └── types.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── answer_generation.py
│   │   ├── document_processor.py
│   │   └── question_extraction.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── file_preview.py
│   │   │   └── stepper.py
│   │   ├── pages/
│   │   │   ├── __init__.py
│   │   │   ├── adhoc_questions.py
│   │   │   ├── step1_upload.py
│   │   │   ├── step2_extract.py
│   │   │   ├── step3_generate.py
│   │   │   └── step4_download.py
│   │   ├── state_manager.py
│   │   └── styles/
│   │       ├── __init__.py
│   │       └── css.py
│   └── utils/
│       └── __init__.py
├── requirements.txt
├── pyproject.toml
├── docs/
├── assets/
└── tests/
```

The `app.py` entry point sets up the Streamlit application and imports modules from `src/aria`.

## Running the application

```bash
# Development
streamlit run app.py

# Specify a port (e.g., for local testing)
streamlit run app.py --server.port 8501
```

## Testing

```bash
# Run all tests
python -m pytest tests/

# Coverage
python -m pytest tests/ --cov=src/aria --cov-report=html
```

## Code quality

- **Ruff**: Fast Python linter/formatter
- **pytest**: Testing framework
- **Type hints**: Strong typing across modules

## Deployment

### Databricks Apps

Use the provided `app.yaml`:

```yaml
command: ['streamlit', 'run', 'app.py']
```

### Local development

1. Create `.env`
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

## API integration

Quill (via ARIA) integrates with Databricks Model Serving endpoints:

- **Question extraction**: e.g., Claude Sonnet family
- **Answer generation**: configurable model endpoint
- **Authentication**: personal access tokens or service principals

## Troubleshooting

### Common issues

1. **Imports**: Ensure `src` is discoverable (handled by `app.py`)
2. **Model serving**: Verify Databricks host/token and endpoint names
3. **File upload**: Confirm filetype and permissions

### Debug mode

```bash
export APP_DEBUG=true
streamlit run app.py
```

## Contributing

1. Align changes with ARIA’s modular architecture
2. Add type hints and concise docstrings
3. Include tests for new functionality
4. Update documentation when behavior changes

## License

[Add your license information here]