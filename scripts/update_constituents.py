import os
import sys
import json
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"

# Common index mappings for Financial Modeling Prep (FMP)
FMP_ENDPOINTS = {
    "S&P 500": "sp500_constituent",
    "NASDAQ": "nasdaq_constituent",
    "Dow Jones": "dowjones_constituent"
}

def load_local_constituents(filepath: Path) -> dict:
    if not filepath.exists():
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_local_constituents(filepath: Path, data: dict):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write("\n")

def fetch_from_fmp(index_name: str, api_key: str) -> list:
    endpoint = FMP_ENDPOINTS.get(index_name)
    if not endpoint:
        logging.warning(f"No FMP endpoint mapped for {index_name}")
        return []
        
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}?apikey={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    constituents = []
    for item in data:
        symbol = item.get("symbol")
        name = item.get("name")
        if not symbol or not name:
            continue
            
        # Create a simple aliases list
        aliases = [name.lower()]
        if symbol.lower() not in aliases:
            aliases.append(symbol.lower())
            
        constituents.append({
            "symbol": symbol,
            "name": name,
            "aliases": aliases
        })
    return constituents

def update_region_file(region_file: Path, api_key: str):
    logging.info(f"Processing {region_file.name}")
    data = load_local_constituents(region_file)
    if not data or "indices" not in data:
        logging.error(f"Invalid or missing constituents data in {region_file.name}")
        return

    updated_indices = {}
    for index_name, current_list in data["indices"].items():
        logging.info(f"  Fetching updates for {index_name}...")
        
        # Try fetching from API
        new_list = fetch_from_fmp(index_name, api_key)
        
        if new_list:
            # Preserve existing aliases if symbol already existed
            existing_map = {c["symbol"]: c for c in current_list}
            merged_list = []
            
            for new_c in new_list:
                symbol = new_c["symbol"]
                if symbol in existing_map:
                    # Keep existing aliases to not break classifiers
                    new_c["aliases"] = existing_map[symbol].get("aliases", new_c["aliases"])
                merged_list.append(new_c)
                
            updated_indices[index_name] = merged_list
            logging.info(f"    -> Updated {index_name} with {len(merged_list)} constituents.")
        else:
            # Fallback to existing list if API fails or unsupported
            updated_indices[index_name] = current_list
            logging.info(f"    -> Kept existing {len(current_list)} constituents for {index_name}.")

    data["indices"] = updated_indices
    save_local_constituents(region_file, data)
    logging.info(f"Saved {region_file.name}")

def main():
    api_key = os.environ.get("MARKET_DATA_API_KEY")
    if not api_key:
        logging.error("MARKET_DATA_API_KEY environment variable is missing.")
        sys.exit(1)
        
    for file_path in KNOWLEDGE_DIR.glob("*_constituents.okf.json"):
        try:
            update_region_file(file_path, api_key)
        except Exception as e:
            logging.error(f"Failed to update {file_path.name}: {e}")

if __name__ == "__main__":
    main()
