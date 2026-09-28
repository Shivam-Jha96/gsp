import os
import json
import torch
import spaces
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer

# We use a smaller model for the MVP if Llama 3 requires approval
MODEL_ID = os.environ.get("MODEL_ID", "HuggingFaceTB/SmolLM-1.7B-Instruct")

print(f"Loading model: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float16)

@spaces.GPU
def predict_sentiment(text: str, region_context: str) -> str:
    prompt = f"""You are an AI financial analyst. Analyze the following text based on the provided regional macro rules.
    
Regional Context (OKF Rules):
{region_context}

Text to analyze:
{text}

Output exactly in the following JSON format:
{{"Choice": "Bullish/Bearish/Neutral", "Score": 0.0-1.0, "Noul": "Explanation"}}
"""
    
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    
    # Try to parse or force format
    try:
        # Simple extraction if it wrapped in markdown blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        json.loads(response) # validate
        return response
    except:
        # Fallback parsing
        return json.dumps({
            "Choice": "Neutral",
            "Score": 0.5,
            "Noul": f"Failed to parse model output: {response[:50]}..."
        })

# Create Gradio interface which automatically exposes an API endpoint (/api/predict)
iface = gr.Interface(
    fn=predict_sentiment,
    inputs=[gr.Textbox(label="Text"), gr.Textbox(label="Region Context")],
    outputs=gr.Textbox(label="JSON Result"),
    title="Global Macro-Sentiment API",
    description="API Microservice for scoring financial sentiment via ZeroGPU."
)

if __name__ == "__main__":
    iface.launch()
