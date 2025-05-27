
"""
Script to download Llama models to a specific folder
"""
import os
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM

def download_model(model_name, output_dir):
    """
    Download the model and tokenizer to a specific directory
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Downloading tokenizer for {model_name} to {output_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.save_pretrained(output_dir)
    print(f"Tokenizer saved to {output_dir}")
    
    print(f"Downloading model {model_name} to {output_dir}...")
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")
    
    print(f"Model and tokenizer successfully downloaded to {output_dir}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Llama model to a specific folder")
    parser.add_argument("--model_name", type=str, default="huihui-ai/Qwen3-8B-abliterated",
                        help="Hugging Face model name to download")
    parser.add_argument("--output_dir", type=str, default="./models",
                        help="Directory to save the model and tokenizer")
    
    args = parser.parse_args()
    download_model(args.model_name, args.output_dir)
