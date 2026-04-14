from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import os
import math

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("SECRET_KEY", "immobilien-rechner-2024")

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
NOTARKOSTEN_SATZ = 0.015


def calculate_loan(kreditbetrag, zinssatz, laufzeit, tilgungssatz, restschuld):
    if kreditbetrag <= 0 or zinssatz <= 0 or laufzeit <= 0:
        return None
    
    monatlicher_zins = (zinssatz / 100) / 12
    monate = laufzeit * 12
    
    if monatlicher_zins > 0:
        monatliche_rate = kreditbetrag * (monatlicher_zins * math.pow(1 + monatlicher_zins, monate)) / (math.pow(1 + monatlicher_zins, monate) - 1)
    else:
        monatliche_rate = kreditbetrag / monate
    
    gesamt_zinsen = (monatliche_rate * monate) - kreditbetrag
    gesamttilgung = kreditbetrag - restschuld
    
    return {
        "kreditbetrag": kreditbetrag,
        "zinssatz": zinssatz,
        "laufzeit": laufzeit,
        "tilgungssatz": tilgungssatz,
        "restschuld": restschuld,
        "monatliche_rate": monatliche_rate,
        "gesamt_zinsen": gesamt_zinsen,
        "gesamttilgung": gesamttilgung,
        "kosten_gesamt": monatliche_rate * monate
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if "history" not in session:
        session["history"] = []

    result = None
    if request.method == "POST":
        try:
            preis = float(request.form.get("preis", 0))
            bundesland = request.form.get("bundesland", "")
            makler_prozent = float(request.form.get("makler_prozent", 3.5))
            eigenkapital = float(request.form.get("eigenkapital", 0))
            zinssatz = float(request.form.get("zinssatz", 3.5))
            laufzeit = int(request.form.get("laufzeit", 10))
            tilgung = float(request.form.get("tilgung", 2.0))
            restschuld = float(request.form.get("restschuld", 0))
            
            if bundesland in GRUNDERWERBSTEUER and preis > 0:
                notarkosten = preis * NOTARKOSTEN_SATZ
                grunderwerbsteuer = preis * (GRUNDERWERBSTEUER[bundesland] / 100)
                maklerkosten = preis * (makler_prozent / 100)
                gesamtkosten = preis + notarkosten + grunderwerbsteuer + maklerkosten
                
                kreditbetrag = max(0, gesamtkosten - eigenkapital)
                loan_info = calculate_loan(kreditbetrag, zinssatz, laufzeit, tilgung, restschuld)
                
                mieteinnahmen = float(request.form.get("mieteinnahmen", 0))
                nebenkosten = float(request.form.get("nebenkosten", 0))
                verwaltung = float(request.form.get("verwaltung", 0))
                ruecklage = float(request.form.get("ruecklage", 0))
                mietniveau = float(request.form.get("mietniveau", 100))
                
                bruttorendite = (mieteinnahmen * 12 / preis * 100) if preis > 0 else 0
                gesamt_nebenkosten = nebenkosten + verwaltung + ruecklage + (mieteinnahmen * 0.03)
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
                        "ruecklage": ruecklage,
                        "mietniveau": mietniveau
                    }
                
                result = {
                    "preis": preis,
                    "bundesland": bundesland,
                    "notarkosten": notarkosten,
                    "grunderwerbsteuer_pct": GRUNDERWERBSTEUER[bundesland],
                    "grunderwerbsteuer": grunderwerbsteuer,
                    "makler_prozent": makler_prozent,
                    "maklerkosten": maklerkosten,
                    "gesamtkosten": gesamtkosten,
                    "nebenkosten_kauf": notarkosten + grunderwerbsteuer + maklerkosten,
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


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)
