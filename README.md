# Immobilien Rechner

Immobilien-Kostenrechner mit Grunderwerbsteuer, Notarkosten und Maklerprovision.

## Online nutzen

1. **Auf GitHub hochladen:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/DEIN-USERNAME/immobilien-rechner.git
   git push -u origin main
   ```

2. **Auf Render.com deployen:**
   - render.com → New → Web Service
   - GitHub Repo verbinden
   - Build Command: (leer lassen)
   - Start Command: `gunicorn app:app`
   - Environment: Python 3

3. **Fertig!** Du erhältst eine URL wie `https://deine-app.onrender.com`

## Lokal ausführen

```bash
pip install -r requirements.txt
python app.py
```

Öffne dann http://localhost:8080
