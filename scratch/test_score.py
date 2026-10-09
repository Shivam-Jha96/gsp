import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from ai_engine.clm_client import CLMClient
from main import score_sentiment

clm_api_key = os.environ.get('CLM_API_KEY') or os.environ.get('TYPESAFE_API_KEY', 'empty_key_allowed')
client = CLMClient(
    api_key=clm_api_key.strip(),
    base_url='https://shivam-jha96--clm-macro-engine-clm-server.modal.run',
    model='clm-latest',
    timeout=120.0
)

texts = [
    "Dow Jones Futures: Nasdaq Hits High As Nvidia, SpaceX, Bloom Energy Flash Buy Signals. What To Do Now.",
    "Stock Market Today: Nasdaq closes just below a record, Dow and S&P 500 also rally after soft jobs data, even as bond yields rise",
    "Stock market today: Dow, S&P 500, Nasdaq rally as Fed rate-hike expectations fade, tech gains"
]

for t in texts:
    from main import load_okf_rules
    context = load_okf_rules("US")
    res = score_sentiment(client, t, context, region_tag="US", asset_class="equity")
    print(json.dumps(res, indent=2))
