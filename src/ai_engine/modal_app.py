import modal
import subprocess
import time
import urllib.request
import urllib.error

# We need vllm to serve the Qwen3-8B embeddings, and contrastive-lm for the System One heads
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm", "contrastive-lm", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"}) # Fast downloads
)

def download_model_weights():
    from huggingface_hub import snapshot_download
    print("Downloading Qwen3-8B backbone...")
    snapshot_download("Qwen/Qwen3-8B")
    print("Downloading CLM-v0.1-8B heads...")
    snapshot_download("Contrastive-LM/CLM-v0.1-8B")

image = image.run_function(download_model_weights)

app = modal.App("clm-macro-engine")

@app.function(
    gpu="A10G", 
    image=image, 
    min_containers=0,
    scaledown_window=120,
    timeout=3600
)
@modal.asgi_app()
def clm_server():
    """
    Mounts the official CLM ASGI app natively inside Modal to bypass TCP proxy deadlocks.
    """
    import subprocess, time, urllib.request, urllib.error
    
    print("Starting vLLM Embedding Backbone...")
    vllm_process = subprocess.Popen([
        "vllm", "serve", "Qwen/Qwen3-8B", 
        "--served-model-name", "qwen3-8b", 
        "--runner", "pooling", 
        "--max-model-len", "2048", 
        "--port", "8090",
        "--enforce-eager", "--gpu-memory-utilization", "0.9"
    ])
    
    # Wait until vLLM is healthy
    print("Waiting for vLLM to spin up (this takes ~30 seconds)...")
    while True:
        try:
            req = urllib.request.Request("http://127.0.0.1:8090/health")
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    break
        except urllib.error.URLError:
            pass
        time.sleep(2)
        
    print("vLLM is ready! Loading CLM Engine...")
    
    from clm.server import create_app, download
    from clm import Engine
    from clm.embedder import Embedder
    
    # Download the default Jev model weights if not present
    ckpt = download()
    
    # Initialize the embedder (pointing to our local vLLM instance)
    embedder = Embedder("http://127.0.0.1:8090/v1/embeddings", "qwen3-8b", max_tokens=2048)
    
    # Initialize the Engine
    engine = Engine(embedder, checkpoint=ckpt, device="cuda")
    
    # Create the official FastAPI app and return it to Modal
    fastapi_app = create_app(engine, api_key=None, ui=False, cors=True)
    
    return fastapi_app
