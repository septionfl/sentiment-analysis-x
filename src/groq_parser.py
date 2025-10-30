import os
import logging
import requests
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GroqQueryParser:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Fast and cost-effective
        
    def _call_groq_api(self, prompt):
        """
        Call GROQ API using direct HTTP requests
        """
        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "temperature": 0.3,
            "max_tokens": 150
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GROQ API request failed: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"GROQ API response parsing failed: {e}")
            return None
    
    def parse_natural_language(self, user_input):
        """
        Parse natural language input into optimized Twitter search query using GROQ
        """
        try:
            prompt = f"""
            Convert this natural language query into an effective Twitter/X search query:
            
            USER INPUT: "{user_input}"
            
            RULES:
            1. Use Twitter Advanced Search operators: from:, since:, until:, lang:, etc.
            2. For Indonesian content, add "lang:id" when relevant
            3. Use quotes for exact phrases
            4. Use - to exclude terms
            5. Use OR for alternatives
            6. Keep it under 500 characters
            7. Make it specific but effective for sentiment analysis
            8. If no date specified, use reasonable default (last 30 days)
            
            Respond ONLY with the optimized search query, no explanations.
            
            Examples:
            - "sentimen pemilu 2024" -> "#pemilu2024 lang:id since:2024-01-01"
            - "tweet dari jokowi bulan januari" -> "from:jokowi since:2024-01-01 until:2024-01-31 lang:id"
            - "opinion about python programming" -> "python programming"
            - "startup di indonesia" -> "startup Indonesia OR startup lang:id"
            
            OPTIMIZED QUERY:
            """
            
            optimized_query = self._call_groq_api(prompt)
            
            if optimized_query:
                optimized_query = optimized_query.replace('"', '')  # Remove quotes if any
                optimized_query = optimized_query.split('\n')[0]   # Take only first line
                
                logger.info(f"GROQ parsed '{user_input}' -> '{optimized_query}'")
                return optimized_query
            else:
                logger.warning("GROQ API returned no response, using fallback")
                return self.fallback_parse(user_input)
            
        except Exception as e:
            logger.error(f"GROQ parsing failed: {e}")
            return self.fallback_parse(user_input)
    
    def fallback_parse(self, user_input):
        """
        Fallback parser when GROQ fails - basic keyword extraction
        """
        # Simple keyword extraction for common patterns
        keywords = []
        
        # Extract basic keywords (remove common stop words)
        stop_words = {'tentang', 'mengenai', 'dari', 'pada', 'di', 'ke', 'yang', 'untuk', 'dengan'}
        words = user_input.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add language filter if Indonesian context detected
        indonesian_indicators = {'indonesia', 'indonesian', 'jokowi', 'pemilu', 'presiden', 'menteri'}
        if any(indicator in user_input.lower() for indicator in indonesian_indicators):
            keywords.append('lang:id')
        
        return ' '.join(keywords[:5])  # Limit to 5 keywords
    
    def validate_query_complexity(self, query):
        """
        Check if query might be too complex/restrictive and provide suggestions
        """
        try:
            prompt = f"""
            Analyze this Twitter search query and suggest if it might be too restrictive:
            
            QUERY: "{query}"
            
            Check for:
            1. Overly specific date ranges (less than 3 days)
            2. Too many exclusion terms
            3. Very niche keywords
            4. Combination of multiple restrictive filters
            
            Respond with JSON only:
            {{
                "is_too_restrictive": true/false,
                "confidence": 0.0-1.0,
                "suggestions": ["suggestion1", "suggestion2"],
                "alternative_query": "less restrictive version if needed"
            }}
            """
            
            analysis_response = self._call_groq_api(prompt)
            
            if analysis_response:
                # Try to extract JSON from response
                try:
                    # Find JSON in the response
                    start_idx = analysis_response.find('{')
                    end_idx = analysis_response.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = analysis_response[start_idx:end_idx]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse GROQ response as JSON")
            
            # Default response if parsing fails
            return {
                "is_too_restrictive": False,
                "confidence": 0.5,
                "suggestions": ["No analysis available"],
                "alternative_query": query
            }
                
        except Exception as e:
            logger.error(f"GROQ complexity analysis failed: {e}")
            return {
                "is_too_restrictive": False,
                "confidence": 0.3,
                "suggestions": ["Analysis unavailable"],
                "alternative_query": query
            }