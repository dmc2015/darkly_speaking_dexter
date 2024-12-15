from pathlib import Path
import json
from typing import Dict, List, Tuple
from collections import defaultdict
import logging

class DexterDialogueProcessor:
    def __init__(self, transcript_path: str = "dexter_transcripts.json"):
        self.transcript_path = Path(transcript_path)
        self.dexter_dialogues: List[Dict] = []
        self.context_windows: List[Tuple[List[str], str]] = []
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dialogue_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_transcripts(self) -> None:
        """Load and validate transcript data."""
        with open(self.transcript_path, 'r', encoding='utf-8') as f:
            transcript_obj = json.load(f)
            
        if not isinstance(transcript_obj, dict) or 'episodes' not in transcript_obj:
            raise ValueError("Invalid transcript format")
            
        self.transcript_obj = transcript_obj
    
    def extract_dexter_dialogue(self) -> List[Dict]:
        """Extract all of Dexter's dialogue entries with context."""
        dexter_dialogues = []
        
        for episode_obj in self.transcript_obj['episodes']:
            dialogue_context = []
            
            for dialogue_obj in episode_obj['dialogue']:
                try:
                    required_fields = ('speaker', 'text')
                    if (
                        'speaker' not in dialogue_obj 
                        or 'text' not in dialogue_obj
                        or dialogue_obj['speaker'] is None
                        or dialogue_obj['text'] is None
                        or not dialogue_obj['speaker'].strip()
                        or not dialogue_obj['text'].strip()
                    ):
                        continue
                                            
                    if dialogue_obj['speaker'].upper() == 'DEXTER':
                        try:
                            processed_dialogue_obj = {
                                'text': dialogue_obj['text'],
                                'episode_title': episode_obj['title'],
                                'line_number': dialogue_obj['line_number'],
                                'previous_context': dialogue_context[-3:],
                                'original_dialogue': dialogue_obj
                            }
                            dexter_dialogues.append(processed_dialogue_obj)
                        except KeyError as ke:
                            self.logger.error(f"Missing key in dialogue entry: {ke}")
                            self.logger.debug(f"Problematic dialogue: {dialogue_obj}")
                            continue
                        except Exception as e:
                            self.logger.error(f"Error processing Dexter dialogue: {str(e)}")
                            self.logger.debug(f"Problematic dialogue: {dialogue_obj}")
                            continue
                    
                    try:
                        context_obj = {
                            'speaker': dialogue_obj['speaker'],
                            'text': dialogue_obj['text']
                        }
                        dialogue_context.append(context_obj)
                    except KeyError as ke:
                        self.logger.error(f"Missing key while adding context: {ke}")
                        continue
                        
                except Exception as e:
                    self.logger.error(f"Error processing dialogue in episode {episode_obj.get('title', 'Unknown')}: {str(e)}")
                    continue
        
        self.dexter_dialogues = dexter_dialogues
        return dexter_dialogues
    
    def create_training_pairs(self) -> List[Dict]:
        """Create input/output pairs for training."""
        training_pairs = []
        
        for dialogue_obj in self.dexter_dialogues:
            context_text = ' '.join(
                f"{context_obj['speaker']}: {context_obj['text']}" 
                for context_obj in dialogue_obj['previous_context']
            )
            
            training_pair_obj = {
                'input': context_text,
                'output': dialogue_obj['text'],
                'metadata': {
                    'episode': dialogue_obj['episode_title'],
                    'line_number': dialogue_obj['line_number']
                }
            }
            
            training_pairs.append(training_pair_obj)
        
        return training_pairs
    
    def get_stats(self) -> Dict:
        """Get basic statistics about the processed data."""
        if not self.dexter_dialogues:
            return {}
            
        stats_obj = {
            'total_dialogues': len(self.dexter_dialogues),
            'avg_dialogue_length': sum(len(d['text'].split()) for d in self.dexter_dialogues) / len(self.dexter_dialogues),
            'unique_episodes': len(set(d['episode_title'] for d in self.dexter_dialogues)),
            'dialogues_with_context': sum(1 for d in self.dexter_dialogues if d['previous_context'])
        }
        
        return stats_obj
    
    def save_training_data(self, output_path: str = "chat_bot_training_data.json") -> None:
        """Save processed training pairs to JSON."""
        training_pairs = self.create_training_pairs()
        stats_obj = self.get_stats()
        
        output_obj = {
            'metadata': {
                'stats': stats_obj,
                'source': str(self.transcript_path)
            },
            'training_pairs': training_pairs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_obj, f, indent=2, ensure_ascii=False)

def main():
    processor = DexterDialogueProcessor()
    processor.load_transcripts()
    processor.extract_dexter_dialogue()
    processor.save_training_data()
    print(processor.get_stats())

if __name__ == "__main__":
    main()