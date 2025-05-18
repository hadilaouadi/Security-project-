document.addEventListener('DOMContentLoaded', function() {
   
    const passwordInput = document.getElementById('passwordInput');
    const toggleVisibility = document.getElementById('toggleVisibility');
    const ttsToggle = document.getElementById('ttsToggle');
    const tarotCard = document.getElementById('tarotCard');
    const cardImage = document.getElementById('cardImage');
    const cardName = document.getElementById('cardName');
    const cardMessage = document.getElementById('cardMessage');
    const suggestionList = document.getElementById('suggestionList');
    const validationList = document.getElementById('validationList');
    const ttsPlayer = document.getElementById('ttsPlayer');
    
    
    let isPasswordVisible = false;
    let debounceTimer;
    let currentSpeech = null;

    
    toggleVisibility.addEventListener('click', function() {
        isPasswordVisible = !isPasswordVisible;
        passwordInput.type = isPasswordVisible ? 'text' : 'password';
        toggleVisibility.textContent = isPasswordVisible ? '🙈' : '👁️';
    });
    
    // Check password strength with debounce
    passwordInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const password = passwordInput.value.trim();
            if (password.length === 0) {
                resetDisplay();
                return;
            }
            checkPasswordStrength(password);
        }, 500);
    });

    // Main password check function
    async function checkPasswordStrength(password) {
        try {
            stopCurrentSpeech(); // Stop any ongoing speech
            
            const response = await fetch('http://localhost:8000/api/check-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    password: password,
                    tts_enabled: ttsToggle.checked
                })
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            updateDisplay(data);
            
            if (ttsToggle.checked) {
                await speakMessage(data.card.message, data);
            }
            
        } catch (error) {
            console.error('Password check failed:', error);
            showError("Could not check password. Please try again.");
        }
    }

    // Display update function
    function updateDisplay(data) {
        // Card display
        document.querySelector('.card-placeholder').classList.add('hidden');
        tarotCard.classList.remove('hidden');
        
        // Card content
        cardName.textContent = data.card.name;
        cardMessage.textContent = data.card.message;
        cardImage.src = `assets/images/${data.card.image}`;
        cardImage.alt = `${data.card.name} Tarot Card`;
        
        // Animation
        tarotCard.classList.add('card-reveal');
        setTimeout(() => tarotCard.classList.remove('card-reveal'), 1500);
        
        // Suggestions
        suggestionList.innerHTML = data.suggestions?.map(suggestion => 
            `<li>${suggestion}</li>`
        ).join('') || '';
        document.getElementById('suggestions').classList.toggle('hidden', !data.suggestions?.length);
        
        // Validation details
        validationList.innerHTML = [
            {text: `Length: ${data.validation_details.length} characters`, valid: data.validation_details.length_ok},
            {text: 'Contains uppercase letters', valid: data.validation_details.has_upper},
            {text: 'Contains lowercase letters', valid: data.validation_details.has_lower},
            {text: 'Contains numbers', valid: data.validation_details.has_digit},
            {text: 'Contains symbols', valid: data.validation_details.has_symbol},
            {text: 'Not a common pattern', valid: !data.validation_details.is_common},
            {text: 'Not found in breaches', valid: !data.validation_details.is_breached}
        ].map(item => 
            `<li style="color: ${item.valid ? 'var(--success)' : 'var(--danger)'}">${item.text}</li>`
        ).join('');
        
        document.getElementById('validationDetails').classList.remove('hidden');
        
        
        setColorScheme(data.verdict);
    }

    // Speech functions
    async function speakMessage(message, data) {
        try {
            stopCurrentSpeech();
            
            
            if ('speechSynthesis' in window) {
                await loadVoices(); 
                
                const utterance = new SpeechSynthesisUtterance(message);
                utterance.lang = 'en-US';
                utterance.rate = 0.9;
                utterance.pitch = 1.1;
                
                const voices = window.speechSynthesis.getVoices();
                const englishVoice = voices.find(v => v.lang.includes('en-US') && v.name.includes('Female')) || 
                                   voices.find(v => v.lang.includes('en'));
                
                if (englishVoice) utterance.voice = englishVoice;
                
                // Visual feedback
                cardMessage.classList.add('speaking');
                utterance.onend = () => cardMessage.classList.remove('speaking');
                utterance.onerror = (e) => {
                    console.error('Speech error:', e);
                    cardMessage.classList.remove('speaking');
                };
                
                window.speechSynthesis.speak(utterance);
                currentSpeech = utterance;
                return;
            }
            
            // Fallback to backend TTS
            if (data?.tts_audio) {
                ttsPlayer.src = data.tts_audio;
                await ttsPlayer.play();
                return;
            }
            
            console.log("No TTS method available");
        } catch (error) {
            console.error('TTS failed:', error);
        }
    }

    function stopCurrentSpeech() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        if (ttsPlayer) {
            ttsPlayer.pause();
            ttsPlayer.currentTime = 0;
        }
        cardMessage?.classList.remove('speaking');
        currentSpeech = null;
    }

    async function loadVoices() {
        return new Promise(resolve => {
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0) return resolve(voices);
            
            window.speechSynthesis.onvoiceschanged = () => {
                resolve(window.speechSynthesis.getVoices());
            };
        });
    }

    // Helper functions
    function setColorScheme(verdict) {
        const colors = verdict === 'strong' ? {
            primary: '#2c5e8a', secondary: '#448a5a', accent: '#37a2d4'
        } : {
            primary: '#8a2c2c', secondary: '#8a5a44', accent: '#d46b37'
        };
        
        document.documentElement.style.setProperty('--primary', colors.primary);
        document.documentElement.style.setProperty('--secondary', colors.secondary);
        document.documentElement.style.setProperty('--accent', colors.accent);
    }

    function resetDisplay() {
        stopCurrentSpeech();
        document.querySelector('.card-placeholder').classList.remove('hidden');
        tarotCard.classList.add('hidden');
        document.getElementById('suggestions').classList.add('hidden');
        document.getElementById('validationDetails').classList.add('hidden');
        
       
        document.documentElement.style.setProperty('--primary', '#4a2c82');
        document.documentElement.style.setProperty('--secondary', '#8a5a44');
        document.documentElement.style.setProperty('--accent', '#d4af37');
    }

    function showError(message) {
        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.textContent = message;
        document.body.appendChild(errorEl);
        setTimeout(() => errorEl.remove(), 3000);
    }
});