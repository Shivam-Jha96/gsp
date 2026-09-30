import os
import json
import torch
import spaces
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer

# Target the specific Contrastive-LM/CLM-8B model as requested!
MODEL_ID = os.environ.get("MODEL_ID", "Contrastive-LM/CLM-8B")

print(f"Loading {MODEL_ID} into memory...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, 
    torch_dtype=torch.float16,
    device_map="auto"
)
print("Model loaded successfully!")

@spaces.GPU(duration=15)
def score_sentiment(text: str, region_context: str) -> str:
    """
    Deterministic System-One scoring based on text and regional OKF context.
    Decorated with @spaces.GPU to dynamically request A100 access on Hugging Face.
    """
    prompt = f"""You are a System-One financial analyst. Analyze the following text based on the provided regional macro rules.
    
Regional Context (OKF Rules):
{region_context}

Text to analyze:
{text}

Output exactly in the following format:
Choice: [Bullish/Bearish/Neutral]
Score: [Confidence score from 0.0 to 1.0]
Noul: [Brief explanation of reasoning]
"""
    
    # Move inputs to CUDA device dynamically allocated by ZeroGPU
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.0, # Ensures deterministic System-One output
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    
    # Parse the output format into our strict JSON structure
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
            
    payload = {
        "Choice": choice,
        "Score": score,
        "Noul": noul
    }
    
    # Gradio API endpoints must return a string (JSON) to the client
    return json.dumps(payload)

# Wrap the function in a Gradio Interface so Hugging Face can host it as an API
demo = gr.Interface(
    fn=score_sentiment,
    inputs=[
        gr.Textbox(label="Headline/Text"),
        gr.Textbox(label="Regional OKF Rules")
    ],
    outputs=gr.Textbox(label="JSON Result"),
    title="CLM-8B Macro-Sentiment Inference Engine",
    description="System-One API for scoring macro-financial news events based on Contrastive-LM."
)

if __name__ == "__main__":
    demo.launch()
