#!/usr/bin/env python3
"""Applica il branding "Dedalo HelpDesk" (Kebox) ai sorgenti di RustDesk.

Si lancia dalla radice del repository, dopo il checkout con i submodule:
    python3 kebox/applica_branding.py

Le modifiche NON sono committate nei sorgenti: lo script le applica al volo in CI,
così per passare a una nuova versione di RustDesk basta fare il rebase del branch
`kebox` sul nuovo tag. Ogni sostituzione verifica che il testo atteso esista: se
upstream cambia qualcosa, la build si ferma qui invece di produrre un client a metà.
"""
import shutil
import sys
from pathlib import Path

APP_NAME = "DedaloHelpDesk"          # nome tecnico: servizio, cartelle, schema URI (niente spazi)
NOME_VISIBILE = "Dedalo HelpDesk"    # nome mostrato all'utente
SERVER = "help.kebox.it"
CHIAVE = "Vpt43r+WTjD0ZEh+LpPv6wVERb8Lb+xQo+WpgeHr2bk="
API = "https://help.kebox.it"

RADICE = Path(__file__).resolve().parent.parent
ASSETS = RADICE / "kebox" / "assets"


def sostituisci(rel, vecchio, nuovo, volte=1):
    p = RADICE / rel
    testo = p.read_text(encoding="utf-8")
    n = testo.count(vecchio)
    if n != volte:
        sys.exit(f"ERRORE {rel}: atteso {volte} occorrenze di {vecchio!r}, trovate {n}")
    p.write_text(testo.replace(vecchio, nuovo), encoding="utf-8", newline="")
    print(f"ok  {rel}")


def copia(src, *dest):
    for d in dest:
        shutil.copyfile(ASSETS / src, RADICE / d)
        print(f"ok  {d}  <- {src}")


# --- nome, server e chiave (hbb_common) ---
cfg = "libs/hbb_common/src/config.rs"
sostituisci(cfg, 'RwLock::new("RustDesk".to_owned());', f'RwLock::new("{APP_NAME}".to_owned());')
sostituisci(cfg, 'RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
            f'RENDEZVOUS_SERVERS: &[&str] = &["{SERVER}"];')
sostituisci(cfg, 'RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
            f'RS_PUB_KEY: &str = "{CHIAVE}";')

# --- server API (rubrica, login, heartbeat) di default ---
sostituisci("src/common.rs", '    "https://admin.rustdesk.com".to_owned()\n}',
            f'    "{API}".to_owned()\n}}')

# --- niente aggiornamenti automatici: scaricherebbero il RustDesk originale ---
sostituisci("src/updater.rs", "fn check_update(manually: bool) -> ResultType<()> {\n",
            "fn check_update(manually: bool) -> ResultType<()> {\n"
            "    if crate::is_custom_client() {\n        return Ok(());\n    }\n")

# --- nome visibile: titolo finestre e testi tradotti ---
sostituisci("flutter/lib/common.dart",
            "String getWindowName({WindowType? overrideType}) {\n  final name = bind.mainGetAppNameSync();",
            f"String getWindowName({{WindowType? overrideType}}) {{\n  final name = '{NOME_VISIBILE}';")
sostituisci("src/lang.rs",
            '                if !app_name.contains("RustDesk") {\n'
            '                    s = s.replace("RustDesk", &app_name);',
            '                if !app_name.contains("RustDesk") {\n'
            f'                    s = s.replace("RustDesk", "{NOME_VISIBILE}");')

# --- installer MSI: collegamenti e testi con il nome visibile ---
# preprocess.py sostituirebbe "RustDesk" con il nome tecnico; qui lo anticipiamo col nome visibile.
# Resta tecnico solo SC_Client_Tray: TryDeleteStartupShortcut lo cerca come "$(var.Product) Tray".
for wxl in sorted((RADICE / "res/msi/Package/Language").glob("*.wxl")):
    righe = wxl.read_text(encoding="utf-8").splitlines(keepends=True)
    nuove = [r if 'Id="SC_Client_Tray"' in r else r.replace("RustDesk", NOME_VISIBILE) for r in righe]
    if nuove != righe:
        wxl.write_text("".join(nuove), encoding="utf-8", newline="")
        print(f"ok  {wxl.relative_to(RADICE)}")

# --- icone e logo ---
copia("tray-icon.ico", "res/tray-icon.ico")
copia("icon.ico", "res/icon.ico",
      "flutter/windows/runner/resources/app_icon.ico", "flutter/assets/icon.ico")
copia("icon.png", "res/icon.png", "flutter/assets/icon.png")
for f in ("32x32.png", "64x64.png", "128x128.png", "128x128@2x.png"):
    copia(f, f"res/{f}")
copia("logo.png", "flutter/assets/logo.png")

print(f"Branding {NOME_VISIBILE} applicato.")
