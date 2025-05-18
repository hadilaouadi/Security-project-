from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import os
from pathlib import Path
import boto3
from hibp import check_hibp
from validation import validate_password
from typing import Dict, Any, List

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_DIR = "static/audio"
Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)


try:
    polly = boto3.client('polly')
    TTS_ENABLED = True
except:
    TTS_ENABLED = False
    print("AWS Polly not configured - TTS will use Web Speech API only")
@app.post("/api/check-password")
async def check_password(data: Dict[str, Any]):
    try:
        password = data.get("password", "")
        tts_enabled = data.get("tts_enabled", False)
        
        if not password:
            raise HTTPException(status_code=400, detail="Password cannot be empty")
        
        
        validation_result = validate_password(password)
        
 
        hibp_result = check_hibp(password)
        validation_result.update(hibp_result)
        
        # Generate appropriate tarot card response
        card_data = generate_tarot_response(validation_result)
        
        response = {
            "verdict": "strong" if validation_result["is_strong"] else "weak",
            "card": card_data,
            "suggestions": generate_suggestions(validation_result),
            "validation_details": validation_result
        }
        
        if tts_enabled:
            response["tts_audio"] = generate_tts_audio(card_data["message"])
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def generate_tarot_response(validation: Dict[str, Any]) -> Dict[str, Any]:
    breach_count = validation.get("breach_count", 0)
    is_breached = validation.get("is_breached", False)
    breach_message = validation.get("breach_message", "")
    
    base_response = {
        "technical": {
            "is_breached": is_breached,
            "breach_count": breach_count,
            "breach_message": breach_message if is_breached else "No breaches found"
        }
    }
    
    if not validation.get("length_ok", True):
        lines = [
        "I foresee... a data breach in your near future!",
        "Your password will fail you before the next moonrise—too short to withstand the storm.   ",
         ]
        if is_breached:
            lines.append(breach_message)
        return {
            **base_response,
            "name": "The Fool",
            "image": "fool_card.png",
            "message": "\n".join(lines),           
        }
    elif not validation.get("complexity_ok", True):
         lines = [
         "I see fractured power",
         "A spell too weak to protect you ",
            ]
         if is_breached:
            lines.append(breach_message)
         return {
            **base_response,
            "name": "The Broken Wand",
            "image": "the-broken_wand.png",
            "message": "\n".join(lines),         } 
    
    else:
        return {
            **base_response,
            "name": "The Star",
            "image": "the-star_card.png",
            "message": "The stars align in your favor! No breaches detected in the cosmic waters.",
           
        }

def generate_suggestions(validation: Dict[str, Any]) -> List[str]:
    suggestions = []
    if not validation["length_ok"]:
        suggestions.append("Make it longer (at least 12 characters)")
    if not validation["has_upper"]:
        suggestions.append("Add uppercase letters")
    if not validation["has_lower"]:
        suggestions.append("Add lowercase letters")
    if not validation["has_digit"]:
        suggestions.append("Add numbers")
    if not validation["has_symbol"]:
        suggestions.append("Add symbols (!@#$% etc.)")
    if validation.get("is_breached", False):
        suggestions.append("This password is compromised - choose a completely different one")
    return suggestions

def generate_tts_audio(message: str) -> str:
    """Generate TTS audio using AWS Polly (if configured)"""
    # Early return if TTS is disabled or message is empty
    if not TTS_ENABLED or not message.strip():
        return ""
    
    try:
        # Check if polly client exists and is initialized
        if not hasattr(generate_tts_audio, '_polly_client'):
            # Lazy initialization 
            try:
                generate_tts_audio._polly_client = boto3.client('polly')
            except Exception as init_error:
                print(f"Polly initialization failed: {init_error}")
                return ""

        # Generate speech
        response = generate_tts_audio._polly_client.synthesize_speech(
            Text=message,
            OutputFormat='mp3',
            VoiceId='Amy'
        )
        
        # Save audio file
        filename = f"audio_{hashlib.md5(message.encode()).hexdigest()}.mp3"
        filepath = f"{AUDIO_DIR}/{filename}"
        
        Path(AUDIO_DIR).mkdir(exist_ok=True)  # Ensure directory exists
        
        with open(filepath, 'wb') as f:
            f.write(response['AudioStream'].read())
        
        return f"/static/audio/{filename}"
        
    except Exception as e:
        print(f"TTS generation failed: {e}")
        return ""
