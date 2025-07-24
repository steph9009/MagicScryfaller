# Magic Scryfaller

**Magic Scryfaller** è uno script da riga di comando per scaricare automaticamente immagini di carte Magic: The Gathering usando le API di [Scryfall](https://scryfall.com/). Supporta opzioni avanzate per formattazione del nome file, filtro dei risultati, gestione del formato immagine e logging.

## Caratteristiche

* Supporto completo alla sintassi di ricerca di Scryfall
* Download immagini ad alta risoluzione (fino a PNG full-size)
* Gestione carte con fronte-retro
* Personalizzazione della sintassi del nome file con segnaposto
* File di configurazione `config.json` generato automaticamente
* Log automatico (`MagicScryfaller.log`) con rotazione oltre 10.000 righe
* Modalità dry-run per simulare i download
* Barra di avanzamento elegante con `tqdm`
* Opzione `--quiet` per output silenzioso

## Requisiti

* Python 3.8+
* Librerie: `requests`, `tqdm`

Puoi installarle con:

```bash
pip install -r requirements.txt
```

## Utilizzo

### Sintassi base:

```bash
python MagicScryfaller.py "<query>"
```
La query supporta la stessa sintassi del sito di [Scryfall](https://scryfall.com/docs/syntax).

### Esempi:

```bash
python MagicScryfaller.py "is:fullart set:ff" --format png --filename "{set_code}-{number}. {name}" --max 50

python MagicScryfaller.py "t:land" --dry-run --format art_crop
```

### Screenshot:
<img width="720" alt="--dry-run" src="https://github.com/user-attachments/assets/aa97c53c-eb55-448e-935c-73de79e9d340" />
<img width="720" alt="--max" src="https://github.com/user-attachments/assets/17e6ed04-15b4-4208-9964-6a2c7f42f07e" />
<img width="720" alt="downloads" src="https://github.com/user-attachments/assets/4f213fcf-c7ec-4080-bd5f-9ba8ed5439f7" />

### Opzioni disponibili:

* `--output-folder`, `--of`, `--fn`: cartella di output (default: `images`)
* `--format`: formato immagine da scaricare (`png`, `large`, `art_crop`, ecc.)
* `--filename`: template per il nome file (vedi sotto)
* `--max`: massimo numero di carte da scaricare
* `--dry-run`: non scarica davvero, mostra solo cosa farebbe
* `--quiet`: nessun output su terminale (eccetto errori critici)
* `--log-level`: cosa scrivere nel file di log (`all`, `errors`, `skipped`, `downloaded`, `dry-run`)

## Template per il nome file

Puoi usare questi placeholder nella sintassi del filename:

* `{set_code}`: codice del set (es. `FIN`)
* `{number}`: numero collezione della carta
* `{name}`: nome completo della carta
* `{face}`: nome della singola faccia (per carte bifronte)
* `{original}`: costruito dal `scryfall_uri` (es. `fin-212-absolute-virtue.png`)
* `{format}`: formato immagine selezionato (utile per evitare sovrascritture PNG/JPG)

Se `{face}` non è incluso e la carta è bifronte, verrà aggiunto automaticamente `-front` o `-back`.

Se `{format}` non è incluso e il formato non è `png`, verrà aggiunto come suffisso: `({format})`.

## File di configurazione

Lo script genera automaticamente un file `config.json` con i valori di default. Puoi modificarlo per personalizzare le opzioni in modo permanente. Gli argomenti da CLI sovrascrivono quelli del file.

Esempio:

```json
{
  "output_folder": "images",
  "max": null,
  "dry_run": false,
  "format": "png",
  "filename": "{original}",
  "quiet": false,
  "log_level": "all"
}
```

## Log

Lo script crea automaticamente un file di log `MagicScryfaller.log` nella cartella di destinazione. Quando supera le 10.000 righe, viene svuotato automaticamente.

## Licenza

MIT

---

Creato con il ❤️ da Stefano ed il supporto di ChatGPT
