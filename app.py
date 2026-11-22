import json
import math
import os
import urllib.request
import streamlit as st

st.set_page_config(page_title="Beyblade X Pro Meta System", page_icon="⚡", layout="wide")

# Inserisci qui l'URL "Raw" del tuo meta_live.json su GitHub
LIVE_META_URL = "https://raw.githubusercontent.com/TUO_UTENTE/beyblade-analyzer/main/meta_live.json"

DB_PATH = "beyblade_bx_db.json"
if not os.path.exists(DB_PATH):
    st.error(f"File database '{DB_PATH}' non trovato! Assicurati che sia nella stessa cartella di app.py.")
    st.stop()

with open(DB_PATH, "r", encoding="utf-8") as f:
    db = json.load(f)

COL_FILE = "mia_collezione.json"
CUSTOM_DB_FILE = "pezzi_custom.json"


def load_json_safe(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json_safe(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Caricamento pezzi aggiunti manualmente dall'utente
custom_parts = load_json_safe(CUSTOM_DB_FILE, {"bx_blades": [], "ux_blades": [], "ratchets": [], "bits": []})
for cat in ["bx_blades", "ux_blades", "ratchets", "bits"]:
    existing_names = {x["name"] for x in db.get(cat, [])}
    for item in custom_parts.get(cat, []):
        if item["name"] not in existing_names:
            db.setdefault(cat, []).append(item)


# Sincronizzazione automatica con meta_live.json su GitHub (cache 1 ora)
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_meta(url):
    if "TUO_UTENTE" in url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


live_data = fetch_live_meta(LIVE_META_URL)
if live_data:
    for cat_live, cat_db in [
        ("extra_bx_blades", "bx_blades"),
        ("extra_ux_blades", "ux_blades"),
        ("extra_ratchets", "ratchets"),
        ("extra_bits", "bits")
    ]:
        existing_names = {x["name"] for x in db.get(cat_db, [])}
        for item in live_data.get(cat_live, []):
            if item["name"] not in existing_names:
                db.setdefault(cat_db, []).append(item)


if "deck" not in st.session_state:
    st.session_state.deck = []

# ==============================================================================
# DIZIONARI META COMPETITIVI (WBO / GSI)
# ==============================================================================
META_BLADES = {
    "Wizard Rod": (24, "S+", "Distribuzione centrifuga (OWD) e forma circolare perfetta: re indiscusso dello Stamina."),
    "Phoenix Wing": (22, "S+", "Massa d'urto devastante e forma aerodinamica: top tier assoluto in Attack e Balance."),
    "Cobalt Dragoon": (21, "S+", "Rotazione sinistra (Left-Spin): domina in Spin-Equalization contro i destrorsi."),
    "Aero Pegasus": (22, "S+", "Compatto, pesantissimo e bilanciato: uno degli attaccanti più letali mai creati."),
    "Silver Wolf": (20, "S", "Anello libero rotante che assorbe gli impatti e prolunga la rotazione finale."),
    "Tyranno Beat": (19, "S", "Lame spesse e pesanti: eccelle sia in attacco puro che in assetti semi-difensivi."),
    "Impact Drake": (20, "S", "Inserti in gomma ad altissimo rinculo: capace di mandare KO anche i top tier."),
    "Shark Scale": (20, "S", "Evoluzione pesante e ribassata di Shark Edge: letale negli upper attack."),
    "Scorpio Spear": (19, "S", "Quasi 40g di peso con baricentro basso e grande stabilità."),
    "Clock Mirage": (18, "A+", "Ottima circonferenza per stamina pura, ma richiede Ratchet molto protettivi."),
    "Meteor Dragoon": (19, "S", "Left-Spin pesante con grande capacità di rubare rotazione e contrattaccare."),
    "Whale Wave": (17, "A+", "Molto pesante con ottimi smash attack dall'alto."),
    "Shark Edge": (16, "A+", "Re degli upper attack veloci, anche se più leggero rispetto ai nuovi pesi massimi."),
    "Dran Buster": (16, "A+", "Colpo singolo devastante (One-Hit KO), ma paga la scarsa stamina se manca il bersaglio."),
    "Knight Mail": (16, "A+", "Ottima difesa con sfere interne assorbi-urto."),
    "Samurai Saber": (16, "A+", "Lame mobili ad alta velocità di taglio."),
    "Cobalt Drake": (16, "A", "Buon peso e forma solida, superato però dalle versioni UX più recenti."),
    "Hells Scythe": (14, "A", "Grande classico bilanciato, ma oggi soffre la differenza di peso contro i Tier S."),
    "Unicorn Sting": (14, "A", "Buona versatilità tra difesa e contrattacco."),
    "Dran Sword": (13, "B+", "Ottimo attaccante base, ma ormai leggero rispetto al meta attuale."),
    "Dran Dagger": (13, "B+", "Buon attacco continuo multi-colpo."),
    "Hells Hammer": (12, "B", "Discreto smash attack, ma tende a perdere equilibrio facilmente."),
    "Leon Crest": (13, "B+", "Parete difensiva spessa, ma attrito elevato a fine rotazione."),
    "Golem Rock": (14, "A", "Compatto e basso, buon potenziale difensivo."),
    "Wyvern Hover": (15, "A", "Buona portanza e resistenza agli urti bassi."),
    "Tricera Press": (15, "A", "Massa notevole per assorbire colpi pesanti."),
    "Xeno Xcalibur": (14, "A", "Forte impatto frontale ma stamina limitata."),
    "Ghost Circle": (6, "C", "Troppo leggera (26.8g): viene sbalzata fuori dall'arena con facilità."),
    "Shinobi Shadow": (7, "C", "Estremamente leggera (28.5g): soffre qualsiasi impatto diretto."),
    "Dranzer": (4, "C", "Remake X-Over da collezione: peso troppo basso per il gioco competitivo."),
    "Driger": (5, "C", "Remake X-Over leggero: divertente ma non competitivo."),
    "Dragoon Storm": (3, "C", "Troppo leggero (25.4g) per reggere gli urti di Beyblade X."),
    "Draciel": (4, "C", "Remake X-Over da collezione.")
}

# Sovrascrive/aggiorna i Tier se meta_live.json è raggiungibile su GitHub
if live_data and "meta_blades" in live_data:
    for b_key, val_list in live_data["meta_blades"].items():
        if len(val_list) >= 3:
            META_BLADES[b_key] = (val_list[0], val_list[1], val_list[2])

META_BITS = {
    "Ball (B)": (14, "S+", "La punta Stamina per eccellenza: movimento fluido e massima durata."),
    "Free Ball (FB)": (14, "S+", "Rotazione libera della sfera: riduce l'attrito e massimizza lo Spin Finish."),
    "Rush (R)": (14, "S+", "Il miglior Bit Attack competitivo: Xtreme Dash controllati e alta stamina."),
    "Low Rush (LR)": (14, "S+", "Versione ribassata di Rush: letale per colpire sotto i Ratchet avversari."),
    "Elevate (E)": (14, "S+", "Indispensabile su Left-Spin (Cobalt Dragoon) per rubare rotazione (LAD)."),
    "Hexa (H)": (13, "S", "Stabilità eccezionale e resistenza al Burst altissima."),
    "Point (P)": (13, "S", "Perfetto equilibrio tra aggressività iniziale e resistenza al centro."),
    "Level (L)": (13, "S", "Ottima stabilità finale (LAD) e controllo degli Xtreme Dash."),
    "Low Flat (LF)": (12, "A+", "Ottimo per attacchi bassi e veloci."),
    "Under Flat (UF)": (12, "A+", "Assetto ultra-basso per massimizzare gli upper attack."),
    "Under Needle (UN)": (12, "A+", "Difesa molto bassa e difficile da scalzare."),
    "Glide (G)": (12, "A+", "Ottima scorrevolezza e controllo a fine rotazione."),
    "Orb (O)": (11, "A", "Simile a Ball ma con meno movimento perimetrale."),
    "Low Orb (LO)": (12, "A+", "Versione ribassata di Orb: ottima stabilità."),
    "Taper (T)": (11, "A", "Buon movimento aggressivo controllato."),
    "Unite (U)": (11, "A", "Versatile e stabile al centro."),
    "Kick (K)": (11, "A", "Buon compromesso tra attacco e controllo."),
    "Flat (F)": (10, "A", "Veloce ma tende ad auto-eliminarsi o perdere stamina presto."),
    "Gear Flat (GF)": (9, "B+", "Molto veloce sull'Xtreme Line ma difficile da controllare."),
    "Accel (A)": (10, "A", "Grande esplosività iniziale."),
    "Rubber Accel (RA)": (10, "A", "Grip altissimo ma perde stamina molto velocemente."),
    "Needle (N)": (7, "B", "Tende a inclinarsi e perdere equilibrio a fine giro."),
    "Spike (S)": (6, "C", "Punta troppo stretta: perde equilibrio e subisce facilmente KO."),
    "Quake (Q)": (4, "C", "Salta in modo imprevedibile: alto rischio di auto-KO.")
}

META_RATCHETS = {
    "9-60": (12, "S+", "Il miglior Ratchet del gioco: 9 micro-alette quasi impossibili da agganciare."),
    "3-60": (11, "S+", "Ottimo bilanciamento, basso e affidabile su quasi ogni combo."),
    "1-60": (11, "S+", "Sbilanciamento mirato per aumentare la potenza d'urto e uscire dalle tasche."),
    "5-60": (10, "S", "Ottimo peso e stabilità per combo Stamina e Balance."),
    "7-60": (10, "S", "Molto pesante e compatto, aumenta l'inerzia."),
    "0-60": (10, "S", "Profilo liscio e ribassato con ottimo anti-burst."),
    "6-60": (9, "A+", "Buona distribuzione del peso."),
    "1-50": (10, "S", "Altezza ultra-bassa (5mm) ideale per attaccanti puri."),
    "4-50": (8, "A", "Molto basso ma con 4 punte esposte."),
    "9-70": (9, "A+", "Ottima resistenza al burst per altezze medie."),
    "7-70": (8, "A", "Pesante ma leggermente più esposto."),
    "4-60": (6, "B", "I 4 spigoli sporgenti aumentano il rischio di Burst."),
    "2-60": (4, "C", "Due lame molto sporgenti: altissimo rischio di Burst."),
    "2-80": (2, "C", "Alto e con due lame enormi: esplode con facilità."),
    "4-80": (3, "C", "Troppo alto ed esposto agli attacchi bassi.")
}


# FIX: Riconoscimento intelligente dei nomi CamelCase del DB (es. "WizardRod" -> "Wizard Rod")
def normalize_name(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum())


def get_blade_meta(n: str):
    n_norm = normalize_name(n)
    for k, v in META_BLADES.items():
        if normalize_name(k) in n_norm:
            return v
    return (11, "B", "Blade standard senza vantaggi competitivi particolari.")


def get_bit_meta(n: str):
    return META_BITS.get(n, (9, "B", "Bit standard."))


def get_ratchet_meta(n: str):
    return META_RATCHETS.get(n, (7, "B", "Ratchet standard."))


def has_blade(blade_name: str, targets: list) -> bool:
    bn = normalize_name(blade_name)
    return any(normalize_name(t) in bn for t in targets)


# ==============================================================================
# GRAFICO RADAR SVG & CALCOLO STATISTICHE
# ==============================================================================
def radar_svg(stats: dict) -> str:
    labels = ["Attacco", "Difesa", "Stamina", "Peso", "Anti-Burst"]
    outer_pts = " ".join([
        f"{140 + 85 * math.cos(math.radians(-90 + i * 72)):.1f},{130 + 85 * math.sin(math.radians(-90 + i * 72)):.1f}"
        for i in range(5)
    ])
    inner_pts = " ".join([
        f"{140 + (85 * max(1, min(10, stats[l])) / 10.0) * math.cos(math.radians(-90 + i * 72)):.1f},{130 + (85 * max(1, min(10, stats[l])) / 10.0) * math.sin(math.radians(-90 + i * 72)):.1f}"
        for i, l in enumerate(labels)
    ])
    texts = "".join([
        f'<text x="{140 + 109 * math.cos(math.radians(-90 + i * 72)):.1f}" y="{130 + 103 * math.sin(math.radians(-90 + i * 72)):.1f}" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">{l} ({stats[l]})</text>'
        for i, l in enumerate(labels)
    ])
    return (
        f'<svg width="290" height="260" viewBox="0 0 290 260">'
        f'<polygon points="{outer_pts}" fill="#1e293b" stroke="#475569" stroke-width="1.5"/>'
        f'<polygon points="{inner_pts}" fill="rgba(56, 189, 248, 0.45)" stroke="#38bdf8" stroke-width="2.5"/>'
        f'{texts}</svg>'
    )


def calc_stats(b_name, b_type, bit_name, bit_type, w, burst_res, risk):
    bm_pts = get_blade_meta(b_name)[0]
    bonus_tier = 2 if bm_pts >= 20 else (1 if bm_pts >= 16 else 0)

    att = max(1, min(10, (8 if b_type == "Attack" else (5 if b_type == "Balance" else 3)) + (2 if bit_type == "Attack" else (1 if bit_type == "Balance" else -1)) + (bonus_tier if b_type == "Attack" else 0)))
    dfn = max(1, min(10, (8 if b_type == "Defense" else (5 if b_type == "Balance" else 3)) + (2 if bit_type == "Defense" else (1 if bit_type == "Balance" else -1)) + (bonus_tier if b_type == "Defense" else 0)))

    if (has_blade(b_name, ["Wizard Rod"]) and bit_type == "Stamina") or (has_blade(b_name, ["Cobalt Dragoon", "Meteor Dragoon"]) and ("Elevate" in bit_name or "Level" in bit_name)):
        sta = 10
    else:
        sta = max(1, min(10, (8 if b_type == "Stamina" else (5 if b_type == "Balance" else 3)) + (2 if bit_type == "Stamina" else (1 if bit_type == "Balance" else -1)) + (bonus_tier if b_type == "Stamina" else 0)))

    peso_stat = max(1, min(10, round((w - 37.5) * 1.1)))
    ab_stat = max(1, min(10, (8 if burst_res == "High" else 4) + (2 if risk == "Very Low" else (1 if risk == "Low" else (-2 if "High" in risk else 0)))))

    return {"Attacco": att, "Difesa": dfn, "Stamina": sta, "Peso": peso_stat, "Anti-Burst": ab_stat}


# ==============================================================================
# MOTORE DI VALUTAZIONE COMBO (BX / UX / CX / INFINITY)
# ==============================================================================
def valuta(blade, ratchet, bit):
    is_int = "Ratchet-Integrated" in bit["name"]
    w = round(blade["weight_g"] + (0 if is_int else ratchet["weight_g"]) + bit["weight_g"], 2)
    h = round((6.0 if is_int else ratchet["height_mm"]) + bit["height_mod"], 1)
    risk = "Very Low" if is_int else ratchet["burst_risk"]
    bm = get_blade_meta(blade["name"])
    bitm = get_bit_meta(bit["name"])
    rm = (12, "S+", "") if is_int else get_ratchet_meta(ratchet["name"])

    synergy_bonus = 0
    pros = [f"Blade Tier {bm[1]}: {bm[2]}"]

    if has_blade(blade["name"], ["Wizard Rod"]) and bit["name"] in ["Ball (B)", "Free Ball (FB)", "Hexa (H)", "Orb (O)", "Low Orb (LO)"]:
        synergy_bonus += 12
        pros.append("COMBO META S+ (Top 1-3 Mondiale): Dominio assoluto sullo Spin Finish e controllo centro.")
    elif has_blade(blade["name"], ["Cobalt Dragoon", "Meteor Dragoon"]) and bit["name"] in ["Elevate (E)", "Level (L)", "Glide (G)"]:
        synergy_bonus += 12
        pros.append("COMBO META S+ (Spin-Equalizer): Sfrutta la rotazione sinistra per rubare energia.")
    elif has_blade(blade["name"], ["Phoenix Wing", "Aero Pegasus", "Shark Scale", "Tyranno Beat", "Impact Drake"]) and bit["name"] in ["Rush (R)", "Low Rush (LR)", "Point (P)", "Low Flat (LF)", "Flat (F)", "Level (L)"]:
        synergy_bonus += 10
        pros.append("COMBO META S+: Potenza d'urto e velocità al vertice competitivo.")
    elif has_blade(blade["name"], ["Silver Wolf"]) and bit["name"] in ["Free Ball (FB)", "Ball (B)", "Hexa (H)"]:
        synergy_bonus += 10
        pros.append("COMBO META S: L'anello free-spin assorbe i colpi massimizzando la stamina.")

    if blade["type"] == bit["type"]:
        synergy_bonus += 6
        pros.append(f"Sinergia di stile ({blade['type']}).")
    elif blade["weight_g"] >= 37.5 and bit["type"] in ["Stamina", "Defense"]:
        synergy_bonus += 6
        pros.append("Assetto Ibrido Pesante: la massa stabilizza la punta.")

    if not is_int and bit["burst_res"] == "Low" and risk == "Very Low":
        synergy_bonus += 6
        pros.append(f"Protezione Burst ottimale con {ratchet['name']}.")

    penalties = 0
    cons = []
    if not is_int and bit["burst_res"] == "Low" and risk in ["High", "Very High"]:
        penalties += 18
        cons.append(f"RISCHIO BURST ALTO: {bit['name']} + {ratchet['name']}.")
    if not is_int and h >= 8.0:
        penalties += 8
        cons.append(f"Baricentro alto ({h}mm): rischio sbilanciamento.")
    if w < 40.0:
        penalties += 10
        cons.append(f"Peso molto basso ({w}g): viene facilmente sbalzato.")

    score = max(0, min(100, 32 + bm[0] + bitm[0] + rm[0] + synergy_bonus - penalties))
    return score, w, h, pros, cons, calc_stats(blade["name"], blade["type"], bit["name"], bit["type"], w, bit["burst_res"], risk)


def valuta_ux_inf(u, bit):
    w = round(u["weight_g"] + bit["weight_g"], 2)
    h = round(u["height_mm"] + bit["height_mod"], 1)
    score = max(0, min(100, 56 + get_bit_meta(bit["name"])[0] + (8 if u["type"] == bit["type"] else 0) + (6 if w >= 46.5 else 0) - (8 if h >= 8.0 else 0)))
    pros = ["UX Infinity (Ratchet Integrato): zero gioco meccanico e basso rischio Burst."]
    if u["type"] == bit["type"]:
        pros.append(f"Sinergia pura ({u['type']}).")
    if w >= 46.5:
        pros.append(f"Peso elevato ({w}g).")
    cons = [f"Baricentro alto ({h}mm)."] if h >= 8.0 else []
    return score, w, h, pros, cons, calc_stats(u["name"], u["type"], bit["name"], bit["type"], w, bit.get("burst_res", "High"), "Very Low")


def valuta_cx(lk, mb, ov, ab, r, bit, is_6):
    is_i = "Ratchet-Integrated" in bit["name"]
    w = round(lk["weight_g"] + mb["weight_g"] + (ov["weight_g"] if is_6 else 0.0) + ab["weight_g"] + (0 if is_i else r["weight_g"]) + bit["weight_g"], 2)
    h = round((6.0 if is_i else r["height_mm"]) + ab.get("height_mod", 0.0) + bit["height_mod"], 1)
    risk = "Low" if is_i else r["burst_risk"]

    score = max(0, min(100, 46 + get_bit_meta(bit["name"])[0] + (12 if is_i else get_ratchet_meta(r["name"])[0]) + (8 if lk["weight_g"] >= 4.5 else 0) + (8 if mb["type"] == bit["type"] else 0) + (8 if w >= 47.0 else 0) - (10 if h >= 8.0 else 0) - (16 if not is_i and bit["burst_res"] == "Low" and risk in ["High", "Very High"] else 0)))
    pros = []
    if lk["weight_g"] >= 4.5:
        pros.append("Metal Lock Chip: aumenta il peso centrale.")
    if mb["type"] == bit["type"]:
        pros.append(f"Coerenza di stile ({mb['type']}).")
    if w >= 47.0:
        pros.append(f"Peso elevato ({w}g): grande inerzia.")

    cons = []
    if h >= 8.0:
        cons.append(f"Assetto alto ({h}mm): espone il Ratchet.")
    if not is_i and bit["burst_res"] == "Low" and risk in ["High", "Very High"]:
        cons.append(f"RISCHIO BURST ALTO: {bit['name']} + {r['name']}.")

    return score, w, h, pros, cons, calc_stats(mb["name"], mb["type"], bit["name"], bit["type"], w, bit["burst_res"], risk)


# ==============================================================================
# INTERFACCIA UTENTE & SELETTORI UNIVERSALI
# ==============================================================================
st.title("⚡ Beyblade X - Pro Meta System & Arena 1vs1")
if live_data:
    st.caption(f"🟢 Meta Live Sincronizzato: **{live_data.get('versione', 'WBO/GSI Active')}**")
else:
    st.caption("🟡 Modalità Locale (Database Offline attivo — configura `LIVE_META_URL` per gli aggiornamenti automatici)")

t1, t2, t3, t4, t5, t6 = st.tabs([
    "🔍 Analizzatore & Radar",
    "⚔️ Simulatore 1vs1",
    "🤖 Suggeritore Top Combo",
    f"🏆 Deck Torneo ({len(st.session_state.deck)}/3)",
    "📦 La Mia Collezione",
    "🔄 Meta Live & Nuovi Pezzi"
])

col_data = load_json_safe(COL_FILE, {
    "blades": [], "ratchets": [], "bits": [],
    "cx_locks": [], "cx_mains": [], "cx_metals": [], "cx_overs": [], "cx_assists": []
})


def filtra(lista, cat, attivo):
    if attivo and col_data.get(cat, []):
        filtrata = [x for x in lista if x["name"] in col_data.get(cat, [])]
        return filtrata if filtrata else lista
    return lista


def selettore_std(cont, pref, lin, usa_col):
    mappa = {"1. BX": db["bx_blades"], "2. UX": db["ux_blades"], "4. BX Infinity": db.get("bx_infinity", db["bx_blades"])}
    b = cont.selectbox("Blade", filtra(mappa[lin], "blades", usa_col), key=f"{pref}_b_{lin}", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]")
    bit = cont.selectbox("Bit", filtra(db["bits"], "bits", usa_col), key=f"{pref}_bit_{lin}", format_func=lambda x: f"{x['name']} ({x['type']})")
    is_i = "Ratchet-Integrated" in bit["name"]
    r = cont.selectbox("Ratchet", filtra(db["ratchets"], "ratchets", usa_col), key=f"{pref}_r_{lin}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)", disabled=is_i)
    nome = f"{b['name']} {'' if is_i else r['name'] + ' '}{bit['name']}"
    pezzi = [b["name"], bit["name"]] if is_i else [b["name"], r["name"], bit["name"]]
    return nome, *valuta(b, r, bit), pezzi, b["type"]


def selettore_ux_inf(cont, pref, usa_col):
    u = cont.selectbox("Blade UX Infinity", filtra(db["ux_infinity"], "blades", usa_col), key=f"{pref}_u", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
    bits_no_int = [x for x in db["bits"] if "Ratchet-Integrated" not in x["name"]]
    bit = cont.selectbox("Bit", filtra(bits_no_int, "bits", usa_col), key=f"{pref}_ubit", format_func=lambda x: f"{x['name']} ({x['type']})")
    return f"{u['name']} + {bit['name']}", *valuta_ux_inf(u, bit), [u["name"], bit["name"]], u["type"]


def selettore_cx(cont, pref, is_6, usa_col):
    tag = "cx6" if is_6 else "cx5"
    lk = cont.selectbox("Lock Chip", filtra(db["cx_lock_chips"], "cx_locks", usa_col), key=f"{pref}_lk_{tag}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
    mb = cont.selectbox("Metal Blade" if is_6 else "Main Blade", filtra(db["cx_metal_blades"] if is_6 else db["cx_main_blades"], "cx_metals" if is_6 else "cx_mains", usa_col), key=f"{pref}_mb_{tag}", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]")
    ov = cont.selectbox("Over Blade", filtra(db["cx_over_blades"], "cx_overs", usa_col), key=f"{pref}_ov_{tag}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)") if is_6 else {"name": "", "weight_g": 0.0}
    ab = cont.selectbox("Assist Blade", filtra(db["cx_assist_blades"], "cx_assists", usa_col), key=f"{pref}_ab_{tag}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
    bit = cont.selectbox("Bit", filtra(db["bits"], "bits", usa_col), key=f"{pref}_cbit_{tag}", format_func=lambda x: f"{x['name']} ({x['type']})")
    is_i = "Ratchet-Integrated" in bit["name"]
    r = cont.selectbox("Ratchet", filtra(db["ratchets"], "ratchets", usa_col), key=f"{pref}_cr_{tag}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)", disabled=is_i)
    ov_part = f" + {ov['name']}" if is_6 else ""
    r_part = "" if is_i else f"{r['name']} "
    nome = f"{mb['name']} [{lk['name']}{ov_part} + {ab['name']}] {r_part}{bit['name']}"
    pezzi = [lk["name"], mb["name"], ab["name"], bit["name"]] + ([ov["name"]] if is_6 else []) + ([] if is_i else [r["name"]])
    return nome, *valuta_cx(lk, mb, ov, ab, r, bit, is_6), pezzi, mb["type"]


def selettore_bey(cont, pref, lin, usa_col):
    if lin in ["1. BX", "2. UX", "4. BX Infinity"]:
        return selettore_std(cont, pref, lin, usa_col)
    elif lin == "5. UX Infinity":
        return selettore_ux_inf(cont, pref, usa_col)
    return selettore_cx(cont, pref, lin == "6. CX Infinity (6 Pezzi)", usa_col)


# ==============================================================================
# TAB 1: ANALIZZATORE & RADAR
# ==============================================================================
with t1:
    solo_mia_col = st.checkbox("Filtra menu usando solo i pezzi della Mia Collezione", value=False)
    linea = st.radio("Linea:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], horizontal=True)
    nome, sc, w, h, pros, cons, st_rad, pezzi_usati, _ = selettore_bey(t1, "t1", linea, solo_mia_col)

    st.subheader(f"Combo: {nome}")
    col_sx, col_dx = st.columns([1.4, 1])
    m1, m2, m3 = col_sx.columns(3)
    m1.metric("Voto Meta", f"{sc} / 100")
    m2.metric("Peso", f"{w} g")
    m3.metric("Altezza", f"{h} mm")

    cp, cc = col_sx.columns(2)
    cp.markdown("### ✅ Pro")
    if pros:
        for p in pros:
            cp.success(p)
    else:
        cp.info("Bilanciata.")

    cc.markdown("### ⚠️ Contro")
    if cons:
        for c in cons:
            cc.error(c)
    else:
        cc.success("Nessun difetto grave!")

    col_dx.markdown("### 📊 Radar Statistiche")
    col_dx.markdown(radar_svg(st_rad), unsafe_allow_html=True)

    if col_sx.button("➕ Aggiungi questa Combo al Deck Torneo"):
        if len(st.session_state.deck) < 3:
            st.session_state.deck.append({"nome": nome, "voto": sc, "peso": w, "pezzi": pezzi_usati})
            st.rerun()
        else:
            col_sx.warning("Il Deck ha già 3 Beyblade! Vai nella scheda Deck Torneo per rimuoverne uno.")

# ==============================================================================
# TAB 2: SIMULATORE 1VS1
# ==============================================================================
with t2:
    st.subheader("⚔️ Confronto Testa a Testa Universale (BX / UX / CX / Infinity)")
    s1, s2 = st.columns(2)
    s1.markdown("### 🔵 Blader 1")
    lin1 = s1.selectbox("Linea Blader 1:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], index=1, key="lin1")
    nome1, sc1, w1, h1, _, _, st1, _, tp1 = selettore_bey(s1, "p1", lin1, False)

    s2.markdown("### 🔴 Blader 2")
    lin2 = s2.selectbox("Linea Blader 2:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], index=0, key="lin2")
    nome2, sc2, w2, h2, _, _, st2, _, tp2 = selettore_bey(s2, "p2", lin2, False)

    p1_pts = (sc1 ** 1.35) + (w1 - w2) * 4.0 + (35 if ("Left-Spin" in nome1 and "Left-Spin" not in nome2 and ("Elevate" in nome1 or "Level" in nome1)) else 0) + (25 if (tp1 == "Attack" and tp2 == "Stamina") or (tp1 == "Stamina" and tp2 == "Defense") or (tp1 == "Defense" and tp2 == "Attack") else 0)
    p2_pts = (sc2 ** 1.35) + (w2 - w1) * 4.0 + (35 if ("Left-Spin" in nome2 and "Left-Spin" not in nome1 and ("Elevate" in nome2 or "Level" in nome2)) else 0) + (25 if (tp2 == "Attack" and tp1 == "Stamina") or (tp2 == "Stamina" and tp1 == "Defense") or (tp2 == "Defense" and tp1 == "Attack") else 0)

    prob1 = max(8, min(92, round((p1_pts / max(1, p1_pts + p2_pts)) * 100)))
    prob2 = 100 - prob1

    st.divider()
    res_c1, res_c2, res_c3 = st.columns(3)
    res_c1.metric(f"🔵 {nome1}", f"{prob1}% Vittoria", f"{w1}g | Voto Meta {sc1}")
    res_c2.metric("Differenza Peso", f"{round(abs(w1 - w2), 2)} g", f"Vantaggio {'Blader 1' if w1 >= w2 else 'Blader 2'}")
    res_c3.metric(f"🔴 {nome2}", f"{prob2}% Vittoria", f"{w2}g | Voto Meta {sc2}")

    win_n, win_st, lose_h, lose_st = (nome1, st1, h2, st2) if prob1 >= prob2 else (nome2, st2, h1, st1)
    if win_st["Stamina"] >= 9:
        cond_win = "Spin Finish (1 pt) per resistenza e OWD superiore"
    elif win_st["Attacco"] >= 8:
        cond_win = "Xtreme / Over Finish (2-3 pt) per impatto pesante"
    elif lose_h >= 7.5 or lose_st["Anti-Burst"] <= 4:
        cond_win = "Burst Finish (2 pt) su Ratchet esposto"
    else:
        cond_win = "Spin Finish (1 pt) per controllo del centro"

    st.success(f"Pronostico Arena: Favorito {'Blader 1' if prob1 >= prob2 else 'Blader 2'} ({win_n}) — Esito più probabile: {cond_win}.")

# ==============================================================================
# TAB 3: SUGGERITORE TOP 5 COMBO
# ==============================================================================
with t3:
    usa_col_sug = st.checkbox("Usa solo pezzi della Mia Collezione per i suggerimenti", value=False)
    lin_sug = st.radio("Seleziona la Linea da ottimizzare:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], horizontal=True)

    bits_1v1 = [x for x in db["bits"] if "Ratchet-Integrated" not in x["name"]]
    r_pool = filtra(db["ratchets"], "ratchets", usa_col_sug)
    b_pool = filtra(bits_1v1, "bits", usa_col_sug)
    mappa_s = {"1. BX": db["bx_blades"], "2. UX": db["ux_blades"], "4. BX Infinity": db.get("bx_infinity", db["bx_blades"])}

    tb = st.selectbox("Blade da ottimizzare:", filtra(mappa_s.get(lin_sug, db["bx_blades"]), "blades", usa_col_sug), key=f"sug_b_{lin_sug}", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]") if lin_sug in ["1. BX", "2. UX", "4. BX Infinity"] else None
    tu = st.selectbox("Blade UX Infinity da ottimizzare:", filtra(db["ux_infinity"], "blades", usa_col_sug), key="sug_u", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]") if lin_sug == "5. UX Infinity" else None

    is_6_s = (lin_sug == "6. CX Infinity (6 Pezzi)")
    if lin_sug in ["3. CX (5 Pezzi)", "6. CX Infinity (6 Pezzi)"]:
        sc1_c, sc2_c, sc3_c = st.columns(3)
        tlk = sc1_c.selectbox("Lock Chip:", filtra(db["cx_lock_chips"], "cx_locks", usa_col_sug), key=f"sug_lk_{lin_sug}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
        tmb = sc2_c.selectbox("Metal Blade:" if is_6_s else "Main Blade:", filtra(db["cx_metal_blades"] if is_6_s else db["cx_main_blades"], "cx_metals" if is_6_s else "cx_mains", usa_col_sug), key=f"sug_mb_{lin_sug}", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]")
        tov = sc3_c.selectbox("Over Blade:", filtra(db["cx_over_blades"], "cx_overs", usa_col_sug), key=f"sug_ov_{lin_sug}", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)") if is_6_s else {"name": "", "weight_g": 0.0}
    else:
        tlk, tmb, tov = None, None, {"name": "", "weight_g": 0.0}

    ab_pool = filtra(db["cx_assist_blades"], "cx_assists", usa_col_sug)
    ov_t = f" + {tov['name']}" if is_6_s else ""

    if st.button("🚀 Calcola Top 5 Combo"):
        if tb:
            res_sug = sorted([(valuta(tb, r, b), f"{tb['name']} {r['name']} {b['name']}") for r in r_pool for b in b_pool], key=lambda x: x[0][0], reverse=True)
        elif tu:
            res_sug = sorted([(valuta_ux_inf(tu, b), f"{tu['name']} + {b['name']}") for b in b_pool], key=lambda x: x[0][0], reverse=True)
        elif tlk:
            res_sug = sorted([(valuta_cx(tlk, tmb, tov, ab, r, b, is_6_s), f"{tmb['name']} [{tlk['name']}{ov_t} + {ab['name']}] {r['name']} {b['name']}") for ab in ab_pool for r in r_pool for b in b_pool], key=lambda x: x[0][0], reverse=True)
        else:
            res_sug = []

        for i, (v, c_name) in enumerate(res_sug[:5], 1):
            st.info(
                f"#{i} — **{c_name}** | Voto Meta: **{v[0]}/100** | Peso: **{v[1]}g** | Altezza: **{v[2]}mm**\n\n"
                f"✅ {' • '.join(v[3]) if v[3] else 'Bilanciata'}\n\n"
                f"⚠️ {' • '.join(v[4]) if v[4] else 'Nessun rischio'}"
            )

# ==============================================================================
# TAB 4: DECK TORNEO 3ON3
# ==============================================================================
with t4:
    st.subheader("🏆 Il tuo Deck da 3 Beyblade (Regolamento 3on3)")
    if not st.session_state.deck:
        st.info("Il tuo Deck è vuoto. Costruisci una combo nella prima scheda e clicca su '➕ Aggiungi questa Combo al Deck Torneo'.")
    else:
        tutti_pezzi_deck = [p for item in st.session_state.deck for p in item["pezzi"]]
        duplicati = set([p for p in tutti_pezzi_deck if tutti_pezzi_deck.count(p) > 1])

        if duplicati:
            st.error(f"⛔ DECK NON VALIDO DA TORNEO! Hai inserito pezzi duplicati: {', '.join(duplicati)}")
        else:
            st.success("✅ DECK VALIDO DA TORNEO: Nessun pezzo ripetuto tra i Beyblade!")

        st.metric("Media Competitiva del Deck", f"{round(sum(x['voto'] for x in st.session_state.deck) / len(st.session_state.deck), 1)} / 100")

        for i, it in enumerate(st.session_state.deck):
            cd1, cd2 = st.columns([5, 1])
            cd1.write(f"**Bey #{i+1}:** {it['nome']} — Voto Meta: **{it['voto']}/100** ({it['peso']}g)")
            if cd2.button("🗑️ Rimuovi", key=f"rem_deck_{i}"):
                st.session_state.deck.pop(i)
                st.rerun()

        st.divider()
        if st.button("🗑️ Svuota tutto il Deck"):
            st.session_state.deck.clear()
            st.rerun()

# ==============================================================================
# TAB 5: LA MIA COLLEZIONE
# ==============================================================================
# TAB 5: LA MIA COLLEZIONE & BACKUP
# ==============================================================================
with t5:
    st.subheader("📦 Gestisci i pezzi che possiedi fisicamente (Tutte le Linee)")
    all_b_names = [x["name"] for x in db["bx_blades"] + db["ux_blades"] + db.get("bx_infinity", []) + db["ux_infinity"]]
    all_r_names = [x["name"] for x in db["ratchets"]]
    all_bit_names = [x["name"] for x in db["bits"]]
    all_lk = [x["name"] for x in db["cx_lock_chips"]]
    all_mb = [x["name"] for x in db["cx_main_blades"]]
    all_mt = [x["name"] for x in db["cx_metal_blades"]]
    all_ov = [x["name"] for x in db["cx_over_blades"]]
    all_ab = [x["name"] for x in db["cx_assist_blades"]]

    sel_b = st.multiselect("Blade (BX / UX / Infinity):", all_b_names, default=[x for x in col_data.get("blades", []) if x in all_b_names])
    sel_r = st.multiselect("Ratchet:", all_r_names, default=[x for x in col_data.get("ratchets", []) if x in all_r_names])
    sel_bit = st.multiselect("Bit:", all_bit_names, default=[x for x in col_data.get("bits", []) if x in all_bit_names])

    c_cx1, c_cx2 = st.columns(2)
    sel_lk = c_cx1.multiselect("CX Lock Chips:", all_lk, default=[x for x in col_data.get("cx_locks", []) if x in all_lk])
    sel_mb = c_cx1.multiselect("CX Main Blades:", all_mb, default=[x for x in col_data.get("cx_mains", []) if x in all_mb])
    sel_mt = c_cx1.multiselect("CX Infinity Metal Blades:", all_mt, default=[x for x in col_data.get("cx_metals", []) if x in all_mt])
    sel_ov = c_cx2.multiselect("CX Infinity Over Blades:", all_ov, default=[x for x in col_data.get("cx_overs", []) if x in all_ov])
    sel_ab = c_cx2.multiselect("CX Assist Blades:", all_ab, default=[x for x in col_data.get("cx_assists", []) if x in all_ab])

    col_payload = {
        "blades": sel_b, "ratchets": sel_r, "bits": sel_bit,
        "cx_locks": sel_lk, "cx_mains": sel_mb, "cx_metals": sel_mt,
        "cx_overs": sel_ov, "cx_assists": sel_ab
    }

    c_btn1, c_btn2 = st.columns(2)
    if c_btn1.button("💾 Salva la Mia Collezione Completa"):
        save_json_safe(COL_FILE, col_payload)
        st.success("Collezione completa salvata! Ora il filtro funziona su tutte le linee (BX, UX, CX e Infinity).")

    c_btn2.download_button(
        label="⬇️ Scarica Backup Collezione (PC / Smartphone)",
        data=json.dumps(col_payload, ensure_ascii=False, indent=2),
        file_name="mia_collezione.json",
        mime="application/json"
    )

    st.divider()
    st.markdown("### ⬆️ Ripristina Collezione da Backup")
    up_col = st.file_uploader("Carica il tuo file `mia_collezione.json` salvato in precedenza:", type=["json"])
    if up_col is not None:
        try:
            restored_data = json.load(up_col)
            save_json_safe(COL_FILE, restored_data)
            st.success("✅ Backup ripristinato con successo! Ricarica la pagina (F5) per aggiornare i menu.")
        except Exception as e:
            st.error(f"Errore nel caricamento del file JSON: {e}")

# ==============================================================================
# TAB 6: AGGIORNAMENTO META LIVE & AGGIUNTA PEZZI AL VOLO
# ==============================================================================
with t6:
    st.subheader("🔄 Aggiornamento Automatico Meta Live (GitHub)")
    st.write("L'app controlla ogni ora il file `meta_live.json` sul tuo repository GitHub per aggiornare i punteggi WBO/GSI e aggiungere nuovi pezzi.")
    if st.button("🔄 Forza Sincronizzazione Meta Live Adesso"):
        fetch_live_meta.clear()
        st.rerun()

    st.divider()
    st.subheader("➕ Aggiungi al volo un nuovo componente appena uscito")
    uc1, uc2, uc3, uc4 = st.columns(4)
    new_cat = uc1.selectbox("Categoria:", ["bx_blades", "ux_blades", "ratchets", "bits"])
    new_name = uc2.text_input("Nome Pezzo (es. New Dragon):")
    new_type = uc3.selectbox("Tipo:", ["Attack", "Defense", "Stamina", "Balance"])
    new_weight = uc4.number_input("Peso (g):", min_value=1.0, max_value=60.0, value=36.0, step=0.1)

    if st.button("➕ Aggiungi al Database"):
        if new_name.strip():
            clean_name = new_name.strip()
            if "blades" in new_cat:
                new_obj = {"name": clean_name, "type": new_type, "weight_g": new_weight}
            elif new_cat == "ratchets":
                new_obj = {"name": clean_name, "height_mm": 6.0, "weight_g": new_weight, "burst_risk": "Low"}
            else:
                new_obj = {"name": clean_name, "type": new_type, "weight_g": new_weight, "burst_res": "High", "height_mod": 0.0}

            custom_parts.setdefault(new_cat, []).append(new_obj)
            save_json_safe(CUSTOM_DB_FILE, custom_parts)
            st.success(f"✅ Aggiunto **{clean_name}**! Ricarica la pagina per vederlo nei menu.")
        else:
            st.warning("Inserisci il nome del componente prima di aggiungerlo.")
