import os
import re
import sys
import json
import argparse
import requests
from urllib.parse import quote
from tqdm import tqdm

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "output_folder": "images",
    "max": None,
    "dry_run": False,
    "format": "png",
    "filename": "{original}",
    "quiet": False,
    "log_level": "all"
}
LOG_FILE_NAME = "MagicScryfaller.log"
LOG_MAX_LINES = 10000

def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return name.replace('/', '-')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"[INFO] Creato file di configurazione predefinito '{CONFIG_FILE}'")
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Errore lettura config.json: {e}")
        return DEFAULT_CONFIG

def parse_args():
    parser = argparse.ArgumentParser(description="Scarica immagini da Scryfall.")
    parser.add_argument("query", type=str, help="Query di ricerca Scryfall (tra virgolette)")
    parser.add_argument("--output-folder", "--of", "--fn", type=str)
    parser.add_argument("--max", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", type=str, choices=["small", "normal", "large", "png", "art_crop", "border_crop"])
    parser.add_argument("--filename", type=str)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--log-level", type=str)
    return parser.parse_args()

def init_log(log_path):
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) >= LOG_MAX_LINES:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
    else:
        open(log_path, "w", encoding="utf-8").close()

def append_log(log_path, message, level="all", active_levels=[]):
    if level in active_levels or "all" in active_levels:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(message.strip() + "\n")

def get_original_filename(card):
    uri = card.get("scryfall_uri", "")
    if not uri:
        return "card"
    original = uri.replace("https://scryfall.com/card/", "").split("?")[0].replace("/", "-")
    return clean_filename(original) + ".png"

def get_filename(template, card, fmt, face=None, original_url=None, is_back=False):
    if template == "{original}":
        base = get_original_filename(card)
        if face:
            suffix = " (rear)" if is_back else " (front)"
            base = base.replace(".png", suffix + ".png")
        return base

    name = template
    name = name.replace("{set_code}", card.get("set", "").upper())
    name = name.replace("{number}", card.get("collector_number", ""))
    name = name.replace("{name}", card.get("name", ""))

    if "{face}" in name and face:
        name = name.replace("{face}", face.get("name", ""))
    elif face:
        suffix = " (rear)" if is_back else " (front)"
        name += suffix

    if "{format}" in name:
        name = name.replace("{format}", fmt)
    elif fmt != "png":
        name += f" ({fmt})"

    return clean_filename(name) + ".jpg" if fmt != "png" else clean_filename(name) + ".png"

def download_image(url, filepath, dry_run=False):
    if dry_run:
        return "DRY-RUN"
    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(r.content)
        return "OK"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    args = parse_args()
    config = load_config()

    output = args.output_folder or config.get("output_folder", "images")
    os.makedirs(output, exist_ok=True)

    log_path = os.path.join(output, LOG_FILE_NAME)
    init_log(log_path)

    max_cards = args.max if args.max is not None else config.get("max")
    dry_run = args.dry_run or config.get("dry_run", False)
    fmt = args.format or config.get("format", "png")
    filename_template = args.filename or config.get("filename", "{original}")
    quiet = args.quiet or config.get("quiet", False)
    log_level = (args.log_level or config.get("log_level", "all")).split(",")

    query = args.query
    base_url = f"https://api.scryfall.com/cards/search?q={quote(query)}"
    total = 0
    skipped = 0
    errors = 0
    downloaded = 0
    results = []

    while base_url:
        res = requests.get(base_url)
        res.raise_for_status()
        data = res.json()

        results.extend(data["data"])
        base_url = data.get("next_page")
        if max_cards and len(results) >= max_cards:
            results = results[:max_cards]
            break

    if not quiet:
        progress = tqdm(total=len(results), desc="Download immagini", unit="img")

    for card in results:
        try:
            if "image_uris" in card:
                url = card["image_uris"].get(fmt)
                if not url:
                    errors += 1
                    append_log(log_path, f"[ERROR] Nessun formato '{fmt}' per {card['name']}", "errors", log_level)
                    continue
                fname = get_filename(filename_template, card, fmt, original_url=url)
                fpath = os.path.join(output, fname)
                if os.path.exists(fpath):
                    skipped += 1
                    append_log(log_path, f"[SKIP] {fname}", "skipped", log_level)
                else:
                    result = download_image(url, fpath, dry_run)
                    append_log(log_path, f"[{result}] {fname}", result.lower(), log_level)
                    if result == "OK":
                        downloaded += 1
                    elif result.startswith("ERROR"):
                        errors += 1
            elif "card_faces" in card:
                for i, face in enumerate(card["card_faces"]):
                    url = face.get("image_uris", {}).get(fmt)
                    if not url:
                        continue
                    is_back = (i == 1)
                    fname = get_filename(filename_template, card, fmt, face=face, original_url=url, is_back=is_back)
                    fpath = os.path.join(output, fname)
                    if os.path.exists(fpath):
                        skipped += 1
                        append_log(log_path, f"[SKIP] {fname}", "skipped", log_level)
                    else:
                        result = download_image(url, fpath, dry_run)
                        append_log(log_path, f"[{result}] {fname}", result.lower(), log_level)
                        if result == "OK":
                            downloaded += 1
                        elif result.startswith("ERROR"):
                            errors += 1
        except Exception as e:
            errors += 1
            append_log(log_path, f"[ERROR] {e}", "errors", log_level)
        if not quiet:
            progress.update(1)

    if not quiet:
        progress.close()
        print(f"\n[RISULTATI]")
        print(f" Scaricate: {downloaded}")
        print(f" Saltate:   {skipped}")
        print(f" Errori:    {errors}")
        if dry_run:
            print(" [Modalità simulazione attiva]")

if __name__ == "__main__":
    main()
