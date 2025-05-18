import requests
import hashlib
from typing import Dict, Any, Optional

def check_hibp(password: str) -> Dict[str, Any]:
    """
    Check password against Have I Been Pwned (HIBP) API using k-Anonymity.
    
    Args:
        password: The password to check against breaches.
        
    Returns:
        A dictionary containing:
        - is_breached: bool indicating if password was found in breaches
        - breach_count: int number of times password was breached (0 if not found)
        - breach_message: Optional[str] formatted message about breaches (None if no breaches)
    """
    try:
        # Generate SHA-1 hash of the password
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]
        
        
        response = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"Add-Padding": "true"},
            timeout=5  
        )
        response.raise_for_status()  
        
        # Parse response
        breaches = {}
        for line in response.text.splitlines():
            if ':' in line:  
                hash_suffix, count = line.split(':', 1)
                try:
                    breaches[hash_suffix] = int(count)
                except ValueError:
                    continue  
        
        breach_count = breaches.get(suffix, 0)
        
        return {
            "is_breached": breach_count > 0,
            "breach_count": breach_count,
            "breach_message": (
                f"This password has appeared in {breach_count:,} data breaches" 
                if breach_count > 0 else None
            )
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error checking HIBP API: {e}")
        return {
            "is_breached": False,
            "breach_count": 0,
            "breach_message": "Could not check breaches due to API error"
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "is_breached": False,
            "breach_count": 0,
            "breach_message": "Could not check breaches due to an error"
        }