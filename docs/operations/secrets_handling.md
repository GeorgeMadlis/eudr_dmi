# Secrets Handling (Operator Guidance)

This repository does not store secrets.

## Secrets directory (outside repo)
Create and secure the secrets directory:

```sh
sudo mkdir -p /Users/server/secrets/eudr_dmi
sudo chown server:staff /Users/server/secrets/eudr_dmi
chmod 700 /Users/server/secrets/eudr_dmi
```

## Cookie jar permissions
If you export browser cookies for EUR-Lex access, store them in a cookie jar file owned by the operator:

```sh
chmod 600 /Users/server/secrets/eudr_dmi/eurlex_cookies.txt
```

Notes:
- The acquisition tool may accept this cookie jar via `--cookie-jar`.
- The tool must not prompt for or store passwords.
- Do not commit secrets. The secrets directory is outside the repository; it is not tracked by git.

## Operator-managed cookie export
If login/WAF challenges require an interactive browser session:
- Authenticate in a normal browser.
- Export cookies to `/Users/server/secrets/eudr_dmi/eurlex_cookies.txt` (operator-managed).
- Run the acquisition tool with `--fetch --cookie-jar ...` or use `--verify` after manually saving files.
