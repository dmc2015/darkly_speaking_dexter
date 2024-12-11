# THIS FILE CAN NOT BE FULLY IMPLEMENTED IT MUST BE IMPLMENENTED PARTIALLY, SLOWLY AT A TIME 
# SO IT IS EASIER TO DEBUG

import logging
from typing import Set, Optional, Tuple

class SpeakerIdentifier:
    def __init__(self, custom_words: Optional[Set[str]] = None):
        self.logger = logging.getLogger(__name__)
        
        # Common transcript verbs that indicate actions/sounds
        self.action_verbs = {
            'grunting', 'groaning', 'breathing', 'gasping', 'sighing',
            'coughing', 'laughing', 'crying', 'whispering', 'muttering',
            'yelling', 'screaming', 'shouting', 'snoring', 'whistling',
            'humming', 'singing', 'speaking', 'talking', 'sniffing',
            'walking', 'running', 'moving', 'standing', 'sitting',
            'opening', 'closing', 'hitting', 'knocking', 'ringing'
        }
        
        # Common transcript adjectives that describe sounds/actions
        self.descriptive_words = {
            'muffled', 'heavy', 'soft', 'loud', 'quick', 'slow',
            'deep', 'sharp', 'faint', 'distant', 'nearby',
            'continuous', 'repeated', 'sudden', 'gentle', 'quiet',
            'noisy', 'dramatic', 'tense', 'nervous', 'angry',
            'happy', 'sad', 'excited', 'worried', 'concerned'
        }
        
        # Sound effects and non-character markers
        self.sound_effects = {
            'music', 'sound', 'noise', 'static', 'silence',
            'footsteps', 'door', 'phone', 'bell', 'alarm',
            'click', 'beep', 'buzz', 'ring', 'thud',
            'crash', 'bang', 'splash', 'rustle', 'creak'
        }

        # Combine all non-speaker words
        self.non_speaker_words = self.action_verbs | self.descriptive_words | self.sound_effects

        # Add any custom words provided
        if custom_words:
            self.add_non_speaker_words(custom_words)

    def add_non_speaker_words(self, words: Set[str]) -> None:
        """Add custom words to the non-speaker word set."""
        self.non_speaker_words.update(word.lower() for word in words)
    
    def is_likely_speaker(self, text: str) -> bool:
        """Check if text is likely a speaker name rather than action/sound."""
        words = text.lower().split()
        return not any(word in self.non_speaker_words for word in words)

    def process_bracketed_text(self, text: str) -> Tuple[Optional[str], str]:
        """Process text in brackets to determine if it's a speaker."""
        parts = text.split(']', 1)
        if len(parts) != 2:
            return None, text
            
        potential_speaker = parts[0].strip('[').strip()
        remaining_text = parts[1].strip()
        
        if self.is_likely_speaker(potential_speaker):
            return potential_speaker, remaining_text
        else:
            return None, text