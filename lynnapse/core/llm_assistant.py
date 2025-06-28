"""
LLM Assistant for University Discovery

This module provides OpenAI-powered assistance for discovering university
faculty directory structures when traditional methods fail.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from openai import AsyncOpenAI
from bs4 import BeautifulSoup
import httpx

from lynnapse.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMDiscoveryResult:
    """Result from LLM-assisted university discovery."""
    faculty_directory_paths: List[str]
    department_paths: Dict[str, List[str]] # Maps department name to a list of URLs
    confidence_score: float
    reasoning: str
    cost_estimate: float
    cached: bool = False


class LLMAssistant:
    """OpenAI-powered assistant for university structure discovery."""
    
    def __init__(self, cache_client: Optional[Any] = None):
        """Initialize the LLM assistant."""
        settings = get_settings()
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured. LLM assistant will be disabled.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM assistant."""
        return """
You are an expert web scraping assistant. Your goal is to find the URLs for faculty and department directory pages at a given university.

You will be given the university name, its base URL, and a snippet of its homepage HTML.

Instructions:
1.  **Analyze the HTML:** Look for navigation bars, menus, and footer links. Keywords to look for are "Faculty", "People", "Directory", "Academics", "Departments", "Schools", "Research".
2.  **Identify Potential Paths:** Extract the `href` attributes from `<a>` tags that seem relevant.
3.  **Filter and Refine:**
    -   Prioritize links that clearly point to academic or personnel directories.
    -   Filter out irrelevant links like "Admissions", "Contact Us", "News", "Events", "Login".
    -   Pay attention to the URL structure. A path like `/academics/departments` is a strong signal.
4.  **Handle Department-Specific Queries:** If a department is specified, focus your search on finding the faculty page for that specific department.
5.  **Provide Reasoning:** Briefly explain why you chose the paths you did. This helps verify the quality of the result.

Output Format:
Return a JSON object with the following structure:
{
  "faculty_directory_paths": ["/path/to/faculty", "/path/to/people"],
  "department_paths": {
    "Computer Science": ["/cs/faculty", "/engineering/cs/people"],
    "Psychology": ["/psych/faculty-directory"]
  },
  "confidence_score": 0.85,
  "reasoning": "Found a clear 'Faculty & Staff' link in the main navigation. The department pages were located under an 'Academics' section."
}
"""

    def _get_user_prompt(self, university_name: str, base_url: str, html_snippet: str, department_name: Optional[str] = None) -> str:
        """Get the user prompt for the LLM assistant."""
        if department_name:
            return (
                f"University: {university_name}\\n"
                f"Department: {department_name}\\n"
                f"Base URL: {base_url}\\n"
                f"HTML Snippet:\\n---\\n{html_snippet}\\n---\\n\\n"
                f"Task: Find the specific faculty directory URL for the **{department_name}** department. "
                "Analyze the provided HTML from the university's department page. Provide the most likely paths."
            )
        else:
            return (
                f"University: {university_name}\\n"
                f"Base URL: {base_url}\\n"
                f"HTML Snippet:\\n---\\n{html_snippet}\\n---\\n\\n"
                "Task: Find the main faculty directory and a list of all academic department pages. "
                "Analyze the provided HTML from the university's homepage. Provide the most likely paths for general faculty and for each department you can find."
            )

    async def discover_faculty_directories(self, university_name: str, base_url: str, department_name: Optional[str] = None) -> LLMDiscoveryResult:
        """Use LLM to discover faculty directory paths for a university."""
        if not self.client:
            logger.warning("LLM client not available, skipping LLM discovery.")
            return None
            
        logger.info(f"Using LLM to discover faculty directories for {university_name}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, follow_redirects=True, timeout=20.0)
                response.raise_for_status()
                html_snippet = response.text
        except httpx.RequestError as e:
            logger.error(f"Error fetching homepage for LLM analysis: {e}")
            return None

        # Create a BeautifulSoup object to extract a snippet
        soup = BeautifulSoup(html_snippet, 'html.parser')
        body_snippet = str(soup.body)[:4000] # Limit the size of the snippet

        user_prompt = self._get_user_prompt(university_name, base_url, body_snippet, department_name)
        system_prompt = self._get_system_prompt()

        try:
            completion = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            
            response_content = completion.choices[0].message.content
            logger.debug(f"LLM Raw Response: {response_content}")
            
            data = json.loads(response_content)
            
            return LLMDiscoveryResult(
                faculty_directory_paths=data.get("faculty_directory_paths", []),
                department_paths=data.get("department_paths", {}),
                confidence_score=data.get("confidence_score", 0.0),
                reasoning=data.get("reasoning", ""),
                cost_estimate=0.0, # Cost estimation can be added here
                cached=False
            )

        except Exception as e:
            logger.error(f"Error communicating with LLM: {e}")
            return None
