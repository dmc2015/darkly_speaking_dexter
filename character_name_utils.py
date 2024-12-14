from typing import Dict, Optional

class CharacterNormalizer:
    """Handles normalization of character names and their variants."""
    
    def __init__(self):
        self.name_mappings = {
            "DEXTER": "DEXTER",
            "DEX": "DEXTER",
            "DEXTER MORGAN": "DEXTER",
            "DEBRA": "DEBRA",
            "DEB": "DEBRA",
            "DEBRA MORGAN": "DEBRA",
            "BATISTA": "BATISTA",
            "ANGEL": "BATISTA",
            "ANGEL BATISTA": "BATISTA",
            "LAGUERTA":  "LAGUERTA",
            "LAGUERTA": "MARIA LAGUERTA",
            "MARIA": "MARIA LAGUERTA",
            "DOAKES":  "DOAKES",
            "DOAKES": "JAMES DOAKES",
            "SGT DOAKES": "JAMES DOAKES",
            "SERGEANT DOAKES": "JAMES DOAKES",
            "RITA": "RITA",
            "RITA BENNETT": "RITA",
            "RITA MORGAN": "RITA",
            "AUDREY": "AUDREY",
            "HARRISON": "HARRISON",
            "MOLLY": "MOLLY",
            "CHIEF ANGELA BISHOP": "CHIEF ANGELA BISHOP",
            "ANGELA": "CHIEF ANGELA BISHOP",
            "BISHOP":  "CHIEF ANGELA BISHOP",
            "CHIEF BISHOP": "CHIEF ANGELA BISHOP"
        }
        self.case_insensitive_mappings = {k.upper(): v for k, v in self.name_mappings.items()}
    
    def normalize(self, name: str) -> str:
        """Normalize a character name to its canonical form."""
        clean_name = name.strip().upper()
        return self.case_insensitive_mappings.get(clean_name, clean_name)
    
    def get_speaker_info(self, speaker: str) -> Dict[str, str]:
        """Get speaker information including normalization and dialogue type."""
        normalized_name = self.normalize(speaker)
        return {
            'original_name': speaker,
            'normalized_name': normalized_name,
            'type': 'voiceover' if any(vo in speaker.lower() 
                    for vo in ['voiceover', 'v.o.', '(vo)']) else 'spoken'
        }