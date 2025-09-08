# ARIA Deployment Guide

This guide covers deployment options for the ARIA application, including local development and Databricks Apps deployment.

## Deployment Options

### 1. Local Development

#### Prerequisites
- Python 3.9+
- Databricks workspace access
- Personal Access Token or Service Principal credentials

#### Setup
1. Clone and install dependencies (see [Development Guide](development.md))
2. Configure environment variables in `.env`
3. Run locally: `streamlit run app.py`

#### Environment Configuration
```bash
# Databricks Unified Authentication Configuration
# The Databricks SDK will automatically choose the best authentication method

# Databricks workspace URL (required)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Personal Access Token (for local development)
# In Databricks Apps, Service Principal credentials are automatically provided
DATABRICKS_TOKEN=your_personal_access_token

# Development mode settings
APP_DEVELOPMENT_MODE=true
APP_DEBUG=true
```

### 2. Databricks Apps Deployment

#### Prerequisites
- Databricks workspace with Apps support
- Service Principal credentials
- Proper permissions for model serving and volumes

#### Deployment Steps

1. **Prepare the application**:
```bash
# Ensure all dependencies are in requirements.txt
pip freeze > requirements.txt

# Validate the app.yaml configuration
cat app.yaml
```

2. **Set up Service Principal**:
   - Create a Service Principal in your Databricks workspace
   - Grant necessary permissions:
     - Model serving endpoints access
     - Volume read/write permissions

3. **Configure app.yaml**:
```yaml
# app.yaml - for Databricks Apps
command: ['streamlit', 'run', 'app.py']
```

4. **Deploy using Databricks CLI**:
```bash
# Install Databricks CLI if not already installed
pip install databricks-cli

# Configure authentication
databricks configure

# Deploy the app
databricks apps create aria
databricks apps deploy aria
```

#### Environment Variables for Databricks Apps

Databricks Apps automatically provides Service Principal credentials via environment variables:
- `DATABRICKS_CLIENT_ID` - Automatically set by Databricks Apps
- `DATABRICKS_CLIENT_SECRET` - Automatically set by Databricks Apps  
- `DATABRICKS_HOST` - Automatically set by Databricks Apps

Additional configuration in `app.yaml`:

```yaml
env:
  # Production Mode
  - name: 'APP_DEVELOPMENT_MODE'
    value: 'false'
  - name: 'APP_DEBUG'
    value: 'false'
  
  # Model Configuration
  - name: 'QUESTION_EXTRACTION_MODEL'
    value: 'your-question-model'
  - name: 'ANSWER_GENERATION_MODEL'
    value: 'your-answer-model'
  
  # Storage Configuration
  - name: 'DATABRICKS_VOLUME_PATH'
    value: '/Volumes/main/default/aria'
  
  # Optional Settings
  - name: 'APP_MAX_FILE_SIZE_MB'
    value: '50'
```

## Configuration Management

### Environment Variables

The application uses environment variables for configuration. Priority order:
1. Environment variables
2. `.env` file (local development only)
3. Default values

### Required Configuration

#### Authentication
The application uses [Databricks Unified Authentication](https://docs.databricks.com/aws/en/dev-tools/auth/unified-auth) which automatically selects the best authentication method:

1. **Personal Access Token** (`DATABRICKS_TOKEN`) - for local development
2. **Service Principal OAuth** (`DATABRICKS_CLIENT_ID`/`DATABRICKS_CLIENT_SECRET`) - for production
3. **Interactive OAuth** (`databricks-cli`) - for development with CLI

In Databricks Apps, Service Principal credentials are automatically provided.

#### Models
- `QUESTION_EXTRACTION_MODEL`: Model for extracting questions from documents
- `ANSWER_GENERATION_MODEL`: Model for generating answers

#### Storage
- `DATABRICKS_VOLUME_PATH`: Volume path for file storage

### Configuration Validation

The application validates configuration on startup:
- Checks required environment variables
- Validates Databricks connectivity
- Verifies model endpoint accessibility

## Monitoring and Logging

### Application Logs
- Logs are sent to stdout by default
- Set `APP_DEBUG=true` for detailed logging
- In Databricks Apps, logs are available in the app console

### Health Checks
The application performs connection tests on startup:
- Databricks workspace connectivity
- Model endpoint availability
- Volume accessibility

### Usage Tracking
If enabled, the application tracks:
- Document processing sessions
- User activity (when email headers are available)
- Processing times and record counts

## Security Considerations

### Authentication
- Use Service Principal credentials for production deployments
- Rotate credentials regularly
- Store secrets securely (not in code)

### Data Handling
- Files are stored temporarily during processing
- No persistent storage of sensitive content
- User data is not logged by default

### Network Security
- All Databricks API calls use HTTPS
- Token/credentials are passed in headers (not URLs)
- File uploads are validated for type and size

## Performance Optimization

### Resource Usage
- Memory usage scales with document size
- CPU usage peaks during AI model calls
- Network bandwidth for file uploads/downloads

### Scaling Considerations
- Databricks Apps auto-scale based on usage
- Model serving endpoints handle concurrent requests
- Consider request timeouts for large documents

### Caching
- Streamlit's native caching for UI components
- No application-level caching of API responses
- Session state manages user workflow

## Troubleshooting

### Common Deployment Issues

1. **Authentication Failures**
   - Verify credentials and permissions
   - Check workspace URL format
   - Ensure service principal has necessary grants

2. **Model Invocation Errors**
   - Verify model names and endpoints
   - Check model serving status
   - Validate payload format

3. **Volume Access Issues**
   - Verify volume paths exist
   - Check read/write permissions
   - Ensure proper volume mounting

4. **Performance Issues**
   - Monitor model response times
   - Check file upload sizes
   - Review batch processing limits

### Debugging Steps

1. **Enable debug mode**: `APP_DEBUG=true`
2. **Check application logs** in Databricks Apps console
3. **Test components individually**:
   - Configuration validation
   - Databricks connectivity
   - Model endpoints
   - Volume access

### Support Resources

- **Databricks Apps Documentation**: Official deployment guides
- **Model Serving Documentation**: Endpoint configuration and troubleshooting
- **Volume Documentation**: File storage and permissions

## Rollback Procedures

### Databricks Apps
```bash
# List app versions
databricks apps list-versions aria

# Rollback to previous version
databricks apps deploy aria --version <previous-version>
```

### Configuration Changes
- Environment variables can be updated without redeployment
- Model endpoint changes require application restart
- Volume path changes may require data migration

## Maintenance

### Regular Tasks
- Monitor application logs for errors
- Update dependencies periodically
- Rotate authentication credentials
- Clean up temporary files in volumes

### Updates
- Test changes in development environment first
- Use staged deployments for critical updates
- Monitor application health after deployment
- Have rollback plan ready

### Backup Considerations
- Configuration is stored in environment variables
- No application data requires backup
- User-generated content is temporary
- Consider backing up usage tracking data if enabled 