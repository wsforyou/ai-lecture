# aionu_llm_client.py

import json
import requests
import time
import logging
from urllib.parse import urljoin
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import mimetypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AionuAPIError(Exception):
    """Custom exception for Aionu API errors"""
    def __init__(self, message: str, status_code: int = None, error_details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_details = error_details
        super().__init__(self.message)


class AionuLLMClient:
    """
    Comprehensive Aionu LLM API Client

    Supports all Aionu API endpoints with proper error handling and retry logic.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Aionu LLM Client

        Args:
            base_url: Base URL for the API (e.g., "https://api.abclab.ktds.com/v1")
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

        # print(f"api_key: {api_key}, base_url: {base_url}")

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "python"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Store conversation state
        self._conversation_id = ""
        self._message_id = ""

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        files: Dict = None,
        max_retries: int = 3,
        base_timeout: int = 30000,
        **kwargs
    ) -> Dict:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            data: Request data
            files: Files for upload
            max_retries: Maximum retry attempts
            base_timeout: Base timeout in seconds
            **kwargs: Additional requests parameters
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

        # Prepare request parameters
        request_kwargs = {
            'timeout': base_timeout,
            **kwargs
        }

        if files:
            # For file uploads, don't set content-type header
            headers = {k: v for k, v in self.headers.items() if k.lower() != 'content-type'}
            request_kwargs['headers'] = headers
            request_kwargs['files'] = files
            if data:
                request_kwargs['data'] = data
        else:
            request_kwargs['headers'] = self.headers
            if data:
                request_kwargs['json'] = data

        for attempt in range(max_retries + 1):
            try:
                current_timeout = base_timeout * (attempt + 1)
                request_kwargs['timeout'] = current_timeout

                #request_kwargs['accept'] = "application/json"


                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} - {method} {url} (timeout: {current_timeout}s)")

                response = self.session.request(method, url, **request_kwargs)

                if response.status_code == 200:
                    return response
                elif response.status_code == 504:
                    logger.warning(f"Gateway timeout (504) on attempt {attempt + 1}")
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AionuAPIError(
                            "Gateway timeout after all retries",
                            status_code=504,
                            error_details={"response": response.text[:500]}
                        )
                else:
                    error_details = self._parse_error_response(response)
                    raise AionuAPIError(
                        f"HTTP {response.status_code} Error",
                        status_code=response.status_code,
                        error_details=error_details
                    )

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AionuAPIError("Request timed out after all retry attempts")
            except requests.exceptions.RequestException as e:
                raise AionuAPIError(f"Request failed: {str(e)}")

        raise AionuAPIError("Failed after all retry attempts")

    def _parse_error_response(self, response) -> Dict:
        """Parse error response"""
        try:
            if 'application/json' in response.headers.get('content-type', ''):
                return response.json()
            else:
                return {"raw_response": response.text[:500]}
        except:
            return {"error": "Could not parse error response"}

    def _parse_streaming_response(self, response) -> str:
        """Parse streaming response with enhanced debugging"""
        try:
            lines = response.text.split('\n')
            message_content = ''
            debug_events = []

            logger.debug(f"Processing {len(lines)} lines from streaming response")

            for line_num, line in enumerate(lines):
                if line.startswith('data: '):
                    json_str = line.replace('data: ', '').strip()
                    if json_str:
                        try:
                            json_data = json.loads(json_str)

                            # Store conversation and message IDs
                            if json_data.get("conversation_id"):
                                self._conversation_id = json_data["conversation_id"]
                            if json_data.get("message_id"):
                                self._message_id = json_data["message_id"]

                            event = json_data.get('event', '')
                            debug_events.append(event)

                            # Handle different event types
                            if event in ['message', 'agent_message']:
                                answer = json_data.get('answer', "")
                                if answer:
                                    message_content += answer
                            elif event == 'agent_thought':
                                # Some agents might use agent_thought
                                thought = json_data.get('thought', "")
                                if thought:
                                    message_content += thought
                            elif event == 'message_file':
                                # Handle file-based responses
                                file_content = json_data.get('content', "")
                                if file_content:
                                    message_content += file_content
                            elif event == 'message_end':
                                usage = json_data.get("metadata", {}).get("usage", {})
                                logger.info(f"Message completed. Usage: {usage}")
                            elif event == 'error':
                                error_msg = json_data.get('message', 'Unknown error')
                                logger.error(f"Stream error: {error_msg}")
                                if "Query or prefix prompt is too long" in error_msg:
                                    raise AionuAPIError(
                                        f"Stream error: {error_msg}",
                                        status_code=json_data.get('status_code', 504),
                                        error_details=json_data
                                    )
                            # Debug: log all events for troubleshooting
                            logger.debug(f"Line {line_num}: Event '{event}', Data keys: {list(json_data.keys())}")

                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON line {line_num}: {json_str[:100]}... - {e}")

            # Debug information
            logger.debug(f"Processed events: {debug_events}")
            logger.debug(f"Final message length: {len(message_content)} characters")

            if not message_content and debug_events:
                logger.warning(f"No content extracted despite events: {debug_events}")
                # Try to extract content from raw response as fallback
                if response.text and len(response.text) > 100:
                    logger.info("Attempting fallback content extraction")
                    # Look for content patterns in the raw response
                    import re
                    content_matches = re.findall(r'"answer"\s*:\s*"([^"]*)"', response.text)
                    if content_matches:
                        message_content = ''.join(content_matches)
                        logger.info(f"Fallback extraction found {len(message_content)} characters")

            return message_content
        except Exception as e:
            logger.error(f"Error processing streaming response: {str(e)}")
            logger.debug(f"Raw response (first 500 chars): {response.text[:500]}")
            return ""

    # Chat Messages API
    def send_message(
        self,
        query: str,
        user: str,
        response_mode: str = "streaming",
        conversation_id: str = "",
        inputs: Dict = None,
        files: List[Dict] = None,
        auto_generate_name: bool = False,
        max_retries: int = 3,
        base_timeout: int = 30000
    ) -> Union[str, Dict]:
        """
        Send a chat message

        Args:
            query: User's question
            user: Unique user identifier
            response_mode: "streaming" or "blocking"
            conversation_id: Conversation ID to continue, empty for new conversation
            inputs: Pre-defined variables
            files: List of file objects for image processing
            auto_generate_name: Auto-generate conversation title
            max_retries: Maximum retry attempts
            base_timeout: Base timeout in seconds
        """
        data = {
            "query": query,
            "user": user,
            "response_mode": response_mode,
            "conversation_id": conversation_id or self._conversation_id,
            "inputs": inputs or {},
            "auto_generate_name": auto_generate_name
        }

        if files:
            data["files"] = files

        response = self._make_request(
            "POST",
            "/chat-messages",
            data=data,
            max_retries=max_retries,
            base_timeout=base_timeout
        )

        if response_mode == "streaming":
            return self._parse_streaming_response(response)
        else:
            return response.json()

    # File Upload API
    def upload_file(self, file_path: str, user: str) -> Dict:
        """
        Upload a file for use in messages

        Args:
            file_path: Path to the file
            user: User identifier
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type or not mime_type.startswith('image/'):
            raise ValueError("Only image files are supported (png, jpg, jpeg, webp, gif)")

        files = {
            'file': (file_path.name, open(file_path, 'rb'), mime_type)
        }
        data = {'user': user}

        try:
            response = self._make_request("POST", "/files/upload", data=data, files=files)
            return response.json()
        finally:
            files['file'][1].close()

    # Task Control API
    def stop_task(self, task_id: str, user: str) -> Dict:
        """
        Stop a streaming task

        Args:
            task_id: Task ID to stop
            user: User identifier
        """
        data = {"user": user}
        response = self._make_request("POST", f"/chat-messages/{task_id}/stop", data=data)
        return response.json()

    # Message Feedback API
    def send_feedback(self, message_id: str, rating: str, user: str) -> Dict:
        """
        Send feedback for a message

        Args:
            message_id: Message ID
            rating: "like", "dislike", or "null"
            user: User identifier
        """
        if rating not in ["like", "dislike", "null"]:
            raise ValueError("Rating must be 'like', 'dislike', or 'null'")

        data = {"rating": rating, "user": user}
        response = self._make_request("POST", f"/messages/{message_id}/feedbacks", data=data)
        return response.json()

    # Suggested Questions API
    def get_suggested_questions(self, message_id: str) -> Dict:
        """
        Get suggested questions for a message

        Args:
            message_id: Message ID
        """
        response = self._make_request("GET", f"/messages/{message_id}/suggested")
        return response.json()

    # Message History API
    def get_messages(
        self,
        conversation_id: str,
        user: str,
        first_id: str = None,
        limit: int = 20
    ) -> Dict:
        """
        Get message history

        Args:
            conversation_id: Conversation ID
            user: User identifier
            first_id: Starting message ID
            limit: Number of messages to retrieve
        """
        params = {
            "conversation_id": conversation_id,
            "user": user,
            "limit": limit
        }
        if first_id:
            params["first_id"] = first_id

        response = self._make_request("GET", "/messages", **{"params": params})
        return response.json()

    # Conversations API
    def get_conversations(
        self,
        user: str,
        last_id: str = None,
        limit: int = 20,
        pinned: bool = None
    ) -> Dict:
        """
        Get conversation list

        Args:
            user: User identifier
            last_id: Last conversation ID for pagination
            limit: Number of conversations to retrieve
            pinned: Filter pinned conversations only
        """
        params = {"user": user, "limit": limit}
        if last_id:
            params["last_id"] = last_id
        if pinned is not None:
            params["pinned"] = str(pinned).lower()

        response = self._make_request("GET", "/conversations", **{"params": params})
        return response.json()

    def delete_conversation(self, conversation_id: str, user: str) -> Dict:
        """
        Delete a conversation

        Args:
            conversation_id: Conversation ID to delete
            user: User identifier
        """
        data = {"user": user}
        response = self._make_request("DELETE", f"/conversations/{conversation_id}", data=data)
        return response.json()

    def rename_conversation(
        self,
        conversation_id: str,
        name: str = None,
        auto_generate: bool = False
    ) -> Dict:
        """
        Rename a conversation

        Args:
            conversation_id: Conversation ID
            name: New conversation name
            auto_generate: Auto-generate name
        """
        data = {"auto_generate": auto_generate}
        if name:
            data["name"] = name

        response = self._make_request("POST", f"/conversations/{conversation_id}/name", data=data)
        return response.json()

    # Audio APIs
    def audio_to_text(self, audio_file_path: str, user: str) -> Dict:
        """
        Convert audio to text

        Args:
            audio_file_path: Path to audio file
            user: User identifier
        """
        file_path = Path(audio_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Check file extension
        supported_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        if file_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported audio format. Supported: {supported_extensions}")

        mime_type = f"audio/{file_path.suffix.lstrip('.')}"
        files = {
            'file': (file_path.name, open(file_path, 'rb'), mime_type)
        }
        data = {'user': user}

        try:
            response = self._make_request("POST", "/audio-to-text", data=data, files=files)
            return response.json()
        finally:
            files['file'][1].close()

    def text_to_audio(self, text: str, user: str, streaming: bool = False) -> requests.Response:
        """
        Convert text to audio

        Args:
            text: Text to convert
            user: User identifier
            streaming: Whether to stream audio
        """
        # Use form data for text-to-audio
        headers = {k: v for k, v in self.headers.items() if k.lower() != 'content-type'}
        headers['Content-Type'] = 'audio/wav'

        data = {
            'text': text,
            'user': user,
            'streaming': str(streaming).lower()
        }

        response = self._make_request(
            "POST",
            "/text-to-audio",
            data=data,
            files={},  # This will trigger form data mode
            **{"headers": headers}
        )
        return response

    # App Configuration APIs
    def get_parameters(self, user: str) -> Dict:
        """
        Get app parameters and configuration

        Args:
            user: User identifier
        """
        params = {"user": user}
        response = self._make_request("GET", "/parameters", **{"params": params})
        return response.json()

    def get_meta(self, user: str) -> Dict:
        """
        Get app metadata including tool icons

        Args:
            user: User identifier
        """
        params = {"user": user}
        response = self._make_request("GET", "/meta", **{"params": params})
        return response.json()

    # Convenience Methods
    def start_conversation(self, query: str, user: str, **kwargs) -> Union[str, Dict]:
        """
        Start a new conversation

        Args:
            query: Initial message
            user: User identifier
            **kwargs: Additional parameters for send_message
        """
        self._conversation_id = ""  # Reset conversation ID
        return self.send_message(query, user, conversation_id="", **kwargs)

    def continue_conversation(self, query: str, user: str, **kwargs) -> Union[str, Dict]:
        """
        Continue existing conversation

        Args:
            query: Message to send
            user: User identifier
            **kwargs: Additional parameters for send_message
        """
        return self.send_message(query, user, **kwargs)

    def get_conversation_id(self) -> str:
        """Get current conversation ID"""
        return self._conversation_id

    def get_message_id(self) -> str:
        """Get current message ID"""
        return self._message_id

    def set_conversation_id(self, conversation_id: str):
        """Set conversation ID for subsequent messages"""
        self._conversation_id = conversation_id


# Example usage and testing
def example_usage():
    """Example usage of the AionuLLMClient"""

    # Initialize client
    client = AionuLLMClient(
        base_url="https://api.abclab.ktds.com/v1",
        api_key="app-7fuLksdLDCYiF5BsrBML0jMl"
    )

    user_id = "test_user_123"

    try:
        # 1. Start a new conversation
        print("=== Starting new conversation ===")
        response = client.start_conversation(
            query="Hello, can you analyze this Java code for code quality?",
            user=user_id,
            response_mode="streaming"
        )
        print(f"Response: {response}")
        print(f"Conversation ID: {client.get_conversation_id()}")

        # 2. Continue the conversation
        print("\n=== Continuing conversation ===")
        java_code = """
        public class Example {
            public void method() {
                System.out.println("Hello World");
            }
        }
        """
        response = client.continue_conversation(
            query=f"Please analyze this code:\n{java_code}",
            user=user_id,
            response_mode="streaming"
        )
        print(f"Response: {response}")

        # 3. Get conversation history
        print("\n=== Getting conversation history ===")
        history = client.get_messages(
            conversation_id=client.get_conversation_id(),
            user=user_id
        )
        print(f"History: {json.dumps(history, indent=2, ensure_ascii=False)}")

        # 4. Send feedback
        if client.get_message_id():
            print("\n=== Sending feedback ===")
            feedback = client.send_feedback(
                message_id=client.get_message_id(),
                rating="like",
                user=user_id
            )
            print(f"Feedback: {feedback}")

        # 5. Get app parameters
        print("\n=== Getting app parameters ===")
        params = client.get_parameters(user=user_id)
        print(f"Parameters: {json.dumps(params, indent=2, ensure_ascii=False)}")

    except AionuAPIError as e:
        print(f"API Error: {e.message}")
        if e.error_details:
            print(f"Details: {e.error_details}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Run example
    example_usage()