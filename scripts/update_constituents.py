import os
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"

# Mapping to the free open-source repository yfiua/index-constituents
# Format: https://yfiua.github.io/index-constituents/constituents-{code}.json
YFIUA_ENDPOINTS = {
    "S&P 500": "sp500",
    "NASDAQ": "nasdaq100",
    "Dow Jones": "dowjones",
    "FTSE 100": "ftse100",
    "Nikkei 225": "nikkei225"
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

def fetch_from_yfiua(index_name: str) -> list:
    code = YFIUA_ENDPOINTS.get(index_name)
    if not code:
        logging.warning(f"No yfiua endpoint mapped for {index_name}")
        return []
        
    url = f"https://yfiua.github.io/index-constituents/constituents-{code}.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Failed to fetch {index_name} from {url}: {e}")
        return []
    
    constituents = []
    for item in data:
        # yfiua JSON structure often varies but typically has Symbol and Name
        symbol = item.get("Symbol", item.get("symbol"))
        name = item.get("Name", item.get("name", item.get("Company", "")))
        
        if not symbol or not name:
            continue
            
        aliases = [name.lower()]
        if symbol.lower() not in aliases:
            aliases.append(symbol.lower())
            
        constituents.append({
            "symbol": symbol,
            "name": name,
            "aliases": aliases
        })
    return constituents

def update_region_file(region_file: Path):
    logging.info(f"Processing {region_file.name}")
    data = load_local_constituents(region_file)
    if not data or "indices" not in data:
        logging.error(f"Invalid or missing constituents data in {region_file.name}")
        return

    updated_indices = {}
    for index_name, current_list in data["indices"].items():
        logging.info(f"  Fetching updates for {index_name}...")
        
        # Try fetching from free repository
        new_list = fetch_from_yfiua(index_name)
        
        if new_list:
            existing_map = {c["symbol"]: c for c in current_list}
            merged_list = []
            
            for new_c in new_list:
                symbol = new_c["symbol"]
                if symbol in existing_map:
                    new_c["aliases"] = existing_map[symbol].get("aliases", new_c["aliases"])
                merged_list.append(new_c)
                
            updated_indices[index_name] = merged_list
            logging.info(f"    -> Updated {index_name} with {len(merged_list)} constituents.")
        else:
            updated_indices[index_name] = current_list
            logging.info(f"    -> Kept existing {len(current_list)} constituents for {index_name}.")

    data["indices"] = updated_indices
    save_local_constituents(region_file, data)
    logging.info(f"Saved {region_file.name}")

def main():
    # Fallback to keyless open-source due to FMP free-tier 403 Forbidden limits
    logging.info("Starting index constituents update using yfiua open-source project...")
    for file_path in KNOWLEDGE_DIR.glob("*_constituents.okf.json"):
        try:
            update_region_file(file_path)
        except Exception as e:
            logging.error(f"Failed to update {file_path.name}: {e}")

if __name__ == "__main__":
    main()
