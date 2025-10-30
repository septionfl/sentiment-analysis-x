import subprocess
import pandas as pd
import os
import logging
import time
import platform
from .config import Config

logger = logging.getLogger(__name__)

def is_windows():
    return platform.system() == 'Windows'

def check_node_installation():
    """Check if Node.js and npx are available"""
    try:
        # Check node version
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            logger.info("Node.js found: %s", result.stdout.strip())
        else:
            logger.error("Node.js not found")
            return False
        
        # Check npx version
        result = subprocess.run(['npx', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            logger.info("npx found: %s", result.stdout.strip())
            return True
        else:
            logger.error("npx not found")
            return False
            
    except Exception as e:
        logger.error("Error checking Node.js installation: %s", e)
        return False

def install_dependencies():
    """Install necessary dependencies"""
    logger.info("Checking Node.js installation...")
    
    if not check_node_installation():
        logger.error("Node.js and npx are required but not found.")
        logger.error("Please install Node.js manually from https://nodejs.org/")
        return False
    
    # Try to install tweet-harvest with available versions
    versions_to_try = ["2.6.1", "latest"]
    
    for version in versions_to_try:
        try:
            logger.info("Trying to install tweet-harvest@%s", version)
            
            if version == "latest":
                package_spec = "tweet-harvest"
            else:
                package_spec = f"tweet-harvest@{version}"
            
            result = subprocess.run(
                ['npm', 'install', '-g', package_spec], 
                capture_output=True, 
                text=True, 
                shell=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("Successfully installed %s", package_spec)
                return True
            else:
                logger.warning("Failed to install %s: %s", package_spec, result.stderr)
                
        except Exception as e:
            logger.warning("Error installing %s: %s", package_spec, e)
    
    logger.error("Could not install any version of tweet-harvest")
    return False

def get_available_tweet_harvest_version():
    """Get available tweet-harvest version"""
    versions_to_try = [
        "tweet-harvest@2.6.1",
        "tweet-harvest@2.6.0", 
        "tweet-harvest@2.5.0",
        "tweet-harvest"
    ]
    
    for version_spec in versions_to_try:
        try:
            # Test if this version works
            result = subprocess.run(
                ['npx', version_spec, '--version'],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Found working version: %s", version_spec)
                return version_spec
                
        except Exception:
            continue
    
    # Fallback to the version from original code
    return "tweet-harvest@2.6.1"

def crawl_tweets(search_keyword=None, filename=None, limit=None):
    """Crawl tweets using tweet-harvest with custom search query"""
    if search_keyword is None:
        search_keyword = Config.DEFAULT_SEARCH_QUERY
    if filename is None:
        filename = Config.DEFAULT_FILENAME
    if limit is None:
        limit = Config.DEFAULT_LIMIT
        
    logger.info("Crawling tweets with query: %s", search_keyword)
    
    # Ensure tweets-data directory exists
    os.makedirs("tweets-data", exist_ok=True)
    
    # Get available version
    tweet_harvest_version = get_available_tweet_harvest_version()
    logger.info("Using tweet-harvest version: %s", tweet_harvest_version)
    
    # Build command
    command = [
        'npx', tweet_harvest_version,
        '-o', filename,
        '-s', search_keyword,
        '--tab', 'LATEST', 
        '-l', str(limit),
        '--token', Config.TWITTER_AUTH_TOKEN
    ]
    
    try:
        logger.info("Executing command: %s", ' '.join(command))
        
        # Run the crawling process
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.getcwd()
        )
        
        logger.info("Tweet harvest completed with return code: %s", result.returncode)
        
        if result.stdout:
            logger.debug("STDOUT: %s", result.stdout)
        if result.stderr:
            logger.debug("STDERR: %s", result.stderr)
        
        # Wait for file to be written
        time.sleep(3)
        
        # Check for files in multiple possible locations
        possible_paths = [
            f"tweets-data/{filename}",
            filename,
            f"./{filename}",
            f"../{filename}"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, delimiter=",")
                    logger.info("Successfully crawled %s tweets from: %s", len(df), path)
                    
                    if len(df) > 0:
                        logger.info("First tweet sample: %s", df.iloc[0]['full_text'][:100])
                    else:
                        logger.warning("CSV file exists but contains no tweets")
                    
                    return df
                except Exception as e:
                    logger.error("Error reading CSV file %s: %s", path, e)
                    continue
        
        logger.error("No data file found after crawling")
        return pd.DataFrame()
            
    except subprocess.CalledProcessError as e:
        logger.error("Error during crawling (return code %s)", e.returncode)
        logger.error("STDOUT: %s", e.stdout)
        logger.error("STDERR: %s", e.stderr)
        
        return try_alternative_crawl_method(search_keyword, filename, limit)
            
    except subprocess.TimeoutExpired:
        logger.error("Crawling process timed out after 5 minutes")
        return pd.DataFrame()
        
    except Exception as e:
        logger.error("Unexpected error during crawling: %s", e)
        return pd.DataFrame()

def try_alternative_crawl_method(search_keyword, filename, limit):
    """Try alternative crawling method"""
    logger.info("Trying alternative crawling method...")
    
    # Try different approaches
    approaches = [
        # Approach 1: npx with -y flag
        ['npx', '-y', 'tweet-harvest@2.6.1', '-o', filename, '-s', search_keyword, '--tab', 'LATEST', '-l', str(limit), '--token', Config.TWITTER_AUTH_TOKEN],
        
        # Approach 2: Simple query test
        ['npx', '-y', 'tweet-harvest@2.6.1', '-o', filename, '-s', 'from:tanyakanrl', '-l', '10', '--token', Config.TWITTER_AUTH_TOKEN],
    ]
    
    for i, command in enumerate(approaches, 1):
        try:
            logger.info("Trying approach %s: %s", i, ' '.join(command))
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                logger.info("Alternative approach %s succeeded", i)
                
                # Check for files
                possible_paths = [filename, f"tweets-data/{filename}", f"./{filename}"]
                for path in possible_paths:
                    if os.path.exists(path):
                        df = pd.read_csv(path, delimiter=",")
                        logger.info("Found %s tweets with alternative approach", len(df))
                        return df
            else:
                logger.warning("Alternative approach %s failed: %s", i, result.stderr)
                
        except Exception as e:
            logger.warning("Alternative approach %s error: %s", i, e)
    
    logger.error("All alternative crawl methods failed")
    return pd.DataFrame()