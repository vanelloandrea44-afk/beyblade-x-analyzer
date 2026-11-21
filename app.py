import json, math, os, streamlit as st

st.set_page_config(page_title="Beyblade X Pro Meta System", page_icon="⚡", layout="wide")

db = json.load(open("beyblade_bx_db.json", "r", encoding="utf-8"))
COL_FILE = "mia_collezione.json"
load_col = lambda: json.load(open(COL_FILE, "r", encoding="utf-8")) if os.path.exists(COL_FILE) else {"blades": [], "ratchets": [], "bits": [], "cx_locks": [], "cx_mains": [], "cx_metals": [], "cx_overs": [], "cx_assists": []}
save_col = lambda d: json.dump(d, open(COL_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
if "deck" not in st.session_state: st.session_state.deck = []

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
    "Tricera Press": (15, "A", "Massa notevole per assorbire i colpi pesanti."),
    "Xeno Xcalibur": (14, "A", "Forte impatto frontale ma stamina limitata."),
    "Ghost Circle": (6, "C", "Troppo leggera (26.8g): viene sbalzata fuori dall'arena con facilità."),
    "Shinobi Shadow": (7, "C", "Estremamente leggera (28.5g): soffre qualsiasi impatto diretto."),
    "Dranzer": (4, "C", "Remake X-Over da collezione: peso troppo basso per il gioco competitivo."),
    "Driger": (5, "C", "Remake X-Over leggero: divertente ma non competitivo."),
    "Dragoon Storm": (3, "C", "Troppo leggero (25.4g) per reggere gli urti di Beyblade X."),
    "Draciel": (4, "C", "Remake X-Over da collezione.")
}

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

get_blade_meta = lambda n: next((v for k, v in META_BLADES.items() if k.lower() in n.lower()), (11, "B", "Blade standard senza vantaggi competitivi particolari."))
get_bit_meta = lambda n: META_BITS.get(n, (9, "B", "Bit standard."))
get_ratchet_meta = lambda n: META_RATCHETS.get(n, (7, "B", "Ratchet standard."))

radar_svg = lambda stats: f'<svg width="290" height="260" viewBox="0 0 290 260"><polygon points="{" ".join([f"{140 + 85 * math.cos(math.radians(-90 + i * 72)):.1f},{130 + 85 * math.sin(math.radians(-90 + i * 72)):.1f}" for i in range(5)])}" fill="#1e293b" stroke="#475569" stroke-width="1.5"/><polygon points="{" ".join([f"{140 + (85 * max(1, min(10, stats[l])) / 10.0) * math.cos(math.radians(-90 + i * 72)):.1f},{130 + (85 * max(1, min(10, stats[l])) / 10.0) * math.sin(math.radians(-90 + i * 72)):.1f}" for i, l in enumerate(["Attacco", "Difesa", "Stamina", "Peso", "Anti-Burst"])])}" fill="rgba(56, 189, 248, 0.45)" stroke="#38bdf8" stroke-width="2.5"/>{"".join([f"<text x=\"{140 + 109 * math.cos(math.radians(-90 + i * 72)):.1f}\" y=\"{130 + 103 * math.sin(math.radians(-90 + i * 72)):.1f}\" fill=\"#ffffff\" font-size=\"11\" font-weight=\"bold\" text-anchor=\"middle\">{l} ({stats[l]})</text>" for i, l in enumerate(["Attacco", "Difesa", "Stamina", "Peso", "Anti-Burst"])])}</svg>'

calc_stats = lambda b_name, b_type, bit_name, bit_type, w, burst_res, risk: {
    "Attacco": max(1, min(10, (8 if b_type == "Attack" else (5 if b_type == "Balance" else 3)) + (2 if bit_type == "Attack" else (1 if bit_type == "Balance" else -1)) + ((2 if get_blade_meta(b_name)[0] >= 20 else (1 if get_blade_meta(b_name)[0] >= 16 else 0)) if b_type == "Attack" else 0))),
    "Difesa": max(1, min(10, (8 if b_type == "Defense" else (5 if b_type == "Balance" else 3)) + (2 if bit_type == "Defense" else (1 if bit_type == "Balance" else -1)) + ((2 if get_blade_meta(b_name)[0] >= 20 else (1 if get_blade_meta(b_name)[0] >= 16 else 0)) if b_type == "Defense" else 0))),
    "Stamina": 10 if (("Wizard Rod" in b_name and bit_type == "Stamina") or ("Cobalt Dragoon" in b_name and ("Elevate" in bit_name or "Level" in bit_name))) else max(1, min(10, (8 if b_type == "Stamina" else (5 if b_type == "Balance" else 3)) + (2 if bit_type == "Stamina" else (1 if bit_type == "Balance" else -1)) + ((2 if get_blade_meta(b_name)[0] >= 20 else (1 if get_blade_meta(b_name)[0] >= 16 else 0)) if b_type == "Stamina" else 0))),
    "Peso": max(1, min(10, round((w - 37.5) * 1.1))),
    "Anti-Burst": max(1, min(10, (8 if burst_res == "High" else 4) + (2 if risk == "Very Low" else (1 if risk == "Low" else (-2 if "High" in risk else 0)))))
}

valuta = lambda blade, ratchet, bit: (
    lambda is_int, w, h, risk, bm, bitm, rm: (
        max(0, min(100, 32 + bm[0] + bitm[0] + rm[0] +
(12 if "Wizard Rod" in blade["name"] and bit["name"] in ["Ball (B)", "Free Ball (FB)", "Hexa (H)", "Orb (O)", "Low Orb (LO)"] else
(12 if "Cobalt Dragoon" in blade["name"] and bit["name"] in ["Elevate (E)", "Level (L)", "Glide (G)"] else
(10 if any(x in blade["name"] for x in ["Phoenix Wing", "Aero Pegasus", "Shark Scale", "Tyranno Beat", "Impact Drake"]) and bit["name"] in ["Rush (R)", "Low Rush (LR)", "Point (P)", "Low Flat (LF)", "Flat (F)", "Level (L)"] else
(10 if "Silver Wolf" in blade["name"] and bit["name"] in ["Free Ball (FB)", "Ball (B)", "Hexa (H)"] else 0)))) +
(6 if blade["type"] == bit["type"] or (blade["weight_g"] >= 37.5 and bit["type"] in ["Stamina", "Defense"]) else 0) -
(18 if not is_int and bit["burst_res"] == "Low" and risk in ["High", "Very High"] else (-6 if not is_int and bit["burst_res"] == "Low" and risk == "Very Low" else 0)) -
(8 if not is_int and h >= 8.0 else 0) -
(10 if w < 40.0 else 0)
)),
w, h,
[f"Blade Tier {bm[1]}: {bm[2]}"] +
(["COMBO META S+ (Top 1-3 Mondiale): Dominio assoluto sullo Spin Finish e controllo centro."] if "Wizard Rod" in blade["name"] and bit["name"] in ["Ball (B)", "Free Ball (FB)", "Hexa (H)", "Orb (O)", "Low Orb (LO)"] else []) +
(["COMBO META S+ (Spin-Equalizer): Sfrutta la rotazione sinistra per rubare energia."] if "Cobalt Dragoon" in blade["name"] and bit["name"] in ["Elevate (E)", "Level (L)", "Glide (G)"] else []) +
(["COMBO META S+: Potenza d'urto e velocità al vertice competitivo."] if any(x in blade["name"] for x in ["Phoenix Wing", "Aero Pegasus", "Shark Scale", "Tyranno Beat", "Impact Drake"]) and bit["name"] in ["Rush (R)", "Low Rush (LR)", "Point (P)", "Low Flat (LF)", "Flat (F)", "Level (L)"] else []) +
(["COMBO META S: L'anello free-spin assorbe i colpi massimizzando la stamina."] if "Silver Wolf" in blade["name"] and bit["name"] in ["Free Ball (FB)", "Ball (B)", "Hexa (H)"] else []) +
([f"Sinergia di stile ({blade['type']})."] if blade["type"] == bit["type"] else (["Assetto Ibrido Pesante: la massa stabilizza la punta."] if blade["weight_g"] >= 37.5 and bit["type"] in ["Stamina", "Defense"] else [])) +
([f"Protezione Burst ottimale con {ratchet['name']}."] if not is_int and bit["burst_res"] == "Low" and risk == "Very Low" else []),
([f"RISCHIO BURST ALTO: {bit['name']} + {ratchet['name']}."] if not is_int and bit["burst_res"] == "Low" and risk in ["High", "Very High"] else []) +
([f"Baricentro alto ({h}mm): rischio sbilanciamento."] if not is_int and h >= 8.0 else []) +
([f"Peso molto basso ({w}g): viene facilmente sbalzato."] if w < 40.0 else []),
calc_stats(blade["name"], blade["type"], bit["name"], bit["type"], w, bit["burst_res"], risk)
)
)(
"Ratchet-Integrated" in bit["name"],
round(blade["weight_g"] + (0 if "Ratchet-Integrated" in bit["name"] else ratchet["weight_g"]) + bit["weight_g"], 2),
round((6.0 if "Ratchet-Integrated" in bit["name"] else ratchet["height_mm"]) + bit["height_mod"], 1),
"Very Low" if "Ratchet-Integrated" in bit["name"] else ratchet["burst_risk"],
get_blade_meta(blade["name"]),
get_bit_meta(bit["name"]),
(12, "S+", "") if "Ratchet-Integrated" in bit["name"] else get_ratchet_meta(ratchet["name"])
)
valuta_ux_inf = lambda u, bit: (
lambda w, h: (
max(0, min(100, 56 + get_bit_meta(bit["name"])[0] + (8 if u["type"] == bit["type"] else 0) + (6 if w >= 46.5 else 0) - (8 if h >= 8.0 else 0))),
w, h,
["UX Infinity (Ratchet Integrato): zero gioco meccanico e basso rischio Burst."] + ([f"Sinergia pura ({u['type']})."] if u["type"] == bit["type"] else []) + ([f"Peso elevato ({w}g)."] if w >= 46.5 else []),
[f"Baricentro alto ({h}mm)."] if h >= 8.0 else [],
calc_stats(u["name"], u["type"], bit["name"], bit["type"], w, bit.get("burst_res", "High"), "Very Low")
)
)(round(u["weight_g"] + bit["weight_g"], 2), round(u["height_mm"] + bit["height_mod"], 1))
valuta_cx = lambda lk, mb, ov, ab, r, bit, is_6: (
lambda is_i, w, h, risk: (
max(0, min(100, 46 + get_bit_meta(bit["name"])[0] + (12 if is_i else get_ratchet_meta(r["name"])[0]) + (8 if lk["weight_g"] >= 4.5 else 0) + (8 if mb["type"] == bit["type"] else 0) + (8 if w >= 47.0 else 0) - (10 if h >= 8.0 else 0) - (16 if bit["burst_res"] == "Low" and risk in ["High", "Very High"] else 0))),
w, h,
(["Metal Lock Chip: aumenta il peso centrale."] if lk["weight_g"] >= 4.5 else []) + ([f"Coerenza di stile ({mb['type']})."] if mb["type"] == bit["type"] else []) + ([f"Peso elevato ({w}g): grande inerzia."] if w >= 47.0 else []),
([f"Assetto alto ({h}mm): espone il Ratchet."] if h >= 8.0 else []) + ([f"RISCHIO BURST ALTO: {bit['name']} + {r['name']}."] if bit["burst_res"] == "Low" and risk in ["High", "Very High"] else []),
calc_stats(mb["name"], mb["type"], bit["name"], bit["type"], w, bit["burst_res"], risk)
)
)(
"Ratchet-Integrated" in bit["name"],
round(lk["weight_g"] + mb["weight_g"] + (ov["weight_g"] if is_6 else 0.0) + ab["weight_g"] + (0 if "Ratchet-Integrated" in bit["name"] else r["weight_g"]) + bit["weight_g"], 2),
round((6.0 if "Ratchet-Integrated" in bit["name"] else r["height_mm"]) + ab["height_mod"] + bit["height_mod"], 1),
"Low" if "Ratchet-Integrated" in bit["name"] else r["burst_risk"]
)
st.title("⚡ Beyblade X - Pro Meta System & Arena 1vs1")
t1, t2, t3, t4, t5 = st.tabs(["🔍 Analizzatore & Radar", "⚔️ Simulatore 1vs1", "🤖 Suggeritore Top Combo", f"🏆 Deck Torneo ({len(st.session_state.deck)}/3)", "📦 La Mia Collezione"])
col_data = load_col()
filtra = lambda lista, cat, attivo: ([x for x in lista if x["name"] in col_data.get(cat, [])] or lista) if (attivo and col_data.get(cat, [])) else lista
selettore_std = lambda cont, pref, lin, usa_col: (
lambda b, bit: (
lambda is_i, r: (f"{b['name']} {'' if is_i else r['name'] + ' '}{bit['name']}", *valuta(b, r, bit), ([b["name"], bit["name"]] if is_i else [b["name"], r["name"], bit["name"]]), b["type"])
)("Ratchet-Integrated" in bit["name"], cont.selectbox("Ratchet", filtra(db["ratchets"], "ratchets", usa_col), key=f"{pref}_r", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)", disabled=("Ratchet-Integrated" in bit["name"])))
)(
cont.selectbox("Blade", filtra({"1. BX": db["bx_blades"], "2. UX": db["ux_blades"], "4. BX Infinity": db.get("bx_infinity", db["bx_blades"])}[lin], "blades", usa_col), key=f"{pref}_b", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]"),
cont.selectbox("Bit", filtra(db["bits"], "bits", usa_col), key=f"{pref}_bit", format_func=lambda x: f"{x['name']} ({x['type']})")
)
selettore_ux_inf = lambda cont, pref, usa_col: (
lambda u, bit: (f"{u['name']} + {bit['name']}", *valuta_ux_inf(u, bit), [u["name"], bit["name"]], u["type"])
)(
cont.selectbox("Blade UX Infinity", filtra(db["ux_infinity"], "blades", usa_col), key=f"{pref}_u", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)"),
cont.selectbox("Bit", filtra([x for x in db["bits"] if "Ratchet-Integrated" not in x["name"]], "bits", usa_col), key=f"{pref}_ubit", format_func=lambda x: f"{x['name']} ({x['type']})")
)
selettore_cx = lambda cont, pref, is_6, usa_col: (
lambda lk, mb, ov, ab, bit: (
lambda is_i, r: (
f"{mb['name']} [{lk['name']}{f' + {ov["name"]}' if is_6 else ''} + {ab['name']}] {'' if is_i else r['name'] + ' '}{bit['name']}",
*valuta_cx(lk, mb, ov, ab, r, bit, is_6),
[lk["name"], mb["name"], ab["name"], bit["name"]] + ([ov["name"]] if is_6 else []) + ([] if is_i else [r["name"]]),
mb["type"]
)
)("Ratchet-Integrated" in bit["name"], cont.selectbox("Ratchet", filtra(db["ratchets"], "ratchets", usa_col), key=f"{pref}_cr", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)", disabled=("Ratchet-Integrated" in bit["name"])))
)(
cont.selectbox("Lock Chip", filtra(db["cx_lock_chips"], "cx_locks", usa_col), key=f"{pref}_lk", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)"),
cont.selectbox("Metal Blade" if is_6 else "Main Blade", filtra(db["cx_metal_blades"] if is_6 else db["cx_main_blades"], "cx_metals" if is_6 else "cx_mains", usa_col), key=f"{pref}_mb", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]"),
cont.selectbox("Over Blade", filtra(db["cx_over_blades"], "cx_overs", usa_col), key=f"{pref}_ov", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)") if is_6 else {"name": "", "weight_g": 0.0},
cont.selectbox("Assist Blade", filtra(db["cx_assist_blades"], "cx_assists", usa_col), key=f"{pref}_ab", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)"),
cont.selectbox("Bit", filtra(db["bits"], "bits", usa_col), key=f"{pref}_cbit", format_func=lambda x: f"{x['name']} ({x['type']})")
)
selettore_bey = lambda cont, pref, lin, usa_col: selettore_std(cont, pref, lin, usa_col) if lin in ["1. BX", "2. UX", "4. BX Infinity"] else (selettore_ux_inf(cont, pref, usa_col) if lin == "5. UX Infinity" else selettore_cx(cont, pref, lin == "6. CX Infinity (6 Pezzi)", usa_col))
solo_mia_col = t1.checkbox("Filtra menu usando solo i pezzi della Mia Collezione", value=False)
linea = t1.radio("Linea:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], horizontal=True)
nome, sc, w, h, pros, cons, st_rad, pezzi_usati, _ = selettore_bey(t1, "t1", linea, solo_mia_col)
t1.subheader(f"Combo: {nome}")
col_sx, col_dx = t1.columns([1.4, 1])
m1, m2, m3 = col_sx.columns(3)
m1.metric("Voto Meta", f"{sc} / 100"); m2.metric("Peso", f"{w} g"); m3.metric("Altezza", f"{h} mm")
cp, cc = col_sx.columns(2)
cp.markdown("### ✅ Pro")
_ = [cp.success(p) for p in pros] if pros else cp.info("Bilanciata.")
cc.markdown("### ⚠️ Contro")
_ = [cc.error(c) for c in cons] if cons else cc.success("Nessun difetto grave!")
col_dx.markdown("### 📊 Radar Statistiche")
col_dx.markdown(radar_svg(st_rad), unsafe_allow_html=True)
add_btn = col_sx.button("➕ Aggiungi questa Combo al Deck Torneo")
_ = add_btn and len(st.session_state.deck) < 3 and (st.session_state.deck.append({"nome": nome, "voto": sc, "peso": w, "pezzi": pezzi_usati}), st.rerun())
_ = add_btn and len(st.session_state.deck) >= 3 and col_sx.warning("Il Deck ha già 3 Beyblade! Vai nella scheda Deck Torneo per rimuoverne uno.")
t2.subheader("⚔️ Confronto Testa a Testa Universale (BX / UX / CX / Infinity)")
s1, s2 = t2.columns(2)
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
t2.divider()
res_c1, res_c2, res_c3 = t2.columns(3)
res_c1.metric(f"🔵 {nome1}", f"{prob1}% Vittoria", f"{w1}g | Voto Meta {sc1}")
res_c2.metric("Differenza Peso", f"{round(abs(w1 - w2), 2)} g", f"Vantaggio {'Blader 1' if w1 >= w2 else 'Blader 2'}")
res_c3.metric(f"🔴 {nome2}", f"{prob2}% Vittoria", f"{w2}g | Voto Meta {sc2}")
win_n, win_st, lose_h, lose_st = (nome1, st1, h2, st2) if prob1 >= prob2 else (nome2, st2, h1, st1)
cond_win = "Spin Finish (1 pt) per resistenza e OWD superiore" if win_st["Stamina"] >= 9 else ("Xtreme / Over Finish (2-3 pt) per impatto pesante" if win_st["Attacco"] >= 8 else ("Burst Finish (2 pt) su Ratchet esposto" if lose_h >= 7.5 or lose_st["Anti-Burst"] <= 4 else "Spin Finish (1 pt) per controllo del centro"))
t2.success(f"Pronostico Arena: Favorito {'Blader 1' if prob1 >= prob2 else 'Blader 2'} ({win_n}) — Esito più probabile: {cond_win}.")
usa_col_sug = t3.checkbox("Usa solo pezzi della Mia Collezione per i suggerimenti", value=False)
lin_sug = t3.radio("Seleziona la Linea da ottimizzare:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], horizontal=True)
bits_1v1 = [x for x in db["bits"] if "Ratchet-Integrated" not in x["name"]]
r_pool = filtra(db["ratchets"], "ratchets", usa_col_sug)
b_pool = filtra(bits_1v1, "bits", usa_col_sug)
mappa_s = {"1. BX": db["bx_blades"], "2. UX": db["ux_blades"], "4. BX Infinity": db.get("bx_infinity", db["bx_blades"])}
tb = t3.selectbox("Blade da ottimizzare:", filtra(mappa_s.get(lin_sug, db["bx_blades"]), "blades", usa_col_sug), format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]") if lin_sug in ["1. BX", "2. UX", "4. BX Infinity"] else None
tu = t3.selectbox("Blade UX Infinity da ottimizzare:", filtra(db["ux_infinity"], "blades", usa_col_sug), format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]") if lin_sug == "5. UX Infinity" else None
is_6_s = (lin_sug == "6. CX Infinity (6 Pezzi)")
sc1_c, sc2_c, sc3_c = t3.columns(3) if lin_sug in ["3. CX (5 Pezzi)", "6. CX Infinity (6 Pezzi)"] else (None, None, None)
tlk = sc1_c.selectbox("Lock Chip:", filtra(db["cx_lock_chips"], "cx_locks", usa_col_sug), format_func=lambda x: f"{x['name']} ({x['weight_g']}g)") if sc1_c else None
tmb = sc2_c.selectbox("Metal Blade:" if is_6_s else "Main Blade:", filtra(db["cx_metal_blades"] if is_6_s else db["cx_main_blades"], "cx_metals" if is_6_s else "cx_mains", usa_col_sug), format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]") if sc2_c else None
tov = sc3_c.selectbox("Over Blade:", filtra(db["cx_over_blades"], "cx_overs", usa_col_sug), format_func=lambda x: f"{x['name']} ({x['weight_g']}g)") if (sc3_c and is_6_s) else {"name": "", "weight_g": 0.0}
ab_pool = filtra(db["cx_assist_blades"], "cx_assists", usa_col_sug)
ov_t = f" + {tov['name']}" if is_6_s else ""
calc_s = t3.button("🚀 Calcola Top 5 Combo")
res_sug = sorted([(valuta(tb, r, b), f"{tb['name']} {r['name']} {b['name']}") for r in r_pool for b in b_pool], key=lambda x: x[0][0], reverse=True) if (calc_s and tb) else (sorted([(valuta_ux_inf(tu, b), f"{tu['name']} + {b['name']}") for b in b_pool], key=lambda x: x[0][0], reverse=True) if (calc_s and tu) else (sorted([(valuta_cx(tlk, tmb, tov, ab, r, b, is_6_s), f"{tmb['name']} [{tlk['name']}{ov_t} + {ab['name']}] {r['name']} {b['name']}") for ab in ab_pool for r in r_pool for b in b_pool], key=lambda x: x[0][0], reverse=True) if (calc_s and tlk) else []))
_ = [t3.info(f"#{i} — {c_name} | Voto Meta: {v[0]}/100 | Peso: {v[1]}g | Altezza: {v[2]}mm\n\n✅ {' • '.join(v[3]) if v[3] else 'Bilanciata'}\n\n⚠️ {' • '.join(v[4]) if v[4] else 'Nessun rischio'}") for i, (v, c_name) in enumerate(res_sug[:5], 1)]
t4.subheader("🏆 Il tuo Deck da 3 Beyblade (Regolamento 3on3)")
_ = not st.session_state.deck and t4.info("Il tuo Deck è vuoto. Costruisci una combo nella prima scheda e clicca su '➕ Aggiungi questa Combo al Deck Torneo'.")
tutti_pezzi_deck = [p for item in st.session_state.deck for p in item["pezzi"]]
duplicati = set([p for p in tutti_pezzi_deck if tutti_pezzi_deck.count(p) > 1])
_ = st.session_state.deck and duplicati and t4.error(f"⛔ DECK NON VALIDO DA TORNEO! Hai inserito pezzi duplicati: {', '.join(duplicati)}")
_ = st.session_state.deck and not duplicati and t4.success("✅ DECK VALIDO DA TORNEO: Nessun pezzo ripetuto tra i Beyblade!")
_ = st.session_state.deck and t4.metric("Media Competitiva del Deck", f"{round(sum(x['voto'] for x in st.session_state.deck) / len(st.session_state.deck), 1)} / 100")
_ = [t4.write(f"Bey #{i+1}: {it['nome']} — Voto Meta: {it['voto']}/100 ({it['peso']}g)") for i, it in enumerate(st.session_state.deck)]
_ = st.session_state.deck and t4.button("🗑️ Svuota tutto il Deck") and (st.session_state.deck.clear(), st.rerun())
t5.subheader("📦 Gestisci i pezzi che possiedi fisicamente (Tutte le Linee)")
all_b_names = [x["name"] for x in db["bx_blades"] + db["ux_blades"] + db.get("bx_infinity", []) + db["ux_infinity"]]
all_r_names = [x["name"] for x in db["ratchets"]]
all_bit_names = [x["name"] for x in db["bits"]]
all_lk = [x["name"] for x in db["cx_lock_chips"]]
all_mb = [x["name"] for x in db["cx_main_blades"]]
all_mt = [x["name"] for x in db["cx_metal_blades"]]
all_ov = [x["name"] for x in db["cx_over_blades"]]
all_ab = [x["name"] for x in db["cx_assist_blades"]]
sel_b = t5.multiselect("Blade (BX / UX / Infinity):", all_b_names, default=[x for x in col_data.get("blades", []) if x in all_b_names])
sel_r = t5.multiselect("Ratchet:", all_r_names, default=[x for x in col_data.get("ratchets", []) if x in all_r_names])
sel_bit = t5.multiselect("Bit:", all_bit_names, default=[x for x in col_data.get("bits", []) if x in all_bit_names])
c_cx1, c_cx2 = t5.columns(2)
sel_lk = c_cx1.multiselect("CX Lock Chips:", all_lk, default=[x for x in col_data.get("cx_locks", []) if x in all_lk])
sel_mb = c_cx1.multiselect("CX Main Blades:", all_mb, default=[x for x in col_data.get("cx_mains", []) if x in all_mb])
sel_mt = c_cx1.multiselect("CX Infinity Metal Blades:", all_mt, default=[x for x in col_data.get("cx_metals", []) if x in all_mt])
sel_ov = c_cx2.multiselect("CX Infinity Over Blades:", all_ov, default=[x for x in col_data.get("cx_overs", []) if x in all_ov])
sel_ab = c_cx2.multiselect("CX Assist Blades:", all_ab, default=[x for x in col_data.get("cx_assists", []) if x in all_ab])
_ = t5.button("💾 Salva la Mia Collezione Completa") and (save_col({"blades": sel_b, "ratchets": sel_r, "bits": sel_bit, "cx_locks": sel_lk, "cx_mains": sel_mb, "cx_metals": sel_mt, "cx_overs": sel_ov, "cx_assists": sel_ab}), t5.success("Collezione completa salvata! Ora il filtro funziona su tutte le linee (BX, UX, CX e Infinity)."))
