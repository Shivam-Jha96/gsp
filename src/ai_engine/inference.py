import os
import torch
import spaces
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = os.environ.get("MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct")

# Initialize globally for ZeroGPU compatibility
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float16)

@spaces.GPU
def score_sentiment(text: str, region_context: str) -> dict:
    """
    Deterministic System-One scoring based on text and regional OKF context.
    Utilizes ZeroGPU for execution.
    
    Returns format: Choice (Bullish/Bearish/Neutral), Score (0.0-1.0), Noul (Explanation)
    """
    prompt = f"""You are an AI financial analyst. Analyze the following text based on the provided regional macro rules.
    
Regional Context (OKF Rules):
{region_context}

Text to analyze:
{text}

Output exactly in the following format:
Choice: [Bullish/Bearish/Neutral]
Score: [Confidence score from 0.0 to 1.0]
Noul: [Brief explanation of reasoning]
"""
    
    # Move inputs to CUDA device allocated by ZeroGPU
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.0, # Ensures deterministic output
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    
    # Parse the output format: Choice, Score, Noul
    choice = "Neutral"
    score = 0.5
    noul = "Could not parse response."
    
    for line in response.strip().split('\n'):
        line = line.strip()
        if line.startswith("Choice:"):
            choice = line.replace("Choice:", "").strip()
        elif line.startswith("Score:"):
            try:
                score = float(line.replace("Score:", "").strip())
            except ValueError:
                pass
        elif line.startswith("Noul:"):
            noul = line.replace("Noul:", "").strip()
            
    return {
        "Choice": choice,
        "Score": score,
        "Noul": noul
    }
