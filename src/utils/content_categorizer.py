"""
Content categorization utilities using OpenAI.
"""

from typing import Dict, List, Optional
import json
from openai import OpenAI


class ContentCategorizer:
    """Categorizes scraped content into structured fields using OpenAI."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def categorize_content(self, title: str, content: str, url: str) -> Dict[str, str]:
        """
        Categorize title and content into structured fields.
        
        Args:
            title: The page title
            content: The page content
            url: The source URL
            
        Returns:
            Dictionary with categorized fields
        """
        # Define the target fields
        target_fields = [
            "Overview",
            "Key Benefits", 
            "Mechanism of Action",
            "Molecular Information",
            "Research Indications",
            "Research Protocols",
            "Peptide Interactions",
            "How to Reconstitute",
            "Quality Indicators",
            "What to Expect",
            "Side Effects & Safety",
            "References",
            "Quick Start Guide",
            "Storage",
            "Cycle Length",
            "Break Between"
        ]
        
        # Create the prompt
        prompt = f"""
Please analyze the following peptide research content and categorize it into these specific fields:

URL: {url}
Title: {title}
Content: {content}

Required fields:
{json.dumps(target_fields, indent=2)}

Instructions:
1. Read through all the content carefully
2. For each required field, extract relevant information if present
3. If no information exists for a field, leave it empty ("")
4. Be concise but comprehensive - extract the most relevant information
5. Focus on factual information from the content
6. Return as a JSON object with the field names as keys

Example format:
{{
    "Overview": "Brief description of the peptide",
    "Key Benefits": "List of main benefits",
    "Mechanism of Action": "How it works",
    ...
}}

Please provide the categorized data as valid JSON only:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using a more common model
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing peptide research content and categorizing it into structured fields. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Extract and parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].strip()
            else:
                json_text = response_text
            
            # Parse JSON
            categorized_data = json.loads(json_text)
            
            # Ensure all required fields are present
            result = {}
            for field in target_fields:
                result[field] = categorized_data.get(field, "")
            
            return result
            
        except Exception as e:
            print(f"Error categorizing content: {str(e)}")
            # Return empty fields on error
            return {field: "" for field in target_fields}
    
    def categorize_multiple_pages(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Categorize multiple pages of content.
        
        Args:
            pages_data: List of dictionaries with title, content, and url
            
        Returns:
            List of dictionaries with categorized fields
        """
        results = []
        
        for i, page_data in enumerate(pages_data):
            print(f"Categorizing page {i+1}/{len(pages_data)}: {page_data.get('title', 'Unknown')}")
            
            categorized = self.categorize_content(
                title=page_data.get('title', ''),
                content=page_data.get('content', ''),
                url=page_data.get('url', '')
            )
            
            # Add metadata
            categorized['_source_title'] = page_data.get('title', '')
            categorized['_source_url'] = page_data.get('url', '')
            categorized['_source_content'] = page_data.get('content', '')
            
            results.append(categorized)
        
        return results
