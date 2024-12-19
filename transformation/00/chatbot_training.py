from pathlib import Path
import json
from typing import Dict, List, Tuple
from collections import defaultdict
import logging
import pdb

class DexterDialogueProcessor:
    def __init__(self, transcript_path: str = "data/dexter_transcripts.json"):
        self.transcript_path = Path(transcript_path)
        self.dexter_dialogues: List[Dict] = []
        self.context_windows: List[Tuple[List[str], str]] = []
        self.training_pairs: List[Dict] = []
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/dialogue_processor.log'),
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
        """Extract dialogue pairs where Dexter responds to someone."""
        dexter_dialogues = []
        
        for episode_obj in self.transcript_obj['episodes']:
            dialogue = episode_obj['dialogue']
            
            
            for i in range(len(dialogue)-1):
                current = dialogue[i] 
                next_line = dialogue[i+1]
            
                if (
                    'speaker' not in current 
                    or 'text' not in current
                    or current['speaker'] is None
                    or current['text'] is None
                    or not current['speaker'].strip()
                    or not current['text'].strip()
                ): continue
                
                if current['speaker'].upper() != 'DEXTER' and next_line['speaker'].upper() == 'DEXTER':
                    # pdb.set_trace()
                    processed_dialogue_obj = {
                        'user_message': current['text'],
                        'dexter_response': next_line['text'],
                        'episode_title': episode_obj['title'],
                        'line_number': next_line['line_number']
                    }
                    dexter_dialogues.append(processed_dialogue_obj)
        
        self.dexter_dialogues = dexter_dialogues
        return dexter_dialogues
  
    def create_training_pairs(self) -> List[Dict]:
        """Create input/output pairs for training."""
        training_pairs = []
        
        for dialogue_obj in self.dexter_dialogues:
            # Remove speaker tags from any input text
            # pdb.set_trace()
            input_text = dialogue_obj['dexter_response']
            if ':' in input_text:
                input_text = input_text.split(':', 1)[1].strip()

            training_pair_obj = {
                'input': input_text,
                'output': dialogue_obj['dexter_response'],
                'metadata': {
                    'episode': dialogue_obj['episode_title'],
                    'line_number': dialogue_obj['line_number']
                }
            }
            
            training_pairs.append(training_pair_obj)
        self.training_pairs = training_pairs
        return training_pairs
    
    def get_stats(self) -> Dict:
        """Get basic statistics about the processed data."""
        if not self.dexter_dialogues:
            return {}

        stats_obj = {
            'total_dialogues': len(self.dexter_dialogues),
            'avg_dialogue_length': sum(len(d['dexter_response'].split()) for d in self.dexter_dialogues) / len(self.dexter_dialogues),
            'unique_episodes': len(set(d['episode_title'] for d in self.dexter_dialogues)),
            'dialogues_with_context': sum(1 for d in self.dexter_dialogues if d['user_message'])
        }
        
        return stats_obj
    
    def create_training_samples(self) -> List[Dict]:
        """Format chat pairs for model training."""
        training_samples = []
        
        for pair in self.training_pairs:
            # Simple input/output format for chatbot
            sample = {
                'input': pair['input'],
                'output': pair['output'],
                'metadata': pair['metadata']
            }
            training_samples.append(sample)
        
        return training_samples
    
    def save_training_data(self, output_path: str = "data/chatbot_training_data.json") -> None:
        """Save processed training pairs to JSON."""
        training_pairs = self.create_training_pairs()
        training_samples = self.create_training_samples()

        stats_obj = self.get_stats()
        
        output_obj = {
            'metadata': {
                'stats': stats_obj,
                'source': str(self.transcript_path)
            },
            'training_pairs': training_pairs,
            'samples': training_samples
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