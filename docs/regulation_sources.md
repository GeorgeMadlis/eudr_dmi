# Regulation Sources Registry

Purpose: record authoritative source snapshots (HTML/PDF) and their SHA-256 fingerprints without embedding the regulation text in this repository.

Server audit root: `/Users/server/audit/eudr_dmi`

| Source | URL | Local Path (server) | SHA256 | Notes |
|---|---|---|---|---|
| EUDR 2023/1115 — OJ (ELI) HTML | https://eur-lex.europa.eu/eli/reg/2023/1115/oj/eng | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_oj_eng.html` | TODO | Automated download currently blocked by an EUR-Lex WAF challenge (HTTP 202 with `x-amzn-waf-action: challenge`) in this environment; re-run the documented curl commands from a network that can fetch the artefacts, then update SHA256 from `SHA256SUMS.txt`. |
| EUDR 2023/1115 — Consolidated HTML (2024-12-26) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02023R1115-20241226 | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_consolidated_2024-12-26_en.html` | TODO | Same as above. |
| EUDR 2023/1115 — CELEX PDF endpoint (32023R1115) | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1115 | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_celex_32023R1115_en.pdf` | TODO | Store whatever is returned (PDF or HTML); hash the file as stored. |

Expected SHA256SUMS paths (server):
- `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/SHA256SUMS.txt`
- `/Users/server/audit/eudr_dmi/regulation/guidance/SHA256SUMS.txt` (if guidance PDFs are added)
