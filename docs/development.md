# Development Guide

This guide covers the development setup and workflow for the ARIA application.

## Project Structure

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
└── README.md                # Project documentation
```

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aria
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Development Workflow

### Code Organization

The application follows a modular architecture:

- **`src/aria/config/`**: Configuration management and constants
- **`src/aria/core/`**: Core utilities like logging and exceptions
- **`src/aria/services/`**: Business logic services
- **`src/aria/ui/`**: Streamlit UI components and pages
- **`src/aria/utils/`**: Utility functions

### Adding New Features

1. **Services**: Add business logic to appropriate service modules
2. **UI Components**: Create reusable components in `ui/components/`
3. **Pages**: Add new pages in `ui/pages/`
4. **Tests**: Add corresponding tests in `tests/`

### Code Style

- Use type hints for all functions and methods
- Add comprehensive docstrings following PEP 257
- Follow PEP 8 style guidelines
- Use Ruff for linting and formatting

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/aria --cov-report=html

# Run specific test file
python -m pytest tests/test_services/test_question_extraction.py
```

### Debugging

Enable debug mode for detailed logging:

```bash
export APP_DEBUG=true
streamlit run app.py
```

## Architecture Patterns

### Service Layer

Services handle business logic and external API calls:

```python
from aria.services.question_extraction import QuestionExtractionService

service = QuestionExtractionService()
questions = service.extract_questions(document_content)
```

### State Management

Use the StateManager for consistent state handling:

```python
from aria.ui.state_manager import StateManager

state_manager = StateManager()
state_manager.set_questions(questions)
```

### Error Handling

Use custom exceptions for better error handling:

```python
from aria.core.exceptions import ValidationError, APIError

try:
    result = service.process_document(file_path)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
except APIError as e:
    logger.error(f"API call failed: {e}")
```

### Configuration

Access configuration through the settings module:

```python
from aria.config.settings import settings

endpoint = settings.question_extraction_endpoint
debug_mode = settings.debug
```

## Common Development Tasks

### Adding a New Service

1. Create service file in `src/aria/services/`
2. Implement service class with proper typing
3. Add configuration constants if needed
4. Write comprehensive tests
5. Update documentation

### Adding a New UI Page

1. Create page file in `src/aria/ui/pages/`
2. Implement page function with proper state management
3. Add navigation logic
4. Test UI functionality
5. Update step flow if needed

### Modifying Configuration

1. Add new settings to `src/aria/config/settings.py`
2. Add corresponding environment variables
3. Update `.env.example`
4. Document new configuration options

## Performance Considerations

- Use `@st.cache_data` for expensive computations
- Implement proper error handling and retries
- Monitor API call performance
- Use progress indicators for long operations

## Deployment

See [deployment.md](deployment.md) for deployment instructions.

## Contributing

1. Create feature branch from main
2. Implement changes following code style guidelines
3. Add tests for new functionality
4. Update documentation
5. Submit pull request with clear description 