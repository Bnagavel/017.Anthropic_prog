"""
Quick script to check DialoGPT model structure for LoRA targeting
"""
from transformers import AutoModelForCausalLM

def check_model_structure():
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
    
    print("Available modules in DialoGPT-small:")
    for name, module in model.named_modules():
        if 'attn' in name.lower() or 'proj' in name.lower() or 'linear' in name.lower():
            print(f"  {name}: {type(module).__name__}")
    
    print("\nAll module names:")
    for name, _ in model.named_modules():
        if len(name.split('.')) <= 3:  # Top-level modules only
            print(f"  {name}")

if __name__ == "__main__":
    check_model_structure()