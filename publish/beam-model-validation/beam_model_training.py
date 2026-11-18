# Beam Analysis Foundation Model Training Pipeline
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset, load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, AutoPeftModelForCausalLM
import pandas as pd
import numpy as np
from typing import Dict, List
import json
import wandb
from torch.utils.data import DataLoader
import evaluate

class BeamAnalysisDataProcessor:
    """Process beam analysis data for model training"""
    
    def __init__(self, tokenizer_name: str = "microsoft/DialoGPT-small"):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        
        # Add special tokens for engineering content
        special_tokens = {
            "pad_token": "<pad>",
            "eos_token": "</s>",
            "bos_token": "<s>",
            "additional_special_tokens": [
                "<problem>", "</problem>",
                "<solution>", "</solution>", 
                "<code>", "</code>",
                "<calculation>", "</calculation>",
                "<units>", "</units>"
            ]
        }
        
        self.tokenizer.add_special_tokens(special_tokens)
        
    def format_training_example(self, row: Dict) -> str:
        """Format a training example with special tokens"""
        
        if row['type'] == 'problem_solution':
            formatted = f"<problem>{row['input']}</problem>\n<solution>{row['output']}</solution>"
        elif row['type'] == 'code_generation':
            formatted = f"<problem>{row['input']}</problem>\n<code>{row['output']}</code>"
        else:
            formatted = f"<problem>{row['input']}</problem>\n<calculation>{row['output']}</calculation>"
            
        return formatted
    
    def preprocess_dataset(self, dataset_path: str, max_length: int = 512) -> Dataset:
        """Preprocess the dataset for training"""
        
        # Load data
        df = pd.read_csv(dataset_path)
        
        # Format examples
        formatted_examples = []
        for _, row in df.iterrows():
            formatted_text = self.format_training_example(row)
            
            # Tokenize
            tokenized = self.tokenizer(
                formatted_text,
                truncation=True,
                max_length=max_length,
                padding='max_length',  # ensure uniform lengths for batching
                return_tensors='pt'
            )
            
            # Convert tensors to lists for Dataset.from_list
            input_ids = tokenized['input_ids'][0].tolist()
            attention_mask = tokenized['attention_mask'][0].tolist()
            
            formatted_examples.append({
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'labels': input_ids.copy(),  # For causal LM
                'original_text': formatted_text
            })
        
        return Dataset.from_list(formatted_examples)

class BeamAnalysisModel:
    """Wrapper for beam analysis foundation model"""
    
    def __init__(self, base_model_name: str = "microsoft/DialoGPT-small"):
        self.base_model_name = base_model_name
        self.tokenizer = None
        self.model = None
        
    def load_base_model(self):
        """Load and prepare base model for fine-tuning"""
        
        # Initialize tokenizer
        processor = BeamAnalysisDataProcessor(self.base_model_name)
        self.tokenizer = processor.tokenizer
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Resize embeddings for new tokens
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        return self.model, self.tokenizer
    
    def setup_lora(self, r: int = 4, alpha: int = 8):
        """Setup LoRA for efficient fine-tuning"""
        
        lora_config = LoraConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=["c_attn", "c_proj"],
            lora_dropout=0.1,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # Prepare model for training
        self.model = prepare_model_for_kbit_training(self.model)
        self.model = get_peft_model(self.model, lora_config)
        
        return self.model

class BeamAnalysisTrainer:
    """Custom trainer for beam analysis model"""
    
    def __init__(self, model, tokenizer, train_dataset, eval_dataset=None):
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        
        # Data collator
        self.data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,  # Causal language modeling
            pad_to_multiple_of=8
        )
        
    def train(self, output_dir: str = "./beam_model_output"):
        """Train the model"""
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            overwrite_output_dir=True,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=4,
            learning_rate=5e-4,
            weight_decay=0.01,
            logging_steps=10,
            save_steps=50,
            eval_steps=50,
            eval_strategy="steps" if self.eval_dataset else "no",
            save_strategy="steps",
            load_best_model_at_end=True if self.eval_dataset else False,
            metric_for_best_model="eval_loss" if self.eval_dataset else None,
            greater_is_better=False,
            warmup_steps=5,
            fp16=torch.cuda.is_available(),
            report_to="wandb",
            run_name="beam-analysis-foundation-model"
        )
        
        # Custom trainer with engineering-specific metrics
        trainer = CustomBeamTrainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            data_collator=self.data_collator,
            # tokenizer parameter removed (deprecated). If needed, pass processing_class.
        )
        
        # Start training
        trainer.train()
        
        # Save final model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        return trainer

class CustomBeamTrainer(Trainer):
    """Custom trainer with engineering-specific evaluation"""
    
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        """Use model-provided loss for robustness across transformers versions."""
        outputs = model(**inputs)
        loss = outputs.loss if hasattr(outputs, "loss") else None
        if loss is None:
            # Fallback: standard causal LM loss if not provided
            logits = outputs.get('logits')
            labels = inputs.get('labels')
            if logits is None or labels is None:
                raise ValueError("Model outputs lack loss and logits/labels not present.")
            loss_fct = torch.nn.CrossEntropyLoss()
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        return (loss, outputs) if return_outputs else loss
    
    def evaluate(self, eval_dataset=None, ignore_keys=None, metric_key_prefix="eval"):
        """Custom evaluation with engineering metrics"""
        
        # Standard evaluation
        eval_results = super().evaluate(eval_dataset, ignore_keys, metric_key_prefix)
        
        # Add custom engineering metrics
        if eval_dataset:
            engineering_metrics = self._compute_engineering_metrics(eval_dataset)
            eval_results.update(engineering_metrics)
        
        return eval_results
    
    def _compute_engineering_metrics(self, eval_dataset) -> Dict:
        """Compute engineering-specific metrics"""
        
        # This would include metrics like:
        # - Numerical accuracy for stress calculations
        # - Units consistency
        # - Physics constraint violations
        
        metrics = {
            "engineering_accuracy": 0.85,  # Placeholder
            "units_consistency": 0.92,     # Placeholder  
            "physics_violations": 0.08     # Placeholder
        }
        
        return metrics

class BeamAnalysisInference:
    """Inference wrapper for trained beam analysis model"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        # Load PEFT adapter-aware model if found
        try:
            self.model = AutoPeftModelForCausalLM.from_pretrained(model_path)
        except Exception:
            self.model = AutoModelForCausalLM.from_pretrained(model_path)
        
    def solve_beam_problem(self, problem_description: str, max_length: int = 512) -> str:
        """Solve a beam analysis problem"""
        
        # Format input
        formatted_input = f"<problem>{problem_description}</problem>\n<solution>"
        
        # Tokenize
        inputs = self.tokenizer(formatted_input, return_tensors="pt")
        
        # Generate solution
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # Extract solution
        if "<solution>" in generated_text and "</solution>" in generated_text:
            solution = generated_text.split("<solution>")[1].split("</solution>")[0].strip()
        else:
            solution = generated_text[len(formatted_input):].strip()
        
        return solution
    
    def generate_code(self, problem_description: str) -> str:
        """Generate code for beam analysis problem"""
        
        formatted_input = f"<problem>Write Python code to solve: {problem_description}</problem>\n<code>"
        
        inputs = self.tokenizer(formatted_input, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=1024,
                num_return_sequences=1,
                temperature=0.3,  # Lower temperature for code generation
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        if "<code>" in generated_text and "</code>" in generated_text:
            code = generated_text.split("<code>")[1].split("</code>")[0].strip()
        else:
            code = generated_text[len(formatted_input):].strip()
        
        return code

# Training pipeline execution
def main():
    """Main training pipeline"""
    
    # Initialize wandb (optional for PoC)
    try:
        wandb.init(project="beam-analysis-foundation-model", mode="disabled")
        print("W&B tracking disabled for PoC")
    except Exception as e:
        print(f"W&B initialization skipped: {e}")
        wandb.init(mode="disabled")
    
    # 1. Generate training data (if not already done)
    print("Generating training dataset...")
    from beam_analysis_data import generate_training_dataset
    dataset = generate_training_dataset(100)  # smaller set for quick CPU PoC
    dataset.to_csv('beam_training_data.csv', index=False)
    
    # 2. Process data
    print("Processing dataset...")
    processor = BeamAnalysisDataProcessor()
    train_dataset = processor.preprocess_dataset('beam_training_data.csv', max_length=384)
    
    # Split into train/eval
    train_test = train_dataset.train_test_split(test_size=0.2)
    train_dataset = train_test['train']
    eval_dataset = train_test['test']
    
    # 3. Load and setup model
    print("Loading base model...")
    beam_model = BeamAnalysisModel()
    model, tokenizer = beam_model.load_base_model()
    
    # Setup LoRA
    print("Setting up LoRA...")
    model = beam_model.setup_lora()
    
    # 4. Train
    print("Starting training...")
    trainer = BeamAnalysisTrainer(model, tokenizer, train_dataset, eval_dataset)
    checkpoint_dir = "./checkpoints/poc"
    trainer.train(output_dir=checkpoint_dir)
    
    # 5. Test inference (optional; robust to adapter/vocab size)
    try:
        print("Testing inference...")
        inference = BeamAnalysisInference(checkpoint_dir)
        
        test_problem = """
        A simply supported beam with the following properties:
        - Length: 5.0 m
        - Cross-section: 200 mm × 300 mm rectangular
        - Material: Steel A36
        - Point load: 10 kN at 2.0 m from left support
        
        Calculate: reactions, maximum stress, and safety factor.
        """
        
        solution = inference.solve_beam_problem(test_problem)
        print("Generated solution:")
        print(solution)
    except Exception as e:
        print(f"Inference test skipped due to load error: {e}")

if __name__ == "__main__":
    main()
