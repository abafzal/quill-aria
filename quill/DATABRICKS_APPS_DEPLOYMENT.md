# Databricks Apps Deployment Guide for ARIA

This guide covers the specific steps needed to deploy ARIA to Databricks Apps.

## Prerequisites

1. **Databricks workspace** with Apps support enabled
2. **Service Principal** created in your workspace
3. **Model serving endpoints** accessible to the Service Principal
4. **Volume access** for file storage

## Step 1: Service Principal Setup

### Create Service Principal
```bash
# Using Databricks CLI
databricks service-principals create --display-name "aria-app"
```

### Grant Permissions
The Service Principal needs:
- **Model Serving**: Access to your model endpoints
- **Volume Access**: Read/write to the storage volume
- **Workspace Access**: Basic workspace permissions

## Step 2: Environment Configuration

### Required Environment Variables in app.yaml

```yaml
env:
  # Production Mode (CRITICAL)
  APP_DEVELOPMENT_MODE: "false"
  APP_DEBUG: "false"
  
  # Model Configuration
  QUESTION_EXTRACTION_MODEL: "databricks-claude-sonnet-4"
  ANSWER_GENERATION_MODEL: "agents_users-rafi_kurlansik-auto_rfi"
  
  # Storage
  DATABRICKS_VOLUME_PATH: "/Volumes/main/default/aria"
```

### Automatic Environment Variables

Databricks Apps **automatically provides** these variables:
- `DATABRICKS_CLIENT_ID` - Service Principal client ID
- `DATABRICKS_CLIENT_SECRET` - Service Principal client secret  
- `DATABRICKS_HOST` - Current workspace URL

**You do NOT need to set these manually!**

## Step 3: Deploy the Application

```bash
# Deploy using Databricks CLI
databricks apps create aria
databricks apps deploy aria
```

## Troubleshooting

### Issue: "No authentication configured - using mock extraction"

**Symptoms:**
- Application falls back to mock data
- Logs show: `[Config Error] Cannot get simple auth headers for Service Principal`
- Development mode warnings in production

**Solutions:**

1. **Check Production Mode**:
   ```yaml
   env:
     APP_DEVELOPMENT_MODE: "false"  # Must be "false" not "true"
   ```

2. **Verify Service Principal**:
   ```bash
   # Check if Service Principal exists
   databricks service-principals list
   
   # Check permissions
   databricks permissions get /serving-endpoints/your-model-name
   ```

3. **Enable Debug Mode** (temporarily):
   ```yaml
   env:
     APP_DEBUG: "true"  # Add this to see detailed auth logs
   ```

### Issue: Model endpoint access denied

**Symptoms:**
- Authentication works but API calls fail
- 403 Forbidden errors in logs

**Solutions:**

1. **Grant Model Access**:
   ```bash
   databricks permissions update /serving-endpoints/your-model-name \
     --json '{"access_control_list": [{"service_principal_name": "your-sp-id", "permission_level": "CAN_QUERY"}]}'
   ```

2. **Check Model Status**:
   ```bash
   databricks serving-endpoints get your-model-name
   ```

### Issue: Volume access problems

**Symptoms:**
- File upload/download failures
- Volume path errors

**Solutions:**

1. **Create Volume** (if needed):
   ```sql
   CREATE VOLUME main.default.aria;
   ```

2. **Grant Volume Access**:
   ```sql
   GRANT READ, WRITE ON VOLUME main.default.aria TO `your-service-principal-id`;
   ```

## Verification Steps

### 1. Check Application Logs
```bash
databricks apps logs aria
```

Look for:
- `[Config] Auth Mode: Service Principal` ✅
- `[Config] Development Mode: False` ✅
- `Successfully obtained token from Service Principal` ✅

### 2. Test Authentication
The application includes a built-in auth test. Look for these log messages:
- `Service Principal authenticated as: your-sp-name@domain.com`
- `Successfully obtained token from Service Principal`

### 3. Test Model Access
Upload a test document and verify:
- Question extraction works (not mock data)
- Answer generation completes successfully
- No "mock" messages in logs

## Common Environment Variable Names

If the automatic injection doesn't work, Databricks Apps might use these alternative names:

- `CLIENT_ID` or `OAUTH_CLIENT_ID`
- `CLIENT_SECRET` or `OAUTH_CLIENT_SECRET`
- `SERVICE_PRINCIPAL_CLIENT_ID`
- `SERVICE_PRINCIPAL_CLIENT_SECRET`

The application automatically checks for these alternatives.

## Production Checklist

Before deploying to production:

- [ ] `APP_DEVELOPMENT_MODE: "false"`
- [ ] `APP_DEBUG: "false"` (unless debugging)
- [ ] Service Principal created and configured
- [ ] Model endpoints accessible to Service Principal
- [ ] Volume permissions granted
- [ ] Test with real documents (not mock data)

## Support

If you continue to have authentication issues:

1. **Enable debug mode** temporarily: `APP_DEBUG: "true"`
2. **Check the logs** for detailed authentication flow
3. **Verify Service Principal** has all required permissions
4. **Test model endpoints** directly using the Databricks CLI

The application provides detailed debug output when `APP_DEBUG=true` to help diagnose authentication and permission issues. 