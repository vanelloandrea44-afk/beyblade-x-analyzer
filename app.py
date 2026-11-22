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

# Profilo fisico/geometrico delle Blade: (forma_label, bonus_att, bonus_def, bonus_sta, desc_forma)
BLADE_SHAPES = {
    "Wizard Rod": ("Circolare OWD", 0, 1, 3, "Massa perimetrale continua (OWD): massima inerzia rotazionale."),
    "Clock Mirage": ("Circolare Stamina", 0, 1, 3, "Profilo tondo a basso attrito aerodinamico."),
    "Silver Wolf": ("Circolare Free-Spin", 0, 2, 3, "Anello esterno rotante che dissipa gli urti tangenziali."),
    "Phoenix Wing": ("Smash Aerodinamico", 3, 1, 0, "3 lame pesanti inclinate per colpi d'urto ad alta energia."),
    "Aero Pegasus": ("Compatta Bilanciata", 3, 1, 1, "Geometria compatta ad altissima densità per Xtreme Dash."),
    "Shark Edge": ("Upper Sloped", 3, 0, 0, "Lame inclinate verso l'alto per sollevare e mandare KO l'avversario."),
    "Shark Scale": ("Upper Ribassato", 3, 0, 0, "Profilo a cuneo basso progettato per colpire sotto i Ratchet."),
    "Dran Buster": ("Lama Singola Impatto", 4, 0, -1, "Concentrazione asimmetrica della massa per colpo singolo KO."),
    "Impact Drake": ("Lame Gomma Rinculo", 3, 1, -1, "Inserti in gomma ad alto attrito: massimo rinculo in impatto."),
    "Tyranno Beat": ("Smash Spesso", 2, 2, 0, "Lame spesse multi-impatto con ottima tenuta alle collisioni."),
    "Scorpio Spear": ("Baricentro Basso", 1, 2, 2, "Profilo largo e ribassato ad altissima stabilità."),
    "Cobalt Dragoon": ("Lame Left-Spin", 2, 0, 2, "Geometria sinistrorsa ottimizzata per Spin-Equalization."),
    "Meteor Dragoon": ("Lame Left-Spin Pesanti", 3, 0, 1, "Profilo sinistrorso massiccio per contrattacco e ruba-rotazione."),
    "Knight Mail": ("Parete Assorbi-Urto", 0, 3, 1, "Scudo perimetrale chiuso con sfere interne anti-rinculo."),
    "Leon Crest": ("Parete Difensiva Spessa", 0, 3, 0, "Muraglia spessa a 7 lati per respingere gli attacchi frontali."),
    "Golem Rock": ("Compatta Bassa", 1, 3, 0, "Profilo basso e raccolto difficile da agganciare."),
    "Whale Wave": ("Smash Verticale", 3, 1, 0, "Lame massicce che schiacciano l'avversario dall'alto."),
    "Samurai Saber": ("Lame Mobili Taglio", 2, 0, 1, "Alette estensibili che aumentano il raggio d'impatto."),
    "Hells Scythe": ("Bilanciata Circolare", 1, 1, 2, "Forma armonica versatile tra difesa perimetrale e stamina."),
    "Unicorn Sting": ("Asimmetrica Ibrida", 1, 2, 1, "Metà liscia difensiva e metà dentata per contrattacco."),
    "Ghost Circle": ("Circolare Ultra-Leggera", -1, -1, 1, "Forma tonda ma massa insufficiente per reggere urti pesanti."),
    "Shinobi Shadow": ("Compatta Ultra-Leggera", -1, 0, 0, "Profilo stretto ma peso troppo ridotto in collisione.")
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

# ==============================================================================
# FISICA E GEOMETRIA DELLE BLADE (Forma, OWD, Upper, Smash, Rinculo)
# ==============================================================================
BLADE_SHAPES = {
    "Wizard Rod": ("Circolare OWD", 1, 10, 4, "Massa periferica (OWD) e profilo tondo continuo: massima inerzia rotazionale."),
    "Clock Mirage": ("Circolare OWD", 1, 9, 4, "Circonferenza ampia ad altissima stamina, ma vulnerabile se colpita sotto."),
    "Silver Wolf": ("Circolare Free-Spin", 2, 9, 7, "Anello esterno libero che dissipa gli urti e preserva la rotazione."),
    "Phoenix Wing": ("Smash Aerodinamico", 9, 5, 5, "3 lame pesanti inclinate per sbalzare l'avversario fuori dall'arena."),
    "Aero Pegasus": ("Smash Compatto", 9, 5, 6, "Profilo compatto ad altissima densità: trasferimento d'energia esplosivo."),
    "Cobalt Dragoon": ("Lame Left-Spin", 8, 8, 5, "Lame destrorse/sinistrorse ottimizzate per agganciare e rubare spin (LAD)."),
    "Meteor Dragoon": ("Lame Left-Spin", 8, 8, 6, "Massa pesante in rotazione sinistra con forte contraccolpo."),
    "Shark Edge": ("Upper Ribassato", 9, 2, 3, "Lame scavate dal basso: progettata per infilarsi sotto il Ratchet e fare Burst/Over."),
    "Shark Scale": ("Upper Ribassato", 10, 3, 4, "Evoluzione pesante e ultra-bassa: devasta i Ratchet esposti."),
    "Dran Buster": ("One-Hit Eccentrico", 10, 1, 2, "Punta singola sbilanciata: massima potenza d'urto iniziale ma crollo di stamina."),
    "Impact Drake": ("Lame Gomma / Rinculo", 10, 3, 4, "Inserti in gomma ad altissimo grip: genera rimbalzi violentissimi."),
    "Tyranno Beat": ("Smash Pesante", 8, 5, 7, "Lame spesse a doppio impatto: eccelle negli scontri pesanti."),
    "Scorpio Spear": ("Lancia Bilanciata", 7, 6, 7, "Baricentro basso e quasi 40g di peso per stabilità e contrattacco."),
    "Whale Wave": ("Smash Verticale", 8, 4, 5, "Profilo alto che schiaccia verso il basso gli avversari."),
    "Knight Mail": ("Parete Assorbi-Urto", 3, 6, 9, "Scudo perimetrale con sfere interne che smorzano i colpi."),
    "Leon Crest": ("Parete Difensiva", 2, 4, 9, "Muro spesso a 7 lobi per bloccare gli attaccanti."),
    "Golem Rock": ("Compatto Ribassato", 4, 5, 8, "Basso e compatto, devia i colpi rasoterra."),
    "Tricera Press": ("Massa Difensiva", 4, 5, 8, "Profilo pesante progettato per assorbire l'impatto senza spostarsi."),
    "Hells Scythe": ("Lame Bilanciate", 5, 7, 5, "Profilo classico versatile con buon equilibrio tra attacco e stamina."),
    "Unicorn Sting": ("Asimmetrico Misto", 5, 6, 6, "Metà liscia per deviare e metà dentata per contrattaccare."),
    "Samurai Saber": ("Lame Taglienti", 8, 5, 4, "Lame mobili che aumentano la velocità di taglio negli Xtreme Dash."),
    "Dran Sword": ("Lame Agganciate", 7, 3, 4, "3 lame classiche per Xtreme Dash rapidi."),
    "Dran Dagger": ("Multi-Lama", 7, 4, 4, "6 piccole lame per colpi ripetuti a raffica."),
}


# FIX: Riconoscimento intelligente dei nomi CamelCase del DB (es. "WizardRod" -> "Wizard Rod")
def normalize_name(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum())


def has_blade(n: str, targets: list) -> bool:
    n_norm = normalize_name(n)
    return any(normalize_name(t) in n_norm for t in targets)


def get_blade_meta(n: str):
    n_norm = normalize_name(n)
    for k, v in META_BLADES.items():
        if normalize_name(k) in n_norm:
            return v
    return (11, "B", "Blade standard senza vantaggi competitivi particolari.")


def get_blade_shape(n: str, b_type: str = "Balance"):
    n_norm = normalize_name(n)
    for k, v in BLADE_SHAPES.items():
        if normalize_name(k) in n_norm:
            return v
    defaults = {
        "Attack": ("Lame Angolate Attack", 7, 3, 4, "Profilo spigoloso orientato all'impatto offensivo."),
        "Defense": ("Scudo Perimetrale", 3, 8, 6, "Bordo chiuso progettato per deviare i colpi."),
        "Stamina": ("Profilo Circolare", 2, 5, 8, "Geometria regolare per preservare la rotazione."),
        "Balance": ("Profilo Ibrido", 5, 5, 5, "Geometria mista tra spinta e stabilità.")
    }
    return defaults.get(b_type, ("Standard", 5, 5, 5, "Geometria bilanciata standard."))


def get_bit_meta(n: str):
    return META_BITS.get(n, (9, "B", "Bit standard."))


def get_ratchet_meta(n: str):
    return META_RATCHETS.get(n, (7, "B", "Ratchet standard."))


def calc_stats(b_name, b_type, bit_name, bit_type, w, burst_res, risk, h=6.0):
    bm_pts = get_blade_meta(b_name)[0]
    shape_name, sh_att, sh_def, sh_sta, _ = get_blade_shape(b_name, b_type)
    bonus_tier = 2 if bm_pts >= 20 else (1 if bm_pts >= 16 else 0)

    # Bonus altezza per forme Upper (es. Shark Edge/Scale su assetti bassi <= 6.0mm)
    upper_h_bonus = 1 if ("Upper" in shape_name and h <= 6.0) else 0

    raw_att = ((8 if b_type == "Attack" else (5 if b_type == "Balance" else 3)) * 0.55) + (sh_att * 0.45) + (2 if bit_type == "Attack" else (1 if bit_type == "Balance" else -1)) + bonus_tier * 0.5 + upper_h_bonus
    raw_dfn = ((8 if b_type == "Defense" else (5 if b_type == "Balance" else 3)) * 0.55) + (sh_def * 0.45) + (2 if bit_type == "Defense" else (1 if bit_type == "Balance" else -1)) + bonus_tier * 0.5

    if (has_blade(b_name, ["Wizard Rod"]) and bit_type == "Stamina") or (has_blade(b_name, ["Cobalt Dragoon", "Meteor Dragoon"]) and ("Elevate" in bit_name or "Level" in bit_name)):
        sta = 10
    else:
        raw_sta = ((8 if b_type == "Stamina" else (5 if b_type == "Balance" else 3)) * 0.5) + (sh_sta * 0.5) + (2 if bit_type == "Stamina" else (1 if bit_type == "Balance" else -1)) + bonus_tier * 0.5
        sta = max(1, min(10, round(raw_sta)))

    att = max(1, min(10, round(raw_att)))
    dfn = max(1, min(10, round(raw_dfn)))
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
    shape_name, sh_att, sh_def, sh_sta, shape_desc = get_blade_shape(blade["name"], blade["type"])

    synergy_bonus = 0
    pros = [
        f"Blade Tier {bm[1]}: {bm[2]}",
        f"Geometria [{shape_name}]: {shape_desc}"
    ]

    # Valutazione fisica del peso reale della Blade
    if blade["weight_g"] >= 38.0:
        synergy_bonus += 4
        pros.append(f"Massa Pesante ({blade['weight_g']}g): elevata inerzia negli scontri fisici.")
    elif blade["weight_g"] < 31.5:
        synergy_bonus -= 6

    # Sinergie Forma + Altezza
    if "Upper" in shape_name and h <= 6.0:
        synergy_bonus += 6
        pros.append(f"Assetto Upper Ribassato ({h}mm): angolo ideale per colpire sotto i Ratchet.")
    elif "Circolare" in shape_name and h <= 6.0 and risk in ["Low", "Very Low"]:
        synergy_bonus += 4
        pros.append(f"Profilo Circolare Compatto ({h}mm): minimizza i punti d'aggancio.")

    if has_blade(blade["name"], ["Wizard Rod"]) and bit["name"] in ["Ball (B)", "Free Ball (FB)", "Hexa (H)", "Orb (O)", "Low Orb (LO)"]:
        synergy_bonus += 10
        pros.append("COMBO META S+ (Top 1-3 Mondiale): Dominio assoluto sullo Spin Finish e controllo centro.")
    elif has_blade(blade["name"], ["Cobalt Dragoon", "Meteor Dragoon"]) and bit["name"] in ["Elevate (E)", "Level (L)", "Glide (G)"]:
        synergy_bonus += 10
        pros.append("COMBO META S+ (Spin-Equalizer): Sfrutta la rotazione sinistra per rubare energia.")
    elif has_blade(blade["name"], ["Phoenix Wing", "Aero Pegasus", "Shark Scale", "Tyranno Beat", "Impact Drake"]) and bit["name"] in ["Rush (R)", "Low Rush (LR)", "Point (P)", "Low Flat (LF)", "Flat (F)", "Level (L)"]:
        synergy_bonus += 8
        pros.append("COMBO META S+: Potenza d'urto e velocità al vertice competitivo.")
    elif has_blade(blade["name"], ["Silver Wolf"]) and bit["name"] in ["Free Ball (FB)", "Ball (B)", "Hexa (H)"]:
        synergy_bonus += 8
        pros.append("COMBO META S: L'anello free-spin assorbe i colpi massimizzando la stamina.")

    if blade["type"] == bit["type"]:
        synergy_bonus += 5
        pros.append(f"Sinergia di stile ({blade['type']}).")
    elif blade["weight_g"] >= 37.5 and bit["type"] in ["Stamina", "Defense"]:
        synergy_bonus += 5
        pros.append("Assetto Ibrido Pesante: la massa stabilizza la punta.")

    if not is_int and bit["burst_res"] == "Low" and risk == "Very Low":
        synergy_bonus += 5
        pros.append(f"Protezione Burst ottimale con {ratchet['name']}.")

    penalties = 0
    cons = []
    if not is_int and bit["burst_res"] == "Low" and risk in ["High", "Very High"]:
        penalties += 18
        cons.append(f"RISCHIO BURST ALTO: {bit['name']} + {ratchet['name']}.")
    if not is_int and h >= 8.0:
        penalties += 9
        cons.append(f"Baricentro alto ({h}mm): espone il Ratchet agli attacchi bassi.")
    if w < 40.0:
        penalties += 12
        cons.append(f"Peso molto basso ({w}g): viene facilmente sbalzato.")

    score = max(0, min(100, 32 + bm[0] + bitm[0] + rm[0] + synergy_bonus - penalties))
    return score, w, h, pros, cons, calc_stats(blade["name"], blade["type"], bit["name"], bit["type"], w, bit["burst_res"], risk, h)


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
    return score, w, h, pros, cons, calc_stats(u["name"], u["type"], bit["name"], bit["type"], w, bit.get("burst_res", "High"), "Very Low", h)


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

    return score, w, h, pros, cons, calc_stats(mb["name"], mb["type"], bit["name"], bit["type"], w, bit["burst_res"], risk, h)


# ==============================================================================
# MOTORE OUTCOME CALCULATOR 1VS1 (Xtreme / Over / Burst / Spin Finish)
# ==============================================================================
def calcola_outcomes_1v1(nome1, sc1, w1, h1, st1, tp1, nome2, sc2, w2, h2, st2, tp2):
    sh1, sh_att1, sh_def1, sh_sta1, _ = get_blade_shape(nome1, tp1)
    sh2, sh_att2, sh_def2, sh_sta2, _ = get_blade_shape(nome2, tp2)

    # 1. XTREME FINISH (3 pt) - Guidato da Attacco, Peso, Forma Smash/Upper e Velocità
    xt1 = max(2.0, (st1["Attacco"] ** 1.45) * 1.4 + (w1 - w2) * 1.6 + (sh_att1 * 1.1) - (st2["Difesa"] * 1.2) - (st2["Peso"] * 0.9))
    xt2 = max(2.0, (st2["Attacco"] ** 1.45) * 1.4 + (w2 - w1) * 1.6 + (sh_att2 * 1.1) - (st1["Difesa"] * 1.2) - (st1["Peso"] * 0.9))

    # 2. OVER FINISH (2 pt) - Spinta fuori dalle tasche laterali (Peso + Attacco + Altezza)
    ov1 = max(3.0, (st1["Attacco"] * 2.1) + (w1 - w2) * 2.1 + (h2 - h1) * 1.8 - (st2["Difesa"] * 1.1))
    ov2 = max(3.0, (st2["Attacco"] * 2.1) + (w2 - w1) * 2.1 + (h1 - h2) * 1.8 - (st1["Difesa"] * 1.1))

    # 3. BURST FINISH (2 pt) - Attacco + Vantaggio Altezza (colpire sotto) vs Anti-Burst avversario
    upper_adv1 = 10.0 if ("Upper" in sh1 and h1 < h2) else max(0.0, (h2 - h1) * 3.5)
    upper_adv2 = 10.0 if ("Upper" in sh2 and h2 < h1) else max(0.0, (h1 - h2) * 3.5)
    bu1 = max(1.5, (st1["Attacco"] * 1.8) + upper_adv1 + ((10 - st2["Anti-Burst"]) ** 1.55) * 1.9 - (st2["Anti-Burst"] * 0.8))
    bu2 = max(1.5, (st2["Attacco"] * 1.8) + upper_adv2 + ((10 - st1["Anti-Burst"]) ** 1.55) * 1.9 - (st1["Anti-Burst"] * 0.8))

    # 4. SPIN FINISH (1 pt) - Stamina, Forma OWD, Spin-Equalization (Left-Spin)
    ls1 = 16.0 if ("Dragoon" in nome1 and "Dragoon" not in nome2 and ("Elevate" in nome1 or "Level" in nome1)) else 0.0
    ls2 = 16.0 if ("Dragoon" in nome2 and "Dragoon" not in nome1 and ("Elevate" in nome2 or "Level" in nome2)) else 0.0
    sp1 = max(3.0, (st1["Stamina"] ** 1.5) * 1.8 + (sh_sta1 * 1.3) + ls1 - (st2["Stamina"] * 1.1))
    sp2 = max(3.0, (st2["Stamina"] ** 1.5) * 1.8 + (sh_sta2 * 1.3) + ls2 - (st1["Stamina"] * 1.1))

    # Correzione in base al Voto Meta complessivo
    f1 = 0.85 + (sc1 / 250.0)
    f2 = 0.85 + (sc2 / 250.0)

    raw = {
        "p1_xt": xt1 * f1, "p1_ov": ov1 * f1, "p1_bu": bu1 * f1, "p1_sp": sp1 * f1,
        "p2_xt": xt2 * f2, "p2_ov": ov2 * f2, "p2_bu": bu2 * f2, "p2_sp": sp2 * f2,
    }
    tot = sum(raw.values())
    pct = {k: round((v / tot) * 100) for k, v in raw.items()}

    # Aggiustamento arrotondamento per somma esatta 100%
    diff = 100 - sum(pct.values())
    max_k = max(pct, key=pct.get)
    pct[max_k] += diff

    prob1 = pct["p1_xt"] + pct["p1_ov"] + pct["p1_bu"] + pct["p1_sp"]
    prob2 = 100 - prob1
    ev1 = round((pct["p1_xt"] * 3 + pct["p1_ov"] * 2 + pct["p1_bu"] * 2 + pct["p1_sp"] * 1) / 100.0, 2)
    ev2 = round((pct["p2_xt"] * 3 + pct["p2_ov"] * 2 + pct["p2_bu"] * 2 + pct["p2_sp"] * 1) / 100.0, 2)

    return pct, prob1, prob2, ev1, ev2, (sh1, sh2)


# ==============================================================================
# GRAFICO RADAR SOVRAPPPOSTO 1VS1 (SVG)
# ==============================================================================
def radar_1v1_svg(st1, st2):
    labels = ["Attacco", "Difesa", "Stamina", "Peso", "Anti-Burst"]
    cx, cy, max_r = 160, 150, 95
    n = len(labels)

    def poly_points(stats_dict):
        pts = []
        for idx, k in enumerate(labels):
            val = max(1, min(10, stats_dict.get(k, 5)))
            r = (val / 10.0) * max_r
            angle = -math.pi / 2 + (2 * math.pi * idx / n)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            pts.append(f"{x:.1f},{y:.1f}")
        return " ".join(pts)

    grid_polys = []
    for level in [2, 4, 6, 8, 10]:
        r = (level / 10.0) * max_r
        g_pts = []
        for idx in range(n):
            angle = -math.pi / 2 + (2 * math.pi * idx / n)
            g_pts.append(f"{cx + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}")
        grid_polys.append(f'<polygon points="{" ".join(g_pts)}" fill="none" stroke="#475569" stroke-width="0.8" stroke-dasharray="2,2"/>')

    axes_svg = []
    text_svg = []
    for idx, k in enumerate(labels):
        angle = -math.pi / 2 + (2 * math.pi * idx / n)
        ex = cx + max_r * math.cos(angle)
        ey = cy + max_r * math.sin(angle)
        axes_svg.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#475569" stroke-width="0.9"/>')

        lx = cx + (max_r + 24) * math.cos(angle)
        ly = cy + (max_r + 18) * math.sin(angle)
        v1 = st1.get(k, 5)
        v2 = st2.get(k, 5)
        text_svg.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="11" font-weight="bold" fill="#e2e8f0">'
            f'{k} (<tspan fill="#38bdf8">{v1}</tspan>/<tspan fill="#f87171">{v2}</tspan>)</text>'
        )

    p1_poly = poly_points(st1)
    p2_poly = poly_points(st2)

    svg = f"""
    <div style="display:flex;justify-content:center;align-items:center;">
      <svg viewBox="0 0 320 300" width="100%" style="max-width:340px;background:#0f172a;border-radius:12px;padding:6px;">
        {"".join(grid_polys)}
        {"".join(axes_svg)}
        <polygon points="{p1_poly}" fill="rgba(56, 189, 248, 0.28)" stroke="#38bdf8" stroke-width="2.2"/>
        <polygon points="{p2_poly}" fill="rgba(248, 113, 113, 0.28)" stroke="#f87171" stroke-width="2.2"/>
        {"".join(text_svg)}
      </svg>
    </div>
    """
    return svg


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


def radar_singolo_svg(stats_dict):
    labels = ["Attacco", "Difesa", "Stamina", "Peso", "Anti-Burst"]
    cx, cy, max_r = 160, 150, 95
    n = len(labels)

    pts = []
    for idx, k in enumerate(labels):
        val = max(1, min(10, stats_dict.get(k, 5)))
        r = (val / 10.0) * max_r
        angle = -math.pi / 2 + (2 * math.pi * idx / n)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pts.append(f"{x:.1f},{y:.1f}")

    grid_polys = []
    for level in [2, 4, 6, 8, 10]:
        r = (level / 10.0) * max_r
        g_pts = []
        for idx in range(n):
            angle = -math.pi / 2 + (2 * math.pi * idx / n)
            g_pts.append(f"{cx + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}")
        grid_polys.append(f'<polygon points="{" ".join(g_pts)}" fill="none" stroke="#475569" stroke-width="0.8" stroke-dasharray="2,2"/>')

    axes_svg = []
    text_svg = []
    for idx, k in enumerate(labels):
        angle = -math.pi / 2 + (2 * math.pi * idx / n)
        ex = cx + max_r * math.cos(angle)
        ey = cy + max_r * math.sin(angle)
        axes_svg.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#475569" stroke-width="0.9"/>')

        lx = cx + (max_r + 24) * math.cos(angle)
        ly = cy + (max_r + 18) * math.sin(angle)
        val = stats_dict.get(k, 5)
        text_svg.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="11" font-weight="bold" fill="#e2e8f0">'
            f'{k} (<tspan fill="#38bdf8">{val}</tspan>)</text>'
        )

    return f"""
    <div style="display:flex;justify-content:center;align-items:center;">
      <svg viewBox="0 0 320 300" width="100%" style="max-width:340px;background:#0f172a;border-radius:12px;padding:6px;">
        {"".join(grid_polys)}
        {"".join(axes_svg)}
        <polygon points="{" ".join(pts)}" fill="rgba(56, 189, 248, 0.30)" stroke="#38bdf8" stroke-width="2.2"/>
        {"".join(text_svg)}
      </svg>
    </div>
    """


# ==============================================================================
# TAB 1: ANALIZZATORE COMBO & RADAR
# ==============================================================================
with t1:
    st.subheader("🔍 Analizzatore Combo, Fisica & Radar Statistiche")
    usa_col_1 = st.checkbox("Usa solo i pezzi della Mia Collezione", value=False, key="usa_col_t1")
    lin_1 = st.radio(
        "Seleziona Linea:",
        ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"],
        horizontal=True,
        key="lin_t1"
    )

    c_sel, c_res = st.columns([1.2, 1.3])
    with c_sel:
        st.markdown("### 🛠️ Assembla la tua Combo")
        nome_c, voto_c, peso_c, alt_c, pros_c, cons_c, stats_c, pezzi_c, tipo_c = selettore_bey(c_sel, "t1", lin_1, usa_col_1)

    with c_res:
        st.markdown("### 📊 Valutazione & Radar")
        m1, m2, m3 = st.columns(3)
        m1.metric("Voto Meta", f"{voto_c} / 100")
        m2.metric("Peso Totale", f"{peso_c} g")
        m3.metric("Altezza Stimata", f"{alt_c} mm")

        st.progress(max(0, min(100, voto_c)))
        st.markdown(radar_singolo_svg(stats_c), unsafe_allow_html=True)

        if pros_c:
            st.success("✅ **Punti di Forza & Sinergie:**\n- " + "\n- ".join(pros_c))
        if cons_c:
            st.warning("⚠️ **Avvertenze & Rischi:**\n- " + "\n- ".join(cons_c))

        if st.button("➕ Aggiungi questa Combo al Deck Torneo", key="btn_add_deck_t1"):
            if len(st.session_state.deck) >= 3:
                st.error("Hai già 3 Beyblade nel Deck! Rimuovine uno nella scheda 'Deck Torneo' per aggiungerne un altro.")
            else:
                st.session_state.deck.append({
                    "nome": nome_c,
                    "voto": voto_c,
                    "peso": peso_c,
                    "pezzi": pezzi_c,
                    "tipo": tipo_c
                })
                st.success(f"✅ Aggiunta **{nome_c}** al Deck Torneo!")
                st.rerun()


