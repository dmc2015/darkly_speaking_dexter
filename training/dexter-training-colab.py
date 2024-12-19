# Title: Dexter GPT-2 Training

# Install required packages
!pip install torch transformers datasets

# Verify GPU is available
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

# Load and prep data
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import json

# Load tokenizer
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
tokenizer.pad_token = tokenizer.eos_token

# Load model
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Upload and load your data
# TODO: Upload gpt2_training_data.json to Colab first
with open('gpt2_training_data.json', 'r') as f:
    training_data = json.load(f)

# Save formatted texts to a file for dataset creation
with open('train.txt', 'w') as f:
    for text in training_data['formatted_texts']:
        f.write(text + '\n')

# Create dataset
def load_dataset(train_path, tokenizer):
    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=train_path,
        block_size=128
    )
    return dataset

train_dataset = load_dataset('train.txt', tokenizer)

# Create data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# Set training arguments
training_args = TrainingArguments(
    output_dir="./dexter-gpt2",
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    save_steps=500,
    save_total_limit=2,
)

# Initialize trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
)

# Train model
trainer.train()

# Save the model
trainer.save_model()

# Test generation
def generate_response(context, model, tokenizer):
    input_text = f"Context: {context} Response:"
    inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(
        inputs['input_ids'],
        max_length=100,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Test with a sample context
test_context = "DEBRA: What are you thinking about?"
response = generate_response(test_context, model, tokenizer)
print(f"Context: {test_context}")
print(f"Generated: {response}")
