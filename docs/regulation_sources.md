# Regulation Sources Registry

Purpose: record authoritative source snapshots (HTML/PDF) and their SHA-256 fingerprints without embedding the regulation text in this repository.

Server audit root: `/Users/server/audit/eudr_dmi`

| Source | URL | Local Path (server) | SHA256 | Notes |
|---|---|---|---|---|
| EUDR 2023/1115 — OJ (ELI) HTML | https://eur-lex.europa.eu/eli/reg/2023/1115/oj/eng | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_oj_eng.html` | TODO | Acquire via the workflow below; do not paste text into repo. |
| EUDR 2023/1115 — Consolidated HTML (2024-12-26) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02023R1115-20241226 | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_consolidated_2024-12-26_en.html` | TODO | Acquire via the workflow below; do not paste text into repo. |
| EUDR 2023/1115 — CELEX PDF endpoint (32023R1115) | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1115 | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_celex_32023R1115_en.pdf` | TODO | Acquire via the workflow below; hash whatever is stored after verification. |

## Operator workflow (WAF-safe)
Some EUR-Lex endpoints may be protected by WAF/login challenges depending on network and headers. This project does not attempt to bypass challenges.

a) Open the link launcher in a browser:
- [docs/regulation_links.html](regulation_links.html)

b) If the browser can access the source, save the artefact to the exact server path shown on the launcher under `/Users/server/audit/eudr_dmi/regulation/...`.

c) Run the acquisition tool to verify non-empty files, compute SHA-256, and update registries:

```sh
python tools/regulation/acquire_and_hash.py --verify
```

Optional: if your browser session is required and you can export cookies, see [docs/secrets_handling.md](secrets_handling.md) and run:

```sh
python tools/regulation/acquire_and_hash.py --fetch --cookie-jar /Users/server/secrets/eudr_dmi/eurlex_cookies.txt
```

Expected SHA256SUMS paths (server):
- `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/SHA256SUMS.txt`
- `/Users/server/audit/eudr_dmi/regulation/guidance/SHA256SUMS.txt` (if guidance PDFs are added)
