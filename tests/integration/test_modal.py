import modal
image = modal.Image.debian_slim(python_version="3.11").pip_install("contrastive-lm")
app = modal.App("test-clm")
@app.function(image=image)
def test():
    import clm
    print("ENGINE DIR:", dir(clm.Engine))
    print("CLM DIR:", dir(clm))
