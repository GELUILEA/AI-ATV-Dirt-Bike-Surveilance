# AI Wash Guard — Manual de Instalare și Utilizare

Acest proiect monitorizează automat boxele unei spălătorii auto și oprește curentul dacă detectează vehicule interzise (ATV, Motoare Cross).

## Cerințe Sistem
- Raspberry Pi 5
- Modul cu 4 Relee
- Python 3.11+
- Camere Hikvision cu RTSP activat

## Instalare Dependențe
Rulează următoarele comenzi pe Raspberry Pi:

```bash
# Actualizare sistem
sudo apt update && sudo apt upgrade -y

# Instalare libgpiod pentru control relee
sudo apt install python3-libgpiod gpiod -y

# Instalare dependențe Python
# Metoda recomandată (Virtual Environment):
python -m venv venv
source venv/bin/activate
pip install customtkinter ultralytics opencv-python mysql-connector-python

# SAU Metoda rapidă (dacă primești eroare de managed environment):
pip install customtkinter ultralytics opencv-python mysql-connector-python --break-system-packages
```

## Configurare
Sistemul poate fi configurat prin fișierul `config.json` sau folosind interfața grafică:

### Folosind Interfața de Setări (GUI)
Pentru a deschide fereastra de configurare:
```bash
python main.py --settings
```
Aici poți seta:
- Cele 4 fluxuri RTSP și activarea lor individuală.
- Credențialele Gmail și activarea notificărilor.
- Credențialele MySQL și activarea logării.
- Pinii GPIO pentru relee.

### Configurare Manuală
Poți edita direct fișierul `config.json` generat la prima rulare.

## Utilizare
Pentru a porni monitorizarea automată:
```bash
python main.py
```

Sistemul va afișa în terminal:
- Fluxul video capturat.
- Notificări de detecție ("DETECȚIE: motorcycle identificat").

## Note Tehnice (MVP)
- **Model**: YOLOv8n (Rulează pe CPU la ~2-5 FPS pe flux, suficient pentru detecție).
- **Stabilizare**: Detecția trebuie să fie prezentă în cel puțin 2 cadre consecutive pentru a declanșa releul (previne declanșările false).
- **Logică Relee**: Setat implicit pe **Active Low** (majoritatea modulelor de relee chinezești).
- **Optimizare CPU**: Pentru început, sistemul monitorizează **o singură boxă (Boxa 1)** pentru a nu forța procesorul. Poți activa restul boxelor în `main.py` prin decomentarea liniilor din lista `CAMERAS`.
