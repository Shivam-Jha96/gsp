import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from ai_engine.clm_client import CLMClient, Choice

clm_api_key = os.environ.get('CLM_API_KEY') or os.environ.get('TYPESAFE_API_KEY', 'empty_key_allowed')
client = CLMClient(
    api_key=clm_api_key.strip(),
    base_url='https://shivam-jha96--clm-macro-engine-clm-server.modal.run',
    model='clm-latest',
    timeout=120.0
)

text = "Dow Jones Futures: Nasdaq Hits High As Nvidia, SpaceX, Bloom Energy Flash Buy Signals. What To Do Now."
formatted_asset_class = "Equity"
region_tag = "US"
criteria = {
    "Bullish": "Equity market optimism: stock prices rising, benchmark index gains, market rally, positive corporate growth, expansion.",
    "Bearish": "Equity market pessimism: stock prices falling, benchmark index drops, market selloff, decline, warnings, downward pressure."
}

state_content = f"Target Financial News Event ({region_tag} Market - {formatted_asset_class} Asset Class):\n{text}"

result = client.system_one(
    state=state_content,
    questions={
        "direction": Choice(
            instructions=f"Directional sentiment of this financial news event concerning the {formatted_asset_class} market:",
            criteria=criteria
        )
    }
)

choice_obj = result.choices["direction"]
probs = choice_obj.probabilities or {}

print(json.dumps(probs, indent=2))
