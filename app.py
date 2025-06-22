from flask import Flask, render_template, request, redirect, session
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "change-moi"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.form.get("password") == "AdminDanino":
            session["auth"] = True
            return redirect("/search")
        return render_template("index.html", error="Mot de passe incorrect")
    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if not session.get("auth"):
        return redirect("/")
    
    criteria = {"loc": "Nice", "price": "120000", "surface": "30"}
    
    if request.method == "POST":
        criteria = {
            "loc": request.form.get("loc", "Nice"),
            "price": request.form.get("price", "120000"),
            "surface": request.form.get("surface", "30")
        }
    
    annonces = run_search(criteria)
    return render_template("results.html", annonces=annonces, criteria=criteria)

def run_search(c):
    url = f"https://www.leboncoin.fr/recherche?category=10&locations={c['loc']}&real_estate_type=2&price=0-{c['price']}"
    print(f"[DEBUG] URL utilisée : {url}")

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[DEBUG] Erreur lors de la requête : {e}")
        return []

    res = []
    for item in soup.select("a[data-qa-id='aditem_container']"):
        try:
            titre = item.select_one("p[data-qa-id='aditem_title']").text.strip()
            prix_txt = item.select_one("span[data-qa-id='aditem_price']").text.strip().replace("€", "").replace(" ", "").replace(" ", "")
            surface_txt = item.select_one("p[data-qa-id='aditem_description']").text.strip()
            
            prix = int(prix_txt)
            surface = int(''.join(filter(str.isdigit, surface_txt.split("m²")[0])))
            prix_m2 = prix / surface

            print(f"[DEBUG] {titre} — {prix}€ — {surface}m² — {prix_m2:.1f}€/m²")

            if prix_m2 < 3500:
                res.append({
                    "titre": titre,
                    "prix": prix,
                    "surface": surface,
                    "prix_m2": round(prix_m2, 1),
                    "url": "https://www.leboncoin.fr" + item["href"]
                })

        except Exception as e:
            print(f"[DEBUG] Erreur sur une annonce : {e}")
            continue

    print(f"[DEBUG] Total annonces valides : {len(res)}")
    return res

if __name__ == "__main__":
    app.run(debug=True)
