import re
from typing import Dict, Any

def validate_password(password: str) -> Dict[str, Any]:
    """Validate password against OWASP standards"""
    validation = {
        "length": len(password),
        "length_ok": len(password) >= 12,
        "has_upper": bool(re.search(r'[A-Z]', password)),
        "has_lower": bool(re.search(r'[a-z]', password)),
        "has_digit": bool(re.search(r'[0-9]', password)),
        "has_symbol": bool(re.search(r'[^a-zA-Z0-9]', password)),
        "is_common": is_common_pattern(password),
        "is_strong": False
    }
    
    # Check complexity 
    validation["complexity_ok"] = (
        validation["length_ok"] and
        validation["has_upper"] and
        validation["has_lower"] and
        validation["has_digit"] and
        validation["has_symbol"]
    )
    

    validation["is_strong"] = (
        validation["complexity_ok"] and 
        not validation["is_common"]
    )
    
    return validation

def is_common_pattern(password: str) -> bool:
    """Check for common patterns (qwerty, 123456, etc.)"""
    common_patterns = [
        r'123456',
        r'password',
        r'qwerty',
        r'abc123',
        r'letmein',
        r'admin',
        r'welcome',
        r'football',
        r'iloveyou',
        r'monkey'
    ]
    
    lower_pass = password.lower()
    return any(re.search(pattern, lower_pass) for pattern in common_patterns)