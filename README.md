# ARIA: Analyst Relations Intelligent Assistant

ARIA is an AI-powered assistant designed to help analyst relations teams efficiently process and respond to RFP (Request for Proposal) documents.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Features

- **Document Upload**: Support for CSV and HTML RFP documents
- **AI Question Extraction**: Automatically extract and categorize questions from documents
- **Intelligent Answer Generation**: Generate contextual responses using AI models
- **Export Options**: Download results in CSV or HTML format
- **Real-time Processing**: Live progress tracking and status updates

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see Configuration section)
4. Start the application: `streamlit run app.py`

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_personal_access_token

# Model Endpoints
QUESTION_EXTRACTION_MODEL=databricks-claude-sonnet-4
ANSWER_GENERATION_MODEL=your_answer_generation_model

# Optional Settings
APP_DEBUG=true
APP_DEVELOPMENT_MODE=true
VOLUME_PATH=/tmp/aria_dev/
```

## Architecture

ARIA follows a modular architecture with clear separation of concerns:

```
src/aria/
├── config/           # Configuration management
├── core/            # Core utilities (logging, exceptions)
├── services/        # Business logic services
├── ui/              # Streamlit UI components
└── utils/           # Utility functions
```

### Key Components

- **Document Processor**: Handles file upload and preprocessing
- **Question Extraction Service**: AI-powered question extraction from documents
- **Answer Generation Service**: Generates responses using AI models
- **State Manager**: Manages application state across steps
- **UI Pages**: Modular Streamlit pages for each processing step

## Usage

### Step 1: Upload Document
- Upload CSV or HTML RFP documents
- Automatic file validation and preview

### Step 2: Extract Questions
- AI-powered question extraction
- Manual review and editing capabilities
- Topic-based categorization

### Step 3: Generate Answers
- Select questions for answer generation
- Customize AI prompts
- Real-time progress tracking

### Step 4: Download Results
- Export in CSV or HTML format
- Customizable filenames
- Complete audit trail

## Development

### Project Structure

```
aria/
├── src/aria/                  # Main application package
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   ├── constants.py      # Application constants
│   │   └── settings.py       # Settings and environment handling
│   ├── core/                 # Core utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── logging_config.py # Logging configuration
│   ├── services/             # Business logic services
│   │   ├── __init__.py
│   │   ├── answer_generation.py    # AI answer generation
│   │   ├── document_processor.py   # Document processing
│   │   └── question_extraction.py  # AI question extraction
│   ├── ui/                   # Streamlit UI components
│   │   ├── __init__.py
│   │   ├── components/       # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── file_preview.py     # File preview widget
│   │   │   ├── navigation.py       # Navigation components
│   │   │   └── stepper.py          # Progress stepper
│   │   ├── pages/            # Individual page implementations
│   │   │   ├── __init__.py
│   │   │   ├── step1_upload.py     # File upload page
│   │   │   ├── step2_extract.py    # Question extraction page
│   │   │   ├── step3_generate.py   # Answer generation page
│   │   │   └── step4_download.py   # Results download page
│   │   └── state_manager.py  # Application state management
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── file_utils.py     # File handling utilities
│       └── validation.py    # Input validation
├── tests/                    # Test suite
├── docs/                     # Documentation
├── app.py                    # Main application entry point
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

The modular version uses a custom Python path configuration to import from the `src/aria/` package. This is handled automatically in `app.py`:

```python
# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
```

### Running the Application

```bash
# Development mode
streamlit run app.py

# Production mode (with specific port)
streamlit run app.py --server.port 8501
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/aria --cov-report=html
```

### Code Quality

The project uses several tools for code quality:

- **Ruff**: Fast Python linter and formatter
- **pytest**: Testing framework
- **Type hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation

## Deployment

### Databricks Apps

For deployment to Databricks Apps, use the provided `app.yaml`:

```yaml
command: ['streamlit', 'run', 'app.py']
```

### Local Development

1. Set up environment variables in `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `streamlit run app.py`

## API Integration

ARIA integrates with Databricks Model Serving endpoints:

- **Question Extraction**: Uses Claude Sonnet for intelligent question parsing
- **Answer Generation**: Configurable model endpoints for response generation
- **Authentication**: Supports both personal access tokens and service principals

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the `src` directory is in your Python path
2. **API Errors**: Verify Databricks credentials and endpoint URLs
3. **File Upload Issues**: Check file permissions and supported formats

### Debug Mode

Enable debug mode for detailed logging:

```bash
export APP_DEBUG=true
streamlit run app.py
```

## Contributing

1. Follow the modular architecture patterns
2. Add comprehensive type hints and docstrings
3. Write tests for new functionality
4. Update documentation as needed

## License

[Add your license information here] 