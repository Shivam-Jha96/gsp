import modal
app = modal.App("test-clm")
@app.function(image=modal.Image.debian_slim(python_version="3.11").pip_install("contrastive-lm"))
def test():
    import clm.server, inspect
    print("SRC:", inspect.getsource(clm.server))
