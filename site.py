import os
import secrets
import sqlite3
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, session, redirect, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

DB = "global_turk.db"

# Render'da bunu Environment Variable olarak vereceğiz.
# Şimdilik yerelde otomatik oluşturulur.
ADMIN_KEY = os.environ.get("ADMIN_KEY", "GT-admin-2026")


def database():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = database()

    con.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            mode TEXT NOT NULL,
            result TEXT,
            created_at TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            created_at TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()


init_db()


def search_web(query):
    try:
        url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)

        headers = {
            "User-Agent":
            "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
            "Chrome/120.0 Mobile Safari/537.36"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=12
        )

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for item in soup.select(".result"):
            title = item.select_one(".result__title")
            link = item.select_one(".result__a")
            snippet = item.select_one(".result__snippet")

            if not title or not link:
                continue

            results.append({
                "title": title.get_text(" ", strip=True),
                "url": link.get("href", ""),
                "snippet": (
                    snippet.get_text(" ", strip=True)
                    if snippet else ""
                )
            })

            if len(results) >= 8:
                break

        return results

    except Exception as error:
        return [{
            "title": "Arama hatası",
            "url": "",
            "snippet": str(error)
        }]


def make_analysis(query, mode):
    results = search_web(query)

    if not results:
        return "Sonuç bulunamadı."

    output = []

    if mode == "advanced":
        output.append("🚀 GELİŞMİŞ ANALİZ")
        output.append("")
        output.append("Sorgu: " + query)
        output.append("")

        for number, item in enumerate(results, 1):
            output.append(
                f"{number}. {item['title']}\n"
                f"{item['snippet']}\n"
                f"Kaynak: {item['url']}\n"
            )

        output.append(
            "📌 Not: Sonuçlar web aramasından alınmıştır. "
            "Önemli bilgileri kaynak sayfasından doğrula."
        )

    else:
        output.append("🤖 NORMAL AI MODU")
        output.append("")

        for number, item in enumerate(results, 1):
            output.append(
                f"{number}. {item['title']}\n"
                f"{item['snippet']}\n"
            )

    return "\n".join(output)


def save_query(text, mode, result):
    con = database()

    con.execute(
        """
        INSERT INTO queries
        (text, mode, result, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            text,
            mode,
            result,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    con.commit()
    con.close()


PAGE = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Global Türk</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    color: white;
    background:
        radial-gradient(
            circle at top,
            #26377a,
            #080b18 60%
        );
}

header {
    position: sticky;
    top: 0;
    z-index: 10;

    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: 16px 20px;

    background: #080c1ddd;
    backdrop-filter: blur(15px);

    border-bottom: 1px solid #303b68;
}

.logo {
    font-size: 22px;
    font-weight: bold;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 15px;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 20px;
}

.hero {
    text-align: center;
    padding: 65px 10px;
}

.hero h1 {
    font-size: 45px;
    margin-bottom: 10px;
}

.card {
    background: #121936;
    border: 1px solid #2b3969;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 15px 40px #0006;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

input,
textarea,
select {
    width: 100%;
    padding: 14px;
    margin: 8px 0;

    background: #080d20;
    color: white;

    border: 1px solid #3a497b;
    border-radius: 12px;
}

button {
    padding: 13px 20px;
    border: 0;
    border-radius: 12px;

    background: #5967f2;
    color: white;

    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: .85;
}

.result {
    white-space: pre-wrap;
    line-height: 1.6;

    background: #080d20;
    padding: 16px;
    border-radius: 15px;

    margin-top: 15px;
}

footer {
    text-align: center;
    padding: 35px;
    color: #8993b9;
}
</style>
</head>

<body>

<header>

<div class="logo">
🌍 Global Türk
</div>

<nav>
<a href="/">Ana Sayfa</a>
<a href="/admin">Admin</a>
</nav>

</header>

<div class="container">

<section class="hero">

<h1>🌍 Global Türk</h1>

<p>
Ücretsiz web araması ve gelişmiş analiz platformu
</p>

</section>


<div class="card">

<h2>🔎 Global Arama</h2>

<form id="searchForm">

<textarea
id="query"
rows="4"
placeholder="Ne araştırmak istiyorsun?"
required></textarea>

<select id="mode">

<option value="normal">
🤖 Normal Mod
</option>

<option value="advanced">
🚀 Gelişmiş AI Modu
</option>

</select>

<button type="submit">
🔍 Ara ve Analiz Et
</button>

</form>

<p id="loading"></p>

<div id="answer" class="result"></div>

</div>


<div class="grid">

<div class="card">
<h2>🤖 AI Modu</h2>
<p>
Sorgunu web sonuçları üzerinden analiz eder.
</p>
</div>

<div class="card">
<h2>🚀 Gelişmiş AI</h2>
<p>
Daha fazla sonuç ve ayrıntılı kaynak gösterimi.
</p>
</div>

<div class="card">
<h2>🌐 Dil</h2>

<select id="language"
        onchange="changeLanguage(this.value)">

<option value="tr">Türkçe</option>
<option value="en">English</option>

</select>

</div>

<div class="card">
<h2>🎵 Fon Müziği</h2>

<audio id="music" controls loop>
<source
src="/static/music.mp3"
type="audio/mpeg">
</audio>

<br><br>

<button onclick="playMusic()">
▶ Müziği Başlat
</button>

</div>

</div>

</div>

<footer>
Global Türk © 2026
</footer>


<script>

document
.getElementById("searchForm")
.addEventListener("submit", async function(event) {

    event.preventDefault();

    const query =
        document.getElementById("query").value;

    const mode =
        document.getElementById("mode").value;

    document.getElementById("loading")
        .innerText = "⏳ Araştırılıyor...";

    document.getElementById("answer")
        .innerText = "";

    try {

        const response = await fetch("/ai", {

            method: "POST",

            headers: {
                "Content-Type":
                "application/json"
            },

            body: JSON.stringify({
                query: query,
                mode: mode
            })
        });

        const data = await response.json();

        document.getElementById("answer")
            .innerText = data.answer;

    } catch (error) {

        document.getElementById("answer")
            .innerText =
            "❌ Bağlantı sırasında hata oluştu.";

    }

    document.getElementById("loading")
        .innerText = "";
});


function playMusic() {

    document
        .getElementById("music")
        .play();

}


function changeLanguage(language) {

    if (language === "en") {

        alert("English mode selected.");

    } else {

        alert("Türkçe modu seçildi.");

    }

}

</script>

</body>
</html>
"""


ADMIN_PAGE = """
<!DOCTYPE html>
<html lang="tr">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>Global Türk Admin</title>

<style>

body {
    margin: 0;
    padding: 20px;

    font-family: Arial;

    color: white;

    background: #080b18;
}

.card {
    background: #151d38;

    padding: 20px;

    border-radius: 18px;

    margin-bottom: 20px;
}

input {
    width: 100%;
    padding: 13px;

    box-sizing: border-box;

    background: #080d20;

    color: white;

    border: 1px solid #354477;

    border-radius: 10px;
}

button {
    margin-top: 10px;

    padding: 12px 18px;

    border: 0;

    border-radius: 10px;

    background: #5967f2;

    color: white;
}

table {
    width: 100%;
    border-collapse: collapse;
}

td,
th {
    padding: 10px;

    border-bottom:
        1px solid #303b63;

    text-align: left;
}

a {
    color: white;
}

</style>

</head>

<body>

<h1>🛠 Global Türk Admin</h1>


{% if not logged %}

<div class="card">

<h2>🔐 Admin Girişi</h2>

<form method="POST">

<input
type="password"
name="key"
placeholder="Admin Key"
required>

<button>
Giriş Yap
</button>

</form>

</div>

{% else %}

<div class="card">

<h2>📊 İstatistikler</h2>

<p>
Toplam sorgu:
<b>{{ total }}</b>
</p>

</div>


<div class="card">

<h2>🔎 Detaylı Sorgu</h2>

<form method="GET">

<input
name="search"
placeholder="Sorgularda ara..."
value="{{ search }}">

<button>
Ara
</button>

</form>

</div>


<div class="card">

<h2>📋 Sorgular</h2>

<table>

<tr>
<th>ID</th>
<th>Sorgu</th>
<th>Mod</th>
<th>Tarih</th>
</tr>

{% for q in results %}

<tr>

<td>{{ q.id }}</td>

<td>{{ q.text }}</td>

<td>{{ q.mode }}</td>

<td>{{ q.created_at }}</td>

</tr>

{% endfor %}

</table>

</div>


<a href="/logout">
🚪 Çıkış Yap
</a>

{% endif %}

</body>
</html>
"""


@app.route("/")
def home():

    con = database()

    ip = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr
    )

    con.execute(
        """
        INSERT INTO visitors
        (ip, created_at)
        VALUES (?, ?)
        """,
        (
            ip,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    con.commit()
    con.close()

    return render_template_string(PAGE)


@app.route("/ai", methods=["POST"])
def ai():

    data = request.get_json() or {}

    query = data.get(
        "query",
        ""
    ).strip()

    mode = data.get(
        "mode",
        "normal"
    )

    if not query:

        return jsonify({
            "answer":
            "❌ Sorgu boş bırakılamaz."
        })

    result = make_analysis(
        query,
        mode
    )

    save_query(
        query,
        mode,
        result
    )

    return jsonify({
        "answer": result
    })


@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin():

    if request.method == "POST":

        key = request.form.get(
            "key",
            ""
        )

        if secrets.compare_digest(
            key,
            ADMIN_KEY
        ):

            session["admin"] = True

            return redirect("/admin")

    if not session.get("admin"):

        return render_template_string(
            ADMIN_PAGE,
            logged=False
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    con = database()

    if search:

        results = con.execute(
            """
            SELECT *
            FROM queries
            WHERE text LIKE ?
            ORDER BY id DESC
            """,
            (
                "%" + search + "%",
            )
        ).fetchall()

    else:

        results = con.execute(
            """
            SELECT *
            FROM queries
            ORDER BY id DESC
            """
        ).fetchall()

    total = con.execute(
        "SELECT COUNT(*) FROM queries"
    ).fetchone()[0]

    con.close()

    return render_template_string(
        ADMIN_PAGE,
        logged=True,
        results=results,
        total=total,
        search=search
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/admin")


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("=" * 50)
    print("🌍 GLOBAL TÜRK")
    print("=" * 50)
    print("Admin Key:", ADMIN_KEY)
    print("Port:", port)
    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
)
