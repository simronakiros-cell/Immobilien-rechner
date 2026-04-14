from flask import Flask, render_template, request, session
from datetime import datetime
import os

app = Flask(__name__)
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
            if bundesland in GRUNDERWERBSTEUER and preis > 0:
                notarkosten = preis * NOTARKOSTEN_SATZ
                grunderwerbsteuer = preis * (GRUNDERWERBSTEUER[bundesland] / 100)
                maklerkosten = preis * (makler_prozent / 100)
                gesamtkosten = preis + notarkosten + grunderwerbsteuer + maklerkosten
                result = {
                    "preis": preis,
                    "bundesland": bundesland,
                    "notarkosten": notarkosten,
                    "grunderwerbsteuer_pct": GRUNDERWERBSTEUER[bundesland],
                    "grunderwerbsteuer": grunderwerbsteuer,
                    "makler_prozent": makler_prozent,
                    "maklerkosten": maklerkosten,
                    "gesamtkosten": gesamtkosten,
                    "nebenkosten": notarkosten + grunderwerbsteuer + maklerkosten,
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
    return {"success": True}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)
