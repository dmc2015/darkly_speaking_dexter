from pathlib import Path
import json
from typing import Dict, List
import logging
from transformers import GPT2Tokenizer
import pdb

class DexterGPT2Preprocessor:
    def __init__(self, training_data_path: str = "data/chatbot_training_data.json"):
        self.training_data_path = Path(training_data_path)
        self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_training_data(self) -> List[Dict]:
        """Load the chat training samples."""
        with open(self.training_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['samples']
  
    def _clean_text(self, text: str) -> str:
        """Clean text of speaker tags and artifacts."""
        import re
        
        # Remove speaker tags
        text = re.sub(r'[A-Z]+:\s*', '', text)
        
        # Remove special tokens
        text = re.sub(r'<\|.*?\|>', '', text)
        text = re.sub(r'\|\|.*?\|\|', '', text)
        
        # Remove formatting artifacts
        text = re.sub(r'\|\s*\|', '', text)
        text = re.sub(r'\s*\|\s*', ' ', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()

        
    # def format_for_gpt2(self, samples: List[Dict]) -> List[str]:
    #     """Convert chat samples into GPT2 format."""
    #     formatted_texts = []
    #     for sample in samples:
    #         # Simple format: "User: {input} Dexter: {output}<|endoftext|>"
    #         formatted_text = f"User: {sample['input']} Dexter: {sample['output']}{self.tokenizer.eos_token}"
    #         formatted_texts.append(formatted_text)
    #     return formatted_texts
    
    def format_for_gpt2(self, samples: List[Dict]) -> List[str]:
        """Convert chat samples into GPT2 format."""
        formatted_texts = []
        for sample in samples:
            # Remove speaker tags and simplify format
            clean_input = self._clean_text(sample['input'])
            clean_output = self._clean_text(sample['output'])
            # Use a simpler format without speaker tags
            formatted_text = f"Input: {clean_input} Output: {clean_output}{self.tokenizer.eos_token}"
            formatted_texts.append(formatted_text)
        return formatted_texts
    
    def save_formatted_data(self, formatted_texts: List[str], output_path: str = "data/gpt2_training_data.json"):
        """Save the formatted texts."""
        output_obj = {
            'formatted_texts': formatted_texts,
            'metadata': {
                'total_samples': len(formatted_texts),
                'tokenizer': 'gpt2'
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_obj, f, indent=2)
        
        self.logger.info(f"Saved {len(formatted_texts)} formatted samples to {output_path}")
    
    def process(self):
        """Run the full preprocessing pipeline."""
        samples = self.load_training_data()
        formatted_texts = self.format_for_gpt2(samples)
        self.save_formatted_data(formatted_texts)
        return formatted_texts

def main():
    preprocessor = DexterGPT2Preprocessor()
    preprocessor.process()

if __name__ == "__main__":
    main()