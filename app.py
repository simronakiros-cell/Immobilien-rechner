from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from datetime import datetime
import os
import math
import secrets
import random

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

@app.template_filter('german_number')
def german_number(value, decimals=0):
    if value is None:
        value = 0
    try:
        return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0"

GRUNDERWERBSTEUER = {
    "Baden-Württemberg": 5.0,
    "Bayern": 3.5,
    "Berlin": 6.0,
    "Brandenburg": 6.5,
    "Bremen": 5.0,
    "Hamburg": 5.5,
    "Hessen": 6.0,
    "Mecklenburg-Vorpommern": 6.0,
    "Niedersachsen": 5.0,
    "Nordrhein-Westfalen": 6.5,
    "Rheinland-Pfalz": 5.0,
    "Saarland": 6.5,
    "Sachsen": 5.5,
    "Sachsen-Anhalt": 5.0,
    "Schleswig-Holstein": 6.5,
    "Thüringen": 6.5
}
NOTAR_GRUNDBUCH_SATZ = 0.02


def calculate_loan(kreditbetrag, zinssatz, laufzeit, tilgungssatz, restschuld):
    if laufzeit <=0:
        return None
    if kreditbetrag <= 0:
        return {
            "kreditbetrag": 0, "zinssatz": zinssatz, "laufzeit": laufzeit,
            "tilgungssatz": 0, "restschuld": 0, "monatliche_rate": 0,
            "gesamt_zinsen": 0, "tilgung_prinzipal": 0, "gesamtzahlung": 0
        }
    
    r = (zinssatz / 100) / 12  # monatlicher Zinssatz
    n = laufzeit * 12  # Monate
    
    # Annuitätenformel: Rate basierend auf Laufzeit
    if r > 0:
        factor = math.pow(1 + r, n)
        monatliche_rate = kreditbetrag * r * factor / (factor - 1)
        # Restschuld berechnen
        restschuld_berechnet = kreditbetrag * factor - monatliche_rate * (factor - 1) / r
        restschuld_berechnet = max(0, restschuld_berechnet)
    else:
        monatliche_rate = kreditbetrag / n
        restschuld_berechnet = 0
    
    # Effektive Tilgungsrate berechnen (abgeleitet von der Rate)
    if kreditbetrag > 0 and r > 0:
        zins_erster_monat = kreditbetrag * r
        tilgung_monatlich = monatliche_rate - zins_erster_monat
        tilgungssatz_effektiv = (tilgung_monatlich * 12 / kreditbetrag) * 100
    else:
        tilgungssatz_effektiv = tilgungssatz
    
    # Gesamtergebnis
    gesamtzahlung = monatliche_rate * n
    tilgung_prinzipal = kreditbetrag - restschuld_berechnet
    gesamt_zinsen = gesamtzahlung - tilgung_prinzipal
    
    return {
        "kreditbetrag": kreditbetrag,
        "zinssatz": zinssatz,
        "laufzeit": laufzeit,
        "tilgungssatz": round(tilgungssatz_effektiv, 2),
        "restschuld": round(restschuld_berechnet, 2),
        "monatliche_rate": monatliche_rate,
        "gesamt_zinsen": gesamt_zinsen,
        "tilgung_prinzipal": tilgung_prinzipal,
        "gesamtzahlung": gesamtzahlung
    }
    
    r = (zinssatz / 100) / 12  # monatlicher Zinssatz
    n = laufzeit * 12  # Monate
    
    if r > 0:
        # Annuity formula: PMT = PV * r * (1+r)^n / ((1+r)^n - 1)
        factor = math.pow(1 + r, n)
        monatliche_rate = kreditbetrag * r * factor / (factor - 1)
        
        # Restschuld nach n Monaten berechnen
        restschuld_berechnet = kreditbetrag * factor - monatliche_rate * (factor - 1) / r
        restschuld_berechnet = max(0, restschuld_berechnet)
        
        # Effektive Tilgungsrate (erster Monat)
        zins_erster_monat = kreditbetrag * r
        tilgung_monatlich = monatliche_rate - zins_erster_monat
        tilgungssatz_effektiv = (tilgung_monatlich * 12 / kreditbetrag) * 100
    else:
        monatliche_rate = kreditbetrag / n
        restschuld_berechnet = 0
        tilgungssatz_effektiv = tilgungssatz
    
    # Gesamtergebnis
    gesamtzahlung = monatliche_rate * n
    tilgung_prinzipal = kreditbetrag - restschuld_berechnet
    gesamt_zinsen = gesamtzahlung - tilgung_prinzipal
    
    return {
        "kreditbetrag": kreditbetrag,
        "zinssatz": zinssatz,
        "laufzeit": laufzeit,
        "tilgungssatz": round(tilgungssatz_effektiv, 2),
        "restschuld": round(restschuld_berechnet, 2),
        "monatliche_rate": monatliche_rate,
        "gesamt_zinsen": gesamt_zinsen,
        "tilgung_prinzipal": tilgung_prinzipal,
        "gesamtzahlung": gesamtzahlung
    }
    
    monatlicher_zins = (zinssatz / 100) / 12 if zinssatz > 0 else 0
    monate = laufzeit * 12
    
    # Annuitätenformel: Rate basierend auf Laufzeit
    if monatlicher_zins > 0:
        zinsfaktor = 1 + monatlicher_zins
        zinsfaktor_hoch_n = math.pow(zinsfaktor, monate)
        # Formel: Rate = Kredit * [r(1+r)^n] / [(1+r)^n - 1]
        monatliche_rate = kreditbetrag * (monatlicher_zins * zinsfaktor_hoch_n) / (zinsfaktor_hoch_n - 1)
        # Restschuld berechnen
        restschuld_tatsaechlich = kreditbetrag * zinsfaktor_hoch_n - monatliche_rate * (zinsfaktor_hoch_n - 1) / monatlicher_zins
        restschuld_tatsaechlich = max(0, restschuld_tatsaechlich)
    else:
        monatliche_rate = kreditbetrag / monate
        restschuld_tatsaechlich = 0
    
    # Effektive Tilgungsrate berechnen (abgeleitet von der Rate)
    if kreditbetrag > 0 and monatlicher_zins > 0:
        zins_erster_monat = kreditbetrag * monatlicher_zins
        tilgung_monatlich = monatliche_rate - zins_erster_monat
        tilgungssatz_effektiv = (tilgung_monatlich * 12 / kreditbetrag) * 100
    else:
        tilgungssatz_effektiv = tilgungssatz
    
    # Gesamtzahlungen und Zinsen
    gesamtzahlung = monatliche_rate * monate
    tilgung_prinzipal = kreditbetrag - restschuld_tatsaechlich
    gesamt_zinsen = gesamtzahlung - tilgung_prinzipal
    
    return {
        "kreditbetrag": kreditbetrag,
        "zinssatz": zinssatz,
        "laufzeit": laufzeit,
        "tilgungssatz": round(tilgungssatz_effektiv, 2),
        "restschuld": round(restschuld_tatsaechlich, 2),
        "monatliche_rate": monatliche_rate,
        "gesamt_zinsen": gesamt_zinsen,
        "tilgung_prinzipal": tilgung_prinzipal,
        "gesamtzahlung": gesamtzahlung
    }
    
    monatlicher_zins = (zinssatz / 100) / 12 if zinssatz > 0 else 0
    monate = laufzeit * 12
    
    # Korrekte Annuitätenformel mit Restschuld:
    # Rate = (Kredit * r * (1+r)^n - Restschuld * r) / ((1+r)^n - 1)
    # wobei r = monatlicher_zins, n = monate
    if monatlicher_zins > 0:
        zinsfaktor = 1 + monatlicher_zins
        zinsfaktor_hoch_n = math.pow(zinsfaktor, monate)
        # Formel: Rate = (K * r * (1+r)^n - Restschuld * r) / ((1+r)^n - 1)
        monatliche_rate = (kreditbetrag * monatlicher_zins * zinsfaktor_hoch_n - restschuld * monatlicher_zins) / (zinsfaktor_hoch_n - 1)
        # Tatsächliche Restschuld berechnen (Soll = Ist)
        restschuld_tatsaechlich = kreditbetrag * zinsfaktor_hoch_n - monatliche_rate * (zinsfaktor_hoch_n - 1) / monatlicher_zins
        restschuld_tatsaechlich = max(0, restschuld_tatsaechlich)
    else:
        monatliche_rate = (kreditbetrag - restschuld) / monate
        restschuld_tatsaechlich = restschuld
    
    # Effektive Tilgungsrate berechnen (abgeleitet von der Rate)
    if kreditbetrag > 0 and monatlicher_zins > 0:
        zins_erster_monat = kreditbetrag * monatlicher_zins
        tilgung_monatlich = monatliche_rate - zins_erster_monat
        tilgungssatz_effektiv = (tilgung_monatlich * 12 / kreditbetrag) * 100
    else:
        tilgungssatz_effektiv = tilgungssatz
    
    # Gesamtzahlungen und Zinsen
    gesamtzahlung = monatliche_rate * monate
    tilgung_prinzipal = kreditbetrag - restschuld_tatsaechlich
    gesamt_zinsen = gesamtzahlung - tilgung_prinzipal
    
    return {
        "kreditbetrag": kreditbetrag,
        "zinssatz": zinssatz,
        "laufzeit": laufzeit,
        "tilgungssatz": round(tilgungssatz_effektiv, 2),
        "restschuld": round(restschuld_tatsaechlich, 2),
        "monatliche_rate": monatliche_rate,
        "gesamt_zinsen": gesamt_zinsen,
        "tilgung_prinzipal": tilgung_prinzipal,
        "gesamtzahlung": gesamtzahlung
    }
    
    monatlicher_zins = (zinssatz / 100) / 12 if zinssatz > 0 else 0
    monatliche_tilgung = (tilgungssatz / 100) / 12
    monate = laufzeit * 12
    
    # Deutsche Berechnung: Rate = Kredit * (Zins + Tilgung) pro Monat
    monatliche_rate = kreditbetrag * (monatlicher_zins + monatliche_tilgung)
    
    # Restschuld nach Laufzeit mit Zinseszins berechnen
    if monatlicher_zins > 0:
        zinsfaktor = 1 + monatlicher_zins
        # Restschuld = Kredit * (1+r)^n - Rate * [(1+r)^n - 1] / r
        restschuld_tatsaechlich = kreditbetrag * math.pow(zinsfaktor, monate) - monatliche_rate * (math.pow(zinsfaktor, monate) - 1) / monatlicher_zins
        restschuld_tatsaechlich = max(0, restschuld_tatsaechlich)
    else:
        restschuld_tatsaechlich = kreditbetrag - (monatliche_rate * monate)
        restschuld_tatsaechlich = max(0, restschuld_tatsaechlich)
    
    # Gesamtzahlungen und Zinsen
    gesamtzahlung = monatliche_rate * monate
    tilgung_prinzipal = kreditbetrag - restschuld_tatsaechlich
    gesamt_zinsen = gesamtzahlung - tilgung_prinzipal
    
    return {
        "kreditbetrag": kreditbetrag,
        "zinssatz": zinssatz,
        "laufzeit": laufzeit,
        "tilgungssatz": round(tilgungssatz, 2),
        "restschuld": round(restschuld_tatsaechlich, 2),
        "monatliche_rate": monatliche_rate,
        "gesamt_zinsen": gesamt_zinsen,
        "tilgung_prinzipal": tilgung_prinzipal,
        "gesamtzahlung": gesamtzahlung
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if "history" not in session:
        session["history"] = []

    result = None
    if request.method == "POST":
        try:
            def parse_number(val):
                if not val:
                    return 0
                val = str(val).strip()
                if not val:
                    return 0
                # Deutsches Format: 1.000,00 oder 1000,00
                if ',' in val:
                    if '.' in val:
                        # Format: 1.000,00 (deutsche Tausender mit Komma-Decimal)
                        val = val.replace('.', '').replace(',', '.')
                    else:
                        # Format: 1000,00 (Komma-Decimal ohne Tausender)
                        val = val.replace(',', '.')
                elif '.' in val:
                    # Prüfen ob englisches Format (1000.00) oder deutsche Tausender (1.000)
                    parts = val.split('.')
                    if len(parts[-1]) <= 2:
                        # Englisches Format: 1000.00 oder 1000.0
                        pass  # val bleibt unverändert
                    else:
                        # Deutsche Tausender: 1.000
                        val = val.replace('.', '')
                return float(val)
            
            preis = parse_number(request.form.get("preis", 0))
            bundesland = request.form.get("bundesland", "")
            makler_prozent = parse_number(request.form.get("makler_prozent", 3.5))
            eigenkapital = parse_number(request.form.get("eigenkapital", 0))
            zinssatz = parse_number(request.form.get("zinssatz", 3.5))
            laufzeit = int(parse_number(request.form.get("laufzeit", 10)))
            tilgung = parse_number(request.form.get("tilgung", 2.0))
            restschuld = parse_number(request.form.get("restschuld", 0))
            
            if bundesland in GRUNDERWERBSTEUER and preis > 0:
                notarkosten_gesamt = preis * NOTAR_GRUNDBUCH_SATZ
                grunderwerbsteuer = preis * (GRUNDERWERBSTEUER[bundesland] / 100)
                maklerkosten = preis * (makler_prozent / 100)
                gesamtkosten = preis + notarkosten_gesamt + grunderwerbsteuer + maklerkosten
                
                kreditbetrag = max(0, gesamtkosten - eigenkapital)
                loan_info = calculate_loan(kreditbetrag, zinssatz, laufzeit, tilgung, restschuld)
                
                mieteinnahmen = parse_number(request.form.get("mieteinnahmen", 0))
                nebenkosten = parse_number(request.form.get("nebenkosten", 0))
                verwaltung = parse_number(request.form.get("verwaltung", 0))
                ruecklage = parse_number(request.form.get("ruecklage", 0))
                
                bruttorendite = (mieteinnahmen * 12 / gesamtkosten * 100) if gesamtkosten > 0 else 0
                gesamt_nebenkosten = nebenkosten + verwaltung + ruecklage
                rendite_info = None
                if preis > 0:
                    nettomiete = (mieteinnahmen * 12) - (gesamt_nebenkosten * 12)
                    rendite = (nettomiete / (eigenkapital if eigenkapital > 0 else preis)) * 100 if eigenkapital > 0 or preis > 0 else 0
                    monatlicher_cashflow = mieteinnahmen - gesamt_nebenkosten - (loan_info["monatliche_rate"] if loan_info else 0)
                    
                    rendite_info = {
                        "bruttorendite": bruttorendite,
                        "nettomiete_jahr": nettomiete,
                        "gesamtnachrang": gesamt_nebenkosten,
                        "rendite": rendite,
                        "monatlicher_cashflow": monatlicher_cashflow,
                        "mieteinnahmen": mieteinnahmen,
                        "nebenkosten": nebenkosten,
                        "verwaltung": verwaltung,
                        "ruecklage": ruecklage
                    }
                
                result = {
                    "preis": preis,
                    "bundesland": bundesland,
                    "notarkosten_gesamt": notarkosten_gesamt,
                    "grunderwerbsteuer_pct": GRUNDERWERBSTEUER[bundesland],
                    "grunderwerbsteuer": grunderwerbsteuer,
                    "makler_prozent": makler_prozent,
                    "maklerkosten": maklerkosten,
                    "gesamtkosten": gesamtkosten,
                    "nebenkosten_kauf": notarkosten_gesamt + grunderwerbsteuer + maklerkosten,
                    "eigenkapital": eigenkapital,
                    "zinssatz": zinssatz,
                    "laufzeit": laufzeit,
                    "tilgung": tilgung,
                    "restschuld": restschuld,
                    "kreditbetrag": kreditbetrag,
                    "loan_info": loan_info,
                    "rendite_info": rendite_info,
                    "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
                }
                session["history"].insert(0, result)
                if len(session["history"]) > 20:
                    session["history"] = session["history"][:20]
                session.modified = True
        except ValueError:
            pass

    history = session.get("history", [])
    return render_template("index.html", bundeslaender=GRUNDERWERBSTEUER.keys(), result=result, history=history)


@app.route("/clear", methods=["POST"])
def clear_history():
    session["history"] = []
    return redirect(url_for("index"))


@app.route("/flights", methods=["GET", "POST"])
def flights():
    if "flights" not in session:
        session["flights"] = []

    result = None
    if request.method == "POST":
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        target_price = request.form.get("target_price", "300").strip()

        try:
            target_price = int(target_price) if target_price else 300
        except ValueError:
            target_price = 300

        if origin and destination:
            current_price = random.randint(150, 800)
            result = {
                "origin": origin,
                "destination": destination,
                "target_price": target_price,
                "current_price": current_price,
                "found": current_price <= target_price,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            session["flights"].insert(0, result)
            if len(session["flights"]) > 20:
                session["flights"] = session["flights"][:20]
            session.modified = True

    flights_history = session.get("flights", [])
    return render_template("flights.html", result=result, flights=flights_history)


@app.route("/api/check-flight", methods=["POST"])
def api_check_flight():
    data = request.get_json()
    origin = data.get("origin", "")
    destination = data.get("destination", "")
    target_price = data.get("target_price", 300)

    current_price = random.randint(150, 800)
    return jsonify({
        "origin": origin,
        "destination": destination,
        "current_price": current_price,
        "target_price": target_price,
        "found": current_price <= target_price,
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