# ==============================================================================
# TAB 2: SIMULATORE 1VS1 & OUTCOME CALCULATOR
# ==============================================================================
with t2:
    st.subheader("⚔️ Simulatore 1vs1 & Outcome Calculator (Xtreme / Over / Burst / Spin)")
    s1, s2 = st.columns(2)
    s1.markdown("### 🔵 Blader 1")
    lin1 = s1.selectbox("Linea Blader 1:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], index=0, key="lin1")
    nome1, sc1, w1, h1, _, _, st1, _, tp1 = selettore_bey(s1, "p1", lin1, False)

    s2.markdown("### 🔴 Blader 2")
    lin2 = s2.selectbox("Linea Blader 2:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], index=1, key="lin2")
    nome2, sc2, w2, h2, _, _, st2, _, tp2 = selettore_bey(s2, "p2", lin2, False)

    pct, prob1, prob2, ev1, ev2, (sh1, sh2) = calcola_outcomes_1v1(nome1, sc1, w1, h1, st1, tp1, nome2, sc2, w2, h2, st2, tp2)

    st.divider()
    res_c1, res_c2, res_c3 = st.columns(3)
    res_c1.metric(f"🔵 {nome1}", f"{prob1}% Vittoria Totale", f"{w1}g | Alt: {h1}mm | {sh1}")
    res_c2.metric("Confronto Fisico (Peso / Alt.)", f"Δ {round(abs(w1 - w2), 2)} g | Δ {round(abs(h1 - h2), 1)} mm", f"Punti Attesi/Round: {ev1} vs {ev2}")
    res_c3.metric(f"🔴 {nome2}", f"{prob2}% Vittoria Totale", f"{w2}g | Alt: {h2}mm | {sh2}")

    st.markdown("### 🎯 Outcome Calculator — Probabilità per Tipo di Finale")
    oc1, oc2 = st.columns(2)

    with oc1:
        st.markdown(f"#### 🔵 Esiti Vittoria: {nome1} ({prob1}%)")
        st.write(f"⚡ **Xtreme Finish (3 pt):** `{pct['p1_xt']}%`")
        st.progress(min(100, pct["p1_xt"]))
        st.write(f"🚀 **Over Finish (2 pt):** `{pct['p1_ov']}%`")
        st.progress(min(100, pct["p1_ov"]))
        st.write(f"💥 **Burst Finish (2 pt):** `{pct['p1_bu']}%`")
        st.progress(min(100, pct["p1_bu"]))
        st.write(f"🔄 **Spin Finish (1 pt):** `{pct['p1_sp']}%`")
        st.progress(min(100, pct["p1_sp"]))

    with oc2:
        st.markdown(f"#### 🔴 Esiti Vittoria: {nome2} ({prob2}%)")
        st.write(f"⚡ **Xtreme Finish (3 pt):** `{pct['p2_xt']}%`")
        st.progress(min(100, pct["p2_xt"]))
        st.write(f"🚀 **Over Finish (2 pt):** `{pct['p2_ov']}%`")
        st.progress(min(100, pct["p2_ov"]))
        st.write(f"💥 **Burst Finish (2 pt):** `{pct['p2_bu']}%`")
        st.progress(min(100, pct["p2_bu"]))
        st.write(f"🔄 **Spin Finish (1 pt):** `{pct['p2_sp']}%`")
        st.progress(min(100, pct["p2_sp"]))

    st.divider()
    col_pred, col_rad_1v1 = st.columns([1.3, 1])
    outcomes_labels = {
        "p1_xt": f"🔵 Xtreme Finish di {nome1} (3 pt)",
        "p1_ov": f"🔵 Over Finish di {nome1} (2 pt)",
        "p1_bu": f"🔵 Burst Finish di {nome1} (2 pt)",
        "p1_sp": f"🔵 Spin Finish di {nome1} (1 pt)",
        "p2_xt": f"🔴 Xtreme Finish di {nome2} (3 pt)",
        "p2_ov": f"🔴 Over Finish di {nome2} (2 pt)",
        "p2_bu": f"🔴 Burst Finish di {nome2} (2 pt)",
        "p2_sp": f"🔴 Spin Finish di {nome2} (1 pt)",
    }
    top_outcome = max(pct, key=pct.get)
    col_pred.success(f"🏆 **Esito Singolo Più Probabile:** {outcomes_labels[top_outcome]} (**{pct[top_outcome]}%**)")
    col_pred.info(
        f"**Analisi Tattica:**\n"
        f"- **🔵 {nome1}** ({w1}g, {h1}mm, *{sh1}*) punta a chiudere per **{max([('Xtreme', pct['p1_xt']), ('Over', pct['p1_ov']), ('Burst', pct['p1_bu']), ('Spin', pct['p1_sp'])], key=lambda x: x[1])[0]} Finish**.\n"
        f"- **🔴 {nome2}** ({w2}g, {h2}mm, *{sh2}*) punta a chiudere per **{max([('Xtreme', pct['p2_xt']), ('Over', pct['p2_ov']), ('Burst', pct['p2_bu']), ('Spin', pct['p2_sp'])], key=lambda x: x[1])[0]} Finish**."
    )
    col_pred.caption("🔵 **Area Blu** = Blader 1 | 🔴 **Area Rossa** = Blader 2")
    col_rad_1v1.markdown(radar_1v1_svg(st1, st2), unsafe_allow_html=True)

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
