"""Answer generation service for ARIA application.

This module handles generating responses to questions using AI models,
with support for both individual and batch processing.
"""

import re
import time
from typing import Dict, List, Optional, Any, Tuple, Callable
import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed

from aria.core.logging_config import get_logger
from aria.config.config import (
    config, DEFAULT_TIMEOUT_SECONDS,
    MAX_RETRIES, RETRY_WAIT_SECONDS, ANSWER_GENERATION_SYSTEM_PROMPT
)

logger = get_logger(__name__)


class AnswerGenerationService:
    """Service for generating answers to questions using AI."""
    
    def __init__(self) -> None:
        """Initialize the answer generation service."""
        self.settings = config
        self.timeout = DEFAULT_TIMEOUT_SECONDS
    
    def generate_answers(
        self,
        questions: List[Dict[str, Any]],
        custom_prompt: str = "",
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """Generate answers for a list of questions.
        
        Args:
            questions: List of question dictionaries
            custom_prompt: Custom prompt for answer generation
            progress_callback: Optional callback for progress updates (current, total, status)
            
        Returns:
            Tuple of (success, answers_list, generation_info)
        """
        generation_info = {
            "questions_processed": 0,
            "answers_generated": 0,
            "processing_time": 0.0,
            "method": "unknown",
            "errors": []
        }
        
        try:
            start_time = time.time()
            
            # Check if we have authentication configured
            auth_headers = self.settings.get_auth_headers()
            if not auth_headers:
                logger.error("No authentication configured - cannot generate answers")
                generation_info["errors"].append("Authentication not configured")
                return False, [], generation_info
            
            # Determine the best processing method based on question structure
            if self._has_hierarchical_structure(questions):
                logger.info("Using topic-based batch processing")
                success, answers = self._generate_by_topics(questions, custom_prompt, auth_headers, progress_callback)
                generation_info["method"] = "topic_batch"
            else:
                logger.info("Using individual question processing")
                success, answers = self._generate_individual(questions, custom_prompt, auth_headers, progress_callback)
                generation_info["method"] = "individual"
            
            generation_info["processing_time"] = time.time() - start_time
            generation_info["questions_processed"] = len(questions)
            generation_info["answers_generated"] = len(answers) if success else 0
            
            if success:
                logger.info(f"Successfully generated {len(answers)} answers in {generation_info['processing_time']:.2f} seconds")
            else:
                logger.warning("Answer generation failed")
            
            return success, answers, generation_info
            
        except Exception as e:
            logger.error(f"Error in answer generation: {str(e)}")
            generation_info["errors"].append(f"Generation error: {str(e)}")
            return False, [], generation_info
    
    def _has_hierarchical_structure(self, questions: List[Dict[str, Any]]) -> bool:
        """Check if questions have hierarchical structure (topics, sub-questions).
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            True if hierarchical structure is detected
        """
        if not questions:
            return False
        
        # Check if questions have the expected hierarchical fields
        sample_question = questions[0]
        required_fields = ['question', 'topic', 'sub_question', 'text']
        
        return all(field in sample_question for field in required_fields)
    
    def _generate_by_topics(
        self,
        questions: List[Dict[str, Any]],
        custom_prompt: str,
        auth_headers: Dict[str, str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Generate answers by grouping questions by topic.
        
        Args:
            questions: List of question dictionaries
            custom_prompt: Custom prompt for generation
            auth_headers: Authentication headers (will be refreshed as needed)
            progress_callback: Progress callback function
            
        Returns:
            Tuple of (success, answers_list)
        """
        try:
            # Group questions by topic
            df = pd.DataFrame(questions)
            grouped_df = self._group_questions_by_topic(df)
            
            total_topics = len(grouped_df)
            all_answers = []
            
            for i, (idx, row) in enumerate(grouped_df.iterrows()):
                if progress_callback:
                    model_name = self.settings.models.answer_generation_model
                    progress_callback(i + 1, total_topics, f"Calling {model_name} for topic: {row['topic']}")
                
                # Get fresh auth headers for each topic to handle potential token expiration
                # This is especially important for long-running batch processes
                current_auth_headers = self.settings.get_auth_headers()
                if not current_auth_headers:
                    logger.error("Authentication headers are no longer available")
                    break
                
                # Generate answers for this topic
                success, topic_answers = self._generate_topic_answers(
                    row, custom_prompt, current_auth_headers
                )
                
                if success:
                    all_answers.extend(topic_answers)
                else:
                    logger.warning(f"Failed to generate answers for topic: {row['topic']}")
            
            return True, all_answers
            
        except Exception as e:
            logger.error(f"Error in topic-based generation: {str(e)}")
            return False, []
    
    def _generate_individual(
        self,
        questions: List[Dict[str, Any]],
        custom_prompt: str,
        auth_headers: Dict[str, str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Generate answers for individual questions.
        
        Args:
            questions: List of question dictionaries
            custom_prompt: Custom prompt for generation
            auth_headers: Authentication headers (will be refreshed as needed)
            progress_callback: Progress callback function
            
        Returns:
            Tuple of (success, answers_list)
        """
        try:
            total_questions = len(questions)
            answers = []
            
            for idx, question in enumerate(questions):
                if progress_callback:
                    question_preview = question.get('text', question.get('Question', ''))[:50]
                    model_name = self.settings.models.answer_generation_model
                    progress_callback(idx + 1, total_questions, f"Calling {model_name}: {question_preview}...")
                
                # Get fresh auth headers for each question to handle potential token expiration
                current_auth_headers = self.settings.get_auth_headers()
                if not current_auth_headers:
                    logger.error("Authentication headers are no longer available")
                    break
                
                # Generate answer for this question
                success, answer = self._generate_single_answer(
                    question, custom_prompt, current_auth_headers
                )
                
                if success:
                    answers.append(answer)
                else:
                    # Add a placeholder answer for failed questions
                    answers.append({
                        "question_id": question.get('id', f"Q{idx+1}"),
                        "question_text": question.get('text', question.get('Question', '')),
                        "answer": "Error: Failed to generate answer",
                        "topic": question.get('topic', 'Unknown')
                    })
            
            return True, answers
            
        except Exception as e:
            logger.error(f"Error in individual generation: {str(e)}")
            return False, []
    
    def _group_questions_by_topic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group questions by topic for batch processing.
        
        Args:
            df: DataFrame with questions
            
        Returns:
            DataFrame grouped by topic
        """
        try:
            # Group by topic and aggregate
            grouped_df = df.groupby(['topic']).agg({
                'question': 'first',  # Keep the main question ID
                'sub_question': lambda x: list(x),  # List of all sub-questions
                'text': lambda x: '\n\n'.join(f"{sq}: {txt}" for sq, txt in zip(df.loc[x.index, 'sub_question'], x))
            }).reset_index()
            
            # Add question count for each topic
            grouped_df['question_count'] = grouped_df['sub_question'].apply(len)
            
            # Create original_questions data for each topic by looking up the original rows
            original_questions_list = []
            for _, row in grouped_df.iterrows():
                topic = row['topic']
                topic_mask = df['topic'] == topic
                topic_questions = df.loc[topic_mask].to_dict('records')
                original_questions_list.append(topic_questions)
            
            grouped_df['original_questions'] = original_questions_list
            
            logger.info(f"Grouped {len(df)} questions into {len(grouped_df)} topics")
            return grouped_df
            
        except Exception as e:
            logger.error(f"Error grouping questions by topic: {str(e)}")
            return pd.DataFrame()
    
    def _generate_topic_answers(
        self,
        topic_row: pd.Series,
        custom_prompt: str,
        auth_headers: Dict[str, str]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Generate answers for all questions in a topic.
        
        Args:
            topic_row: Row from grouped DataFrame containing topic info
            custom_prompt: Custom prompt for generation
            auth_headers: Authentication headers
            
        Returns:
            Tuple of (success, answers_list)
        """
        try:
            topic = str(topic_row['topic'])
            question_text = str(topic_row['text'])
            sub_question_ids = list(topic_row['sub_question'])
            
            # Get the original questions data for this topic
            original_questions = topic_row.get('original_questions', [])
            
            # Build prompt for this topic
            system_prompt = self._build_generation_prompt()
            user_prompt = self._build_topic_user_prompt(topic, question_text, custom_prompt)
            
            # Make API call
            success, response_text = self._call_generation_api(system_prompt, user_prompt, auth_headers)
            
            if not success:
                return False, []
            
            # Parse the response to extract individual answers
            answers = self._parse_topic_response(response_text, topic, sub_question_ids, original_questions)
            
            return True, answers
            
        except Exception as e:
            logger.error(f"Error generating topic answers: {str(e)}")
            return False, []
    
    def _generate_single_answer(
        self,
        question: Dict[str, Any],
        custom_prompt: str,
        auth_headers: Dict[str, str]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Generate answer for a single question.
        
        Args:
            question: Question dictionary
            custom_prompt: Custom prompt for generation
            auth_headers: Authentication headers
            
        Returns:
            Tuple of (success, answer_dict)
        """
        try:
            question_text = question.get('text', question.get('Question', ''))
            question_id = question.get('sub_question', question.get('id', question.get('ID', 'Q1')))
            
            # Build prompt for this question
            system_prompt = self._build_generation_prompt()
            user_prompt = self._build_single_user_prompt(question_text, custom_prompt)
            
            # Make API call
            success, response_text = self._call_generation_api(system_prompt, user_prompt, auth_headers)
            
            if not success:
                return False, {}
            
            # Create answer dictionary
            answer = {
                "question_id": question_id,
                "question_text": question_text,
                "answer": response_text.strip(),
                "topic": question.get('topic', 'General')
            }
            
            return True, answer
            
        except Exception as e:
            logger.error(f"Error generating single answer: {str(e)}")
            return False, {}
    
    def _build_generation_prompt(self) -> str:
        """Build the system prompt for answer generation.
        
        Returns:
            System prompt for AI
        """
        return ANSWER_GENERATION_SYSTEM_PROMPT
    
    def _build_topic_user_prompt(self, topic: str, question_text: str, custom_prompt: str = "") -> str:
        """Build user prompt for topic-based generation.
        
        Args:
            topic: Topic name
            question_text: Combined question text for the topic
            custom_prompt: Custom instructions
            
        Returns:
            User prompt for AI
        """
        base_prompt = f"""Please answer the following group of related questions about {topic}:

{question_text}"""
        
        if custom_prompt and custom_prompt.strip():
            base_prompt += f"\n\nAdditional context/instructions: {custom_prompt}"
        
        return base_prompt
    
    def _build_single_user_prompt(self, question_text: str, custom_prompt: str = "") -> str:
        """Build user prompt for single question generation.
        
        Args:
            question_text: The question to answer
            custom_prompt: Custom instructions
            
        Returns:
            User prompt for AI
        """
        base_prompt = f"Please provide a detailed answer to the following question about our product capabilities:\n\n{question_text}"
        
        if custom_prompt and custom_prompt.strip():
            base_prompt += f"\n\nAdditional context/instructions: {custom_prompt}"
        
        return base_prompt
    
    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(RETRY_WAIT_SECONDS))
    def _call_generation_api(
        self,
        system_prompt: str,
        user_prompt: str,
        auth_headers: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Call the AI API for answer generation.
        
        Args:
            system_prompt: System prompt for AI
            user_prompt: User prompt with content
            auth_headers: Authentication headers
            
        Returns:
            Tuple of (success, response_text)
        """
        try:
            endpoint_url = self.settings.answer_generation_endpoint
            model_name = self.settings.models.answer_generation_model
            
            payload = {
                "messages": [
                    {"role": "user", "content": user_prompt}  # Omit system message as requested
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            logger.info(f"Calling {model_name} for answer generation: {endpoint_url}")
            
            response = requests.post(
                endpoint_url,
                headers=auth_headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Check for JWT token expiration (403 with specific error pattern)
            if response.status_code == 403:
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
                                choice = response_data["choices"][0]
                                
                                # Check for message format (OpenAI/Claude style API)
                                if 'message' in choice and 'content' in choice['message']:
                                    response_text = choice['message']['content']
                                # Check for text format (older API style)
                                elif 'text' in choice:
                                    response_text = choice['text']
                                else:
                                    logger.warning("Unexpected response format")
                                    response_text = str(choice)
                                
                                logger.info(f"{model_name} generation API call successful after token refresh")
                                return True, response_text
                            else:
                                logger.error("Unexpected API response format after token refresh")
                                return False, ""
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
            
            elif response.status_code == 200:
                response_data = response.json()
                
                # Extract response text
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    choice = response_data["choices"][0]
                    
                    # Check for message format (OpenAI/Claude style API)
                    if 'message' in choice and 'content' in choice['message']:
                        response_text = choice['message']['content']
                    # Check for text format (older API style)
                    elif 'text' in choice:
                        response_text = choice['text']
                    else:
                        logger.warning("Unexpected response format")
                        response_text = str(choice)
                    
                    logger.info(f"{model_name} generation API call successful")
                    return True, response_text
                else:
                    logger.error("Unexpected API response format")
                    return False, ""
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False, ""
                
        except Exception as e:
            logger.error(f"Error calling {model_name} generation API: {str(e)}")
            return False, ""
    
    def _parse_topic_response(
        self,
        response_text: str,
        topic: str,
        sub_question_ids: List[str],
        original_questions: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Parse AI response for topic-based generation.
        
        Args:
            response_text: Raw response from AI
            topic: Topic name
            sub_question_ids: List of sub-question IDs
            original_questions: List of original question dictionaries
            
        Returns:
            List of answer dictionaries
        """
        try:
            answers = []
            
            # Create a mapping from sub_question_id to original question text
            question_text_map = {}
            if original_questions:
                for q in original_questions:
                    sub_q_id = q.get('sub_question', '')
                    question_text = q.get('text', '')
                    if sub_q_id and question_text:
                        question_text_map[sub_q_id] = question_text
            
            # Parse with regex to match sub-question IDs with their answers
            pattern = r'(\d+(?:\.\d+)*):?\s*(.*?)(?=\n\n\d+(?:\.\d+)*:|\Z)'
            matches = re.findall(pattern, response_text, flags=re.DOTALL)
            
            if matches:
                # Build a dictionary of sub_question_id -> answer
                answer_dict = {q_id.strip(): answer.strip() for q_id, answer in matches}
                
                # Match each sub_question_id to the extracted answers
                for sub_q in sub_question_ids:
                    answer_text = ""
                    
                    # Try to find an exact match first
                    if sub_q in answer_dict:
                        answer_text = answer_dict[sub_q]
                    else:
                        # Try to find partial matches
                        for q_id in answer_dict:
                            if (sub_q.endswith(q_id) or 
                                q_id in sub_q or 
                                sub_q.replace('.', '') == q_id.replace('.', '')):
                                answer_text = answer_dict[q_id]
                                break
                    
                    # If no match found, use the full response
                    if not answer_text:
                        answer_text = response_text.strip()
                    
                    # Get the original question text from the mapping
                    original_question_text = question_text_map.get(sub_q, f"Question {sub_q}")
                    
                    answers.append({
                        "question_id": sub_q,
                        "question_text": original_question_text,
                        "answer": answer_text,
                        "topic": topic
                    })
            else:
                # If no structured parsing worked, create one answer with the full response
                answers.append({
                    "question_id": "combined",
                    "question_text": f"Combined questions for {topic}",
                    "answer": response_text.strip(),
                    "topic": topic
                })
            
            logger.info(f"Parsed {len(answers)} answers for topic {topic}")
            return answers
            
        except Exception as e:
            logger.error(f"Error parsing topic response: {str(e)}")
            return []
    
 