"""Question extraction service for ARIA application.

This module handles extracting questions from documents using AI models
for HTML files and direct extraction for CSV files.
"""

import re
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from aria.core.logging_config import get_logger
from aria.config.config import (
    config, DEFAULT_TIMEOUT_SECONDS,
    MAX_RETRIES, RETRY_WAIT_SECONDS, QUESTION_EXTRACTION_SYSTEM_PROMPT
)

logger = get_logger(__name__)


class TemporaryServiceUnavailableError(Exception):
    """Exception for temporary service unavailability (503 errors)."""
    pass


class QuestionExtractionService:
    """Service for extracting questions from documents."""
    
    def __init__(self) -> None:
        """Initialize the question extraction service."""
        self.settings = config
        self.timeout = DEFAULT_TIMEOUT_SECONDS
    
    def extract_questions(
        self, 
        content: str, 
        extraction_method: str,
        custom_prompt: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """Extract questions from content.
        
        Args:
            content: The content to extract questions from
            extraction_method: Method to use ('csv_direct' or 'ai_extraction')
            custom_prompt: Custom prompt for AI extraction
            metadata: Additional metadata about the content
            model_name: Optional model name to use for AI extraction
            
        Returns:
            Tuple of (success, questions_list, extraction_info)
        """
        extraction_info = {
            "method": extraction_method,
            "questions_found": 0,
            "processing_time": 0.0,
            "errors": [],
            "model_used": model_name or self.settings.models.question_extraction_model
        }
        
        try:
            import time
            start_time = time.time()
            
            if extraction_method == "csv_direct":
                success, questions = self._extract_from_csv_content(content, metadata)
            elif extraction_method == "ai_extraction":
                success, questions = self._extract_with_ai(content, custom_prompt, model_name)
            else:
                extraction_info["errors"].append(f"Unknown extraction method: {extraction_method}")
                return False, [], extraction_info
            
            extraction_info["processing_time"] = time.time() - start_time
            extraction_info["questions_found"] = len(questions) if success else 0
            
            if success:
                logger.info(f"Successfully extracted {len(questions)} questions using {extraction_method}")
            else:
                logger.warning(f"Question extraction failed using {extraction_method}")
            
            return success, questions, extraction_info
            
        except Exception as e:
            logger.error(f"Error in question extraction: {str(e)}")
            extraction_info["errors"].append(f"Extraction error: {str(e)}")
            return False, [], extraction_info
    
    def _extract_from_csv_content(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Extract questions from CSV content.
        
        Args:
            content: CSV content as text
            metadata: Metadata about the CSV file
            
        Returns:
            Tuple of (success, questions_list)
        """
        try:
            questions = []
            
            # Parse the content which should be in format "Q1: question text"
            lines = content.strip().split('\n')
            
            for i, line in enumerate(lines):
                if line.strip():
                    # Extract question text (remove "Q1:" prefix if present)
                    question_text = re.sub(r'^Q\d+:\s*', '', line.strip())
                    
                    question = {
                        "id": f"Q{i+1}",
                        "question": str(i+1),
                        "topic": "General",  # CSV files don't have topic grouping by default
                        "sub_question": f"{i+1}.1",
                        "text": question_text
                    }
                    questions.append(question)
            
            logger.info(f"Extracted {len(questions)} questions from CSV content")
            return True, questions
            
        except Exception as e:
            logger.error(f"Error extracting from CSV content: {str(e)}")
            return False, []
    
    def _extract_with_ai(
        self, 
        html_content: str, 
        custom_prompt: str = "",
        model_name: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Extract questions from HTML content using AI.
        
        Args:
            html_content: HTML content to process
            custom_prompt: Custom prompt for extraction
            model_name: Optional model name to use for AI extraction
            
        Returns:
            Tuple of (success, questions_list)
        """
        try:
            # Check if we have authentication configured
            auth_headers = self.settings.get_auth_headers()
            if not auth_headers:
                logger.error("No authentication configured - cannot perform AI extraction")
                return False, []
            
            # Prepare the content for AI processing
            processed_content = self._preprocess_html(html_content)
            
            # Create the prompt
            system_prompt = self._build_extraction_prompt()
            user_prompt = self._build_user_prompt(processed_content, custom_prompt)
            
            # Make API call with improved retry logic
            success, response_text = self._call_extraction_api_with_retry(system_prompt, user_prompt, auth_headers, model_name)
            
            if not success:
                logger.error("AI extraction failed after retries")
                return False, []
            
            # Parse the AI response
            questions = self._parse_ai_response(response_text)
            
            if not questions:
                logger.error("AI extraction succeeded but no questions were parsed from response")
                return False, []
            
            return True, questions
            
        except Exception as e:
            logger.error(f"Error in AI extraction: {str(e)}")
            return False, []
    
    def _preprocess_html(self, html_content: str) -> str:
        """Preprocess HTML content for AI extraction.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Processed content suitable for AI
        """
        try:
            # Try to use BeautifulSoup if available for better preprocessing
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text_content = soup.get_text(separator=' ', strip=True)
                
                # Clean up whitespace
                text_content = re.sub(r'\s+', ' ', text_content)
                
                logger.info(f"Preprocessed HTML: {len(html_content)} -> {len(text_content)} characters")
                return text_content
                
            except ImportError:
                logger.warning("BeautifulSoup not available - using basic preprocessing")
                # Basic preprocessing without BeautifulSoup
                # Remove script and style tags
                text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', ' ', text)
                
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                
                return text
                
        except Exception as e:
            logger.error(f"Error preprocessing HTML: {str(e)}")
            return html_content
    
    def _build_extraction_prompt(self) -> str:
        """Build the system prompt for question extraction.
        
        Returns:
            System prompt for AI
        """
        return QUESTION_EXTRACTION_SYSTEM_PROMPT
    
    def _build_user_prompt(self, content: str, custom_prompt: str = "") -> str:
        """Build the user prompt for question extraction.
        
        Args:
            content: Content to extract questions from
            custom_prompt: Custom instructions
            
        Returns:
            User prompt for AI
        """
        base_prompt = f"Please extract and structure questions from the following content:\n\n{content}"
        
        if custom_prompt and custom_prompt.strip():
            base_prompt += f"\n\nAdditional instructions: {custom_prompt}"
        
        return base_prompt
    
    def _call_extraction_api_with_retry(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        auth_headers: Dict[str, str],
        model_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Call the AI API with improved retry logic for 503 errors.
        
        Args:
            system_prompt: System prompt for AI
            user_prompt: User prompt with content
            auth_headers: Authentication headers
            model_name: Optional model name to use for AI extraction
            
        Returns:
            Tuple of (success, response_text)
        """
        try:
            # First attempt with standard retry logic
            return self._call_extraction_api(system_prompt, user_prompt, auth_headers, model_name)
        except TemporaryServiceUnavailableError:
            # For 503 errors, try with more aggressive retry
            logger.warning("Service temporarily unavailable, trying with extended retry logic")
            return self._call_extraction_api_extended_retry(system_prompt, user_prompt, auth_headers, model_name)
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            return False, ""
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TemporaryServiceUnavailableError)
    )
    def _call_extraction_api(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        auth_headers: Dict[str, str],
        model_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Call the AI API for question extraction.
        
        Args:
            system_prompt: System prompt for AI
            user_prompt: User prompt with content
            auth_headers: Authentication headers
            model_name: Optional model name to use for AI extraction
            
        Returns:
            Tuple of (success, response_text)
        """
        try:
            endpoint_url = self.settings.question_extraction_endpoint
            model_name = model_name or self.settings.models.question_extraction_model
            
            # Check if model_name is a display name rather than an endpoint name
            # If it's a key in the available models dict, get the corresponding endpoint name
            available_models = self.settings.AVAILABLE_CLAUDE_MODELS
            if model_name in available_models:
                model_endpoint_name = available_models[model_name]
                logger.info(f"Converting model display name '{model_name}' to endpoint name '{model_endpoint_name}'")
                model_name = model_endpoint_name
            
            # Use custom model name for endpoint URL if provided
            if model_name != self.settings.models.question_extraction_model:
                endpoint_url = self.settings.databricks.get_model_endpoint_url(model_name)
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 15000,
                "temperature": 0.1
            }
            
            logger.info(f"Calling {model_name} for question extraction: {endpoint_url}")
            
            response = requests.post(
                endpoint_url,
                headers=auth_headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract response text
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    response_text = response_data["choices"][0]["message"]["content"]
                    logger.info(f"{model_name} extraction API call successful")
                    return True, response_text
                else:
                    logger.error("Unexpected API response format")
                    return False, ""
            elif response.status_code == 403:
                response_text = response.text
                
                # Check if this is a JWT expiration error
                if ("ExpiredJwtException" in response_text or 
                    "JWT expired" in response_text or
                    "token expired" in response_text.lower()):
                    
                    logger.warning("JWT token expired, attempting to refresh authentication")
                    
                    # Get fresh authentication headers
                    fresh_auth_headers = self.settings.get_auth_headers()
                    
                    if fresh_auth_headers and fresh_auth_headers != auth_headers:
                        logger.info("Retrieved fresh authentication token, retrying API call")
                        
                        # Retry with fresh token
                        retry_response = requests.post(
                            endpoint_url,
                            headers=fresh_auth_headers,
                            json=payload,
                            timeout=self.timeout
                        )
                        
                        if retry_response.status_code == 200:
                            response_data = retry_response.json()
                            
                            # Extract response text
                            if "choices" in response_data and len(response_data["choices"]) > 0:
                                response_text = response_data["choices"][0]["message"]["content"]
                                logger.info(f"{model_name} extraction API call successful after token refresh")
                                return True, response_text
                            else:
                                logger.error("Unexpected API response format after token refresh")
                                return False, ""
                        elif retry_response.status_code == 503:
                            # Raise specific exception for 503 errors to trigger retry
                            error_msg = f"Service temporarily unavailable after token refresh: {retry_response.text}"
                            logger.warning(error_msg)
                            raise TemporaryServiceUnavailableError(error_msg)
                        else:
                            logger.error(f"API call failed even after token refresh with status {retry_response.status_code}: {retry_response.text}")
                            return False, ""
                    else:
                        logger.error("Could not refresh authentication token or got same token")
                        return False, ""
                else:
                    # Non-token related 403 error
                    logger.error(f"Authentication error (403): {response_text}")
                    return False, ""
            elif response.status_code == 503:
                # Raise specific exception for 503 errors to trigger retry
                error_msg = f"Service temporarily unavailable: {response.text}"
                logger.warning(error_msg)
                raise TemporaryServiceUnavailableError(error_msg)
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False, ""
                
        except TemporaryServiceUnavailableError:
            # Re-raise to trigger retry
            raise
        except Exception as e:
            logger.error(f"Error calling {model_name} extraction API: {str(e)}")
            return False, ""
    
    @retry(
        stop=stop_after_attempt(6),  # More attempts for 503 errors
        wait=wait_exponential(multiplier=2, min=5, max=60)  # Longer waits
    )
    def _call_extraction_api_extended_retry(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        auth_headers: Dict[str, str],
        model_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Call the AI API with extended retry for persistent 503 errors.
        
        Args:
            system_prompt: System prompt for AI
            user_prompt: User prompt with content
            auth_headers: Authentication headers
            model_name: Optional model name to use for AI extraction
            
        Returns:
            Tuple of (success, response_text)
        """
        try:
            endpoint_url = self.settings.question_extraction_endpoint
            model_name = model_name or self.settings.models.question_extraction_model
            
            # Check if model_name is a display name rather than an endpoint name
            # If it's a key in the available models dict, get the corresponding endpoint name
            available_models = self.settings.AVAILABLE_CLAUDE_MODELS
            if model_name in available_models:
                model_endpoint_name = available_models[model_name]
                logger.info(f"Converting model display name '{model_name}' to endpoint name '{model_endpoint_name}' (extended retry)")
                model_name = model_endpoint_name
            
            # Use custom model name for endpoint URL if provided
            if model_name != self.settings.models.question_extraction_model:
                endpoint_url = self.settings.databricks.get_model_endpoint_url(model_name)
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 15000,
                "temperature": 0.1
            }
            
            logger.info(f"Extended retry - calling {model_name} for question extraction: {endpoint_url}")
            
            response = requests.post(
                endpoint_url,
                headers=auth_headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract response text
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    response_text = response_data["choices"][0]["message"]["content"]
                    logger.info(f"{model_name} extraction API call successful (extended retry)")
                    return True, response_text
                else:
                    logger.error("Unexpected API response format")
                    return False, ""
            elif response.status_code == 503:
                # Continue retrying for 503 errors
                error_msg = f"Service still unavailable (extended retry): {response.text}"
                logger.warning(error_msg)
                raise TemporaryServiceUnavailableError(error_msg)
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False, ""
                
        except TemporaryServiceUnavailableError:
            # Re-raise to trigger retry
            raise
        except Exception as e:
            logger.error(f"Error calling {model_name} extraction API (extended retry): {str(e)}")
            return False, ""
    
    def _parse_ai_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured questions.
        
        Args:
            response_text: Raw response from AI
            
        Returns:
            List of structured questions
        """
        try:
            # Clean up the response text to extract JSON
            json_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if json_text.startswith('```'):
                lines = json_text.split('\n')
                # Remove first and last lines if they're markdown
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                json_text = '\n'.join(lines)
            
            # Find JSON array or object pattern in the text
            json_match = re.search(r'(\[.*\]|\{.*\})', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            
            # Parse JSON
            try:
                questions_data = json.loads(json_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON, attempting to clean and retry")
                # Try to clean up common JSON issues
                cleaned_json = re.sub(r'\\([^"\\/bfnrtu])', r'\1', json_text)
                cleaned_json = re.sub(r'\}\s*\{', '},{', cleaned_json)
                cleaned_json = re.sub(r',\s*\]', ']', cleaned_json)
                questions_data = json.loads(cleaned_json)
            
            # Handle different response formats
            questions = []
            
            if isinstance(questions_data, list):
                # Handle array of questions or complex objects
                for i, item in enumerate(questions_data):
                    if isinstance(item, str):
                        # Simple string array
                        questions.append({
                            "question": str(i + 1),
                            "topic": "General",
                            "sub_question": f"{i + 1}.1",
                            "text": item
                        })
                    elif isinstance(item, dict):
                        # Check if it's the complex nested structure with sub_topics
                        if 'sub_topics' in item:
                            # Use pandas to flatten the nested structure
                            import pandas as pd
                            df = pd.json_normalize(
                                [item],
                                record_path=['sub_topics', 'sub_questions'],
                                meta=['question', ['sub_topics', 'topic']],
                                errors='ignore'
                            )
                            if 'sub_topics.topic' in df.columns:
                                df = df.rename(columns={'sub_topics.topic': 'topic'})
                            questions.extend(df.to_dict('records'))
                        # Check if it's the section/questions structure
                        elif 'section' in item and 'questions' in item:
                            section_name = item.get('section', 'General')
                            section_questions = item.get('questions', [])
                            for j, q in enumerate(section_questions):
                                if isinstance(q, dict):
                                    questions.append({
                                        "question": str(i + 1),
                                        "topic": section_name,
                                        "sub_question": q.get('number', f"{i + 1}.{j + 1}"),
                                        "text": q.get('text', q.get('question', ''))
                                    })
                                elif isinstance(q, str):
                                    questions.append({
                                        "question": str(i + 1),
                                        "topic": section_name,
                                        "sub_question": f"{i + 1}.{j + 1}",
                                        "text": q
                                    })
                        else:
                            # Simple object structure
                            questions.append({
                                "question": item.get("question", str(i + 1)),
                                "topic": item.get("topic", "General"),
                                "sub_question": item.get("sub_question", f"{i + 1}.1"),
                                "text": item.get("text", item.get("question", ""))
                            })
                            
            elif isinstance(questions_data, dict):
                # Handle object with questions array
                if 'questions' in questions_data:
                    question_list = questions_data['questions']
                    for i, q in enumerate(question_list):
                        if isinstance(q, str):
                            questions.append({
                                "question": "1",
                                "topic": "General",
                                "sub_question": f"1.{i + 1}",
                                "text": q
                            })
                        elif isinstance(q, dict):
                            questions.append({
                                "question": q.get("question", "1"),
                                "topic": q.get("topic", "General"),
                                "sub_question": q.get("sub_question", f"1.{i + 1}"),
                                "text": q.get("text", q.get("question", ""))
                            })
                else:
                    # Single question object
                    questions.append({
                        "question": questions_data.get("question", "1"),
                        "topic": questions_data.get("topic", "General"),
                        "sub_question": questions_data.get("sub_question", "1.1"),
                        "text": questions_data.get("text", questions_data.get("question", ""))
                    })
            
            logger.info(f"Successfully parsed {len(questions)} questions from AI response")
            return questions
                
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return []
    
 