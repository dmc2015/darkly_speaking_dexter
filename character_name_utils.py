from typing import Dict, Optional

class CharacterNormalizer:
    """Handles normalization of character names and their variants."""
    
    def __init__(self):
        self.name_mappings = {
            "DEX": "DEXTER",
            "DEXTER MORGAN": "DEXTER",
            "DEB": "DEBRA",
            "DEBRA MORGAN": "DEBRA",
            "ANGEL": "BATISTA",
            "ANGEL BATISTA": "BATISTA",
            "LAGUERTA": "MARIA LAGUERTA",
            "MARIA": "MARIA LAGUERTA",
            "DOAKES": "JAMES DOAKES",
            "SGT DOAKES": "JAMES DOAKES",
            "SERGEANT DOAKES": "JAMES DOAKES",
            "RITA BENNETT": "RITA",
            "RITA MORGAN": "RITA"
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