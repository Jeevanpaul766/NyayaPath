# Bare Act Source Files

Place plain-text (.txt) copies of the Indian bare acts here before running
the ingestion script.

## Expected filenames

| Filename   | Act                                          | Regime     |
|------------|----------------------------------------------|------------|
| `BNS.txt`  | Bharatiya Nyaya Sanhita, 2023                | bns_bnss   |
| `BNSS.txt` | Bharatiya Nagarik Suraksha Sanhita, 2023     | bns_bnss   |
| `BSA.txt`  | Bharatiya Sakshya Adhiniyam, 2023            | bns_bnss   |
| `IPC.txt`  | Indian Penal Code, 1860                      | ipc_crpc   |
| `CrPC.txt` | Code of Criminal Procedure, 1973             | ipc_crpc   |

## Where to get the texts

- **India Code portal**: https://www.indiacode.nic.in/  
  Search for the act → download as PDF → convert to plain text with `pdftotext`.

- **PRS India**: https://prsindia.org/ — has cleaner formatted versions.

## After placing files

```bash
pip install -r requirements.txt
python scripts/ingest_bare_acts.py
```

This creates:
- `data/chroma_db/` — ChromaDB vector index
- `data/chroma_db/bm25_index.pkl` — BM25 sparse index
