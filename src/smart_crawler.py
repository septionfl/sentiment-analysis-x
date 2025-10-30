import logging
import pandas as pd
from .groq_parser import GroqQueryParser
from .crawler import crawl_tweets

logger = logging.getLogger(__name__)

class SmartCrawler:
    def __init__(self):
        self.parser = GroqQueryParser()
        self.max_retries = 2
    
    def smart_search(self, user_input):
        """
        Smart search with GROQ-powered query optimization and fallback strategies
        """
        logger.info(f"Smart search initiated for: {user_input}")
        
        # Step 1: Parse natural language with GROQ
        optimized_query = self.parser.parse_natural_language(user_input)
        logger.info(f"Input parsed to: {optimized_query}")
        
        # Step 2: Validate query complexity
        complexity_check = self.parser.validate_query_complexity(optimized_query)
        
        # Step 3: Try the optimized query first
        result = self._try_crawl(optimized_query, "Optimized query")
        
        if not result.empty:
            return {
                'success': True,
                'original_input': user_input,
                'used_query': optimized_query,
                'data': result,
                'query_type': 'ai_optimized',
                'complexity_check': complexity_check
            }
        
        # Step 4: If optimized fails, try fallback strategies
        fallback_queries = self._generate_fallback_queries(user_input, optimized_query)
        
        for i, (fallback_query, strategy) in enumerate(fallback_queries):
            if i >= self.max_retries:
                break
                
            logger.info(f"Trying fallback strategy {i+1}: {strategy}")
            result = self._try_crawl(fallback_query, f"Fallback {i+1}")
            
            if not result.empty:
                return {
                    'success': True,
                    'original_input': user_input,
                    'used_query': fallback_query,
                    'data': result,
                    'query_type': f'fallback_{i+1}',
                    'strategy': strategy,
                    'complexity_check': complexity_check
                }
        
        # Step 5: All strategies failed
        return {
            'success': False,
            'original_input': user_input,
            'used_query': optimized_query,
            'data': pd.DataFrame(),
            'query_type': 'failed',
            'complexity_check': complexity_check
        }
    
    def _generate_fallback_queries(self, original_input, optimized_query):
        """
        Generate fallback queries with different strategies
        """
        fallbacks = []
        
        # Strategy 1: Simplify by removing date filters
        if 'since:' in optimized_query or 'until:' in optimized_query:
            simple_query = self._remove_date_filters(optimized_query)
            fallbacks.append((simple_query, "Remove date filters"))
        
        # Strategy 2: Remove language filter
        if 'lang:' in optimized_query:
            no_lang_query = self._remove_language_filter(optimized_query)
            fallbacks.append((no_lang_query, "Remove language filter"))
        
        # Strategy 3: Extract main keywords only
        keyword_query = self._extract_keywords(original_input)
        if keyword_query and keyword_query != optimized_query:
            fallbacks.append((keyword_query, "Keyword-only approach"))
        
        # Strategy 4: Use complexity check alternative
        complexity_check = self.parser.validate_query_complexity(optimized_query)
        if complexity_check.get('is_too_restrictive', False):
            alt_query = complexity_check.get('alternative_query', optimized_query)
            if alt_query != optimized_query:
                fallbacks.append((alt_query, "Complexity-reduced query"))
        
        return fallbacks
    
    def _try_crawl(self, query, description):
        """Attempt to crawl with a given query"""
        try:
            logger.info(f"Attempting crawl: {description} - '{query}'")
            result = crawl_tweets(search_keyword=query, limit=50)
            return result
        except Exception as e:
            logger.error(f"Crawl failed for '{query}': {e}")
            return pd.DataFrame()
    
    def _remove_date_filters(self, query):
        """Remove since: and until: filters from query"""
        import re
        return re.sub(r'(since|until):\S+\s*', '', query).strip()
    
    def _remove_language_filter(self, query):
        """Remove lang: filter from query"""
        import re
        return re.sub(r'lang:\S+\s*', '', query).strip()
    
    def _extract_keywords(self, text):
        """Extract main keywords from natural language"""
        stop_words = {
            'tentang', 'mengenai', 'dari', 'pada', 'di', 'ke', 'yang', 
            'untuk', 'dengan', 'bagaimana', 'apa', 'siapa', 'kapan', 'dimana'
        }
        words = text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return ' '.join(keywords[:3]) if keywords else text