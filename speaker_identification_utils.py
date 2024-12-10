import nltk
from nltk.corpus import wordnet as wn
import logging
from typing import Set, Optional
from pathlib import Path

class SpeakerIdentifier:
    def __init__(self, custom_words: Optional[Set[str]] = None):
        self.logger = logging.getLogger(__name__)
        self._ensure_nltk_downloads()
        self.non_speaker_words = self._initialize_non_speaker_words()
        
        # Add any custom words provided
        if custom_words:
            self.add_non_speaker_words(custom_words)
    
    def _ensure_nltk_downloads(self) -> None:
        """Ensure required NLTK data is downloaded."""
        nltk_data_dir = Path(nltk.data.find('.')).parent
        required_data = {
            'wordnet': 'corpora/wordnet.zip',
            'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger.zip'
        }
        
        for data_name, data_path in required_data.items():
            try:
                # Check if the data exists
                path = nltk_data_dir / data_path
                if not path.exists():
                    self.logger.info(f"Downloading required NLTK data: {data_name}")
                    nltk.download(data_name, quiet=True)
            except Exception as e:
                self.logger.error(f"Failed to download NLTK data {data_name}: {e}")
                raise RuntimeError(f"Failed to initialize NLTK data: {e}")
    
    def _initialize_non_speaker_words(self) -> Set[str]:
        """Initialize and cache the set of non-speaker words."""
        try:
            # Generate comprehensive lists using WordNet
            action_words = {word.lower() for synset in wn.all_synsets('v') 
                          for word in synset.lemma_names()}
            adjectives = {word.lower() for synset in wn.all_synsets('a') 
                        for word in synset.lemma_names()}
            sounds = {word.lower() for synset in wn.synsets('sound', 'n') 
                    for word in synset.lemma_names()}
            
            # Common transcript-specific words to filter
            transcript_specific = {
                'music', 'rings', 'click', 'phone', 'opens', 'closes',
                'background', 'dramatic', 'suspenseful', 'intense',
                'footsteps', 'silence', 'quietly', 'loudly', 'softly',
                'door', 'window', 'creaking', 'squeaking', 'banging',
                'buzzing', 'ringing', 'beeping', 'static', 'ambient'
            }
            
            return action_words | adjectives | sounds | transcript_specific
            
        except Exception as e:
            self.logger.error(f"Failed to initialize word lists: {e}")
            raise RuntimeError(f"Failed to initialize word lists: {e}")
    
    def add_non_speaker_words(self, words: Set[str]) -> None:
        """Add custom words to the non-speaker word set."""
        self.non_speaker_words.update(word.lower() for word in words)
        self.logger.info(f"Added {len(words)} custom non-speaker words")
    
    def is_likely_speaker(self, text: str) -> bool:
        """
        Check if the given text is likely to be a speaker name.
        
        Args:
            text (str): Text to check (without brackets)
            
        Returns:
            bool: True if the text likely represents a speaker
        """
        words = text.lower().split()
        return not any(word in self.non_speaker_words for word in words)
    
    def get_non_speaker_words(self) -> Set[str]:
        """Get the current set of non-speaker words."""
        return self.non_speaker_words.copy()

    def process_bracketed_text(self, text: str) -> tuple[Optional[str], str]:
        """
        Process text that appears in brackets to determine if it's a speaker.
        
        Args:
            text (str): Full text including brackets and any following text
            
        Returns:
            tuple[Optional[str], str]: (speaker name if found, remaining text)
                                     (None, original text) if not a speaker
        """
        # Strip brackets and split into potential speaker and remaining text
        parts = text.split(']', 1)
        if len(parts) != 2:
            return None, text
            
        potential_speaker = parts[0].strip('[').strip()
        remaining_text = parts[1].strip()
        
        if self.is_likely_speaker(potential_speaker):
            return potential_speaker, remaining_text
        else:
            # Return the original text to be handled as context
            return None, text

# Example usage:
if __name__ == "__main__":
    # Setup logging for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    # Example custom words
    custom_non_speakers = {'whispering', 'echoing', 'reverberating'}
    
    # Initialize the identifier
    identifier = SpeakerIdentifier(custom_words=custom_non_speakers)
    
    # Test cases
    test_cases = [
        "[DEXTER]",
        "[Heavy Breathing]",
        "[Door Opens]",
        "[Rita]",
        "[Grunts]",
        "[Laughing]"
    ]
    
    for test in test_cases:
        speaker, remaining = identifier.process_bracketed_text(test)
        if speaker:
            print(f"{test} -> Speaker: {speaker}")
        else:
            print(f"{test} -> Context/Action")