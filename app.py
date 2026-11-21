import json, math, os, streamlit as st

st.set_page_config(page_title="Beyblade X Pro System", page_icon="⚡", layout="wide")

@st.cache_data
def load_data():
    with open("beyblade_bx_db.json", "r", encoding="utf-8") as f:
        return json.load(f)

db = load_data()
COL_FILE = "mia_collezione.json"

def load_col():
    if os.path.exists(COL_FILE):
        with open(COL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"blades": [], "ratchets": [], "bits": [], "cx_locks": [], "cx_mains": [], "cx_metals": [], "cx_overs": [], "cx_assists": []}

def save_col(data):
    with open(COL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "deck" not in st.session_state:
    st.session_state.deck = []

def radar_svg(stats):
    labels = ["Attacco", "Difesa", "Stamina", "Peso", "Anti-Burst"]
    vals = [stats[k] for k in labels]
    cx, cy, r_max = 140, 130, 85
    pts_bg, pts_val, txt_svg = [], [], []
    for i, (lbl, v) in enumerate(zip(labels, vals)):
        ang = math.radians(-90 + i * 72)
        pts_bg.append(f"{cx + r_max * math.cos(ang):.1f},{cy + r_max * math.sin(ang):.1f}")
        rv = r_max * (max(1, min(10, v)) / 10.0)
        pts_val.append(f"{cx + rv * math.cos(ang):.1f},{cy + rv * math.sin(ang):.1f}")
        lx, ly = cx + (r_max + 24) * math.cos(ang), cy + (r_max + 18) * math.sin(ang)
        txt_svg.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">{lbl} ({v})</text>')
    return f'<svg width="290" height="260" viewBox="0 0 290 260"><polygon points="{" ".join(pts_bg)}" fill="#1e293b" stroke="#475569" stroke-width="1.5"/><polygon points="{" ".join(pts_val)}" fill="rgba(56, 189, 248, 0.45)" stroke="#38bdf8" stroke-width="2.5"/>{"".join(txt_svg)}</svg>'

def calc_stats(b_type, bit_type, w, burst_res, risk):
    atk = max(1, min(10, (9 if b_type == "Attack" else (6 if b_type == "Balance" else 3)) + (2 if bit_type == "Attack" else (1 if bit_type == "Balance" else -1))))
    dfs = max(1, min(10, (9 if b_type == "Defense" else (6 if b_type == "Balance" else 3)) + (2 if bit_type == "Defense" else (1 if bit_type == "Balance" else -1))))
    stm = max(1, min(10, (9 if b_type == "Stamina" else (6 if b_type == "Balance" else 3)) + (2 if bit_type == "Stamina" else (1 if bit_type == "Balance" else -1))))
    w_sc = max(1, min(10, round((w - 38.0) * 1.1)))
    br_sc = max(1, min(10, (8 if burst_res == "High" else 4) + (2 if risk == "Very Low" else (1 if risk == "Low" else (-2 if "High" in risk else 0)))))
    return {"Attacco": atk, "Difesa": dfs, "Stamina": stm, "Peso": w_sc, "Anti-Burst": br_sc}

def valuta(blade, ratchet, bit):
    score, pros, cons = 50, [], []
    is_int = "Ratchet-Integrated" in bit["name"]
    w = round(blade["weight_g"] + (0 if is_int else ratchet["weight_g"]) + bit["weight_g"], 2)
    h = round((6.0 if is_int else ratchet["height_mm"]) + bit["height_mod"], 1)
    risk = "Very Low" if is_int else ratchet["burst_risk"]
    if is_int: pros.append(f"Ratchet Integrato ({bit['name']}): zero gioco meccanico.")
    if w >= 46.5: score += 15; pros.append(f"Peso elevato ({w}g): grande stabilità e inerzia.")
    elif w < 41.0: score -= 12; cons.append(f"Combo leggera ({w}g): soffre gli impatti.")
    if blade["type"] == bit["type"]: score += 12; pros.append(f"Sinergia pura ({blade['type']}).")
    elif blade["weight_g"] >= 37.5 and bit["type"] in ["Stamina", "Defense"]: score += 15; pros.append("Meta Ibrida: Blade pesante stabilizza la punta.")
    if bit["burst_res"] == "Low" and risk in ["High", "Very High"]: score -= 25; cons.append(f"RISCHIO BURST ALTO: {bit['name']} + {ratchet['name']}.")
    elif bit["burst_res"] == "Low" and risk == "Very Low": score += 14; pros.append("Protezione Burst ottimale.")
    elif bit["burst_res"] == "High" and risk in ["Low", "Very Low"]: score += 10; pros.append("Resistenza Burst altissima.")
    if h <= 5.5 and blade["type"] == "Attack": score += 10; pros.append(f"Assetto ultra-basso ({h}mm).")
    elif h >= 8.0: score -= 8; cons.append(f"Baricentro alto ({h}mm).")
    return max(0, min(100, score)), w, h, pros, cons, calc_stats(blade["type"], bit["type"], w, bit["burst_res"], risk)

def valuta_ux_inf(u, bit):
    w = round(u["weight_g"] + bit["weight_g"], 2)
    h = round(u["height_mm"] + bit["height_mod"], 1)
    pros = ["UX Infinity (Ratchet Integrato): zero gioco meccanico e basso rischio Burst."]
    cons = []
    sc = 68 + (12 if u["type"] == bit["type"] else 0) + (10 if w >= 46.5 else 0) - (8 if h >= 8.0 else 0)
    if u["type"] == bit["type"]: pros.append(f"Sinergia pura ({u['type']}).")
    if w >= 46.5: pros.append(f"Peso elevato ({w}g): ottima stabilità.")
    if h >= 8.0: cons.append(f"Baricentro alto ({h}mm).")
    return max(0, min(100, sc)), w, h, pros, cons, calc_stats(u["type"], bit["type"], w, bit.get("burst_res", "High"), "Very Low")

def valuta_cx(lk, mb, ov, ab, r, bit, is_6):
    is_i = "Ratchet-Integrated" in bit["name"]
    w = round(lk["weight_g"] + mb["weight_g"] + (ov["weight_g"] if is_6 else 0.0) + ab["weight_g"] + (0 if is_i else r["weight_g"]) + bit["weight_g"], 2)
    h = round((6.0 if is_i else r["height_mm"]) + ab["height_mod"] + bit["height_mod"], 1)
    risk = "Low" if is_i else r["burst_risk"]
    pros, cons = [], []
    sc = 52 + (12 if lk["weight_g"] >= 4.5 else 0) + (12 if mb["type"] == bit["type"] else 0) + (15 if w >= 47.0 else 0) - (12 if h >= 8.0 else 0) - (20 if bit["burst_res"] == "Low" and risk in ["High", "Very High"] else 0)
    if lk["weight_g"] >= 4.5: pros.append("Metal Lock Chip: aumenta il peso centrale.")
    if mb["type"] == bit["type"]: pros.append(f"Coerenza di stile ({mb['type']}).")
    if w >= 47.0: pros.append(f"Peso elevato ({w}g): grande potenza d'impatto.")
    if h >= 8.0: cons.append(f"Assetto alto ({h}mm): rischio sbilanciamento.")
    if bit["burst_res"] == "Low" and risk in ["High", "Very High"]: cons.append(f"RISCHIO BURST ALTO: {bit['name']} + {r['name']}.")
    return max(0, min(100, sc)), w, h, pros, cons, calc_stats(mb["type"], bit["type"], w, bit["burst_res"], risk)

st.title("⚡ Beyblade X - Pro System & Arena 1vs1")
t1, t2, t3, t4, t5 = st.tabs(["🔍 Analizzatore & Radar", "⚔️ Simulatore 1vs1", "🤖 Suggeritore Top Combo", f"🏆 Deck Torneo ({len(st.session_state.deck)}/3)", "📦 La Mia Collezione"])

col_data = load_col()
filtra = lambda lista, cat, attivo: ([x for x in lista if x["name"] in col_data.get(cat, [])] or lista) if (attivo and col_data.get(cat, [])) else lista

def selettore_bey(cont, pref, lin, usa_col):
    if lin in ["1. BX", "2. UX", "4. BX Infinity"]:
        mappa = {"1. BX": db["bx_blades"], "2. UX": db["ux_blades"], "4. BX Infinity": db.get("bx_infinity", db["bx_blades"])}
        b = cont.selectbox("Blade", filtra(mappa[lin], "blades", usa_col), key=f"{pref}_b", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]")
        bit = cont.selectbox("Bit", filtra(db["bits"], "bits", usa_col), key=f"{pref}_bit", format_func=lambda x: f"{x['name']} ({x['type']})")
        is_i = "Ratchet-Integrated" in bit["name"]
        r = cont.selectbox("Ratchet", filtra(db["ratchets"], "ratchets", usa_col), key=f"{pref}_r", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)", disabled=is_i)
        return f"{b['name']} {'' if is_i else r['name'] + ' '}{bit['name']}", *valuta(b, r, bit), ([b["name"], bit["name"]] if is_i else [b["name"], r["name"], bit["name"]]), b["type"]
    elif lin == "5. UX Infinity":
        u = cont.selectbox("Blade UX Infinity", filtra(db["ux_infinity"], "blades", usa_col), key=f"{pref}_u", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
        bit = cont.selectbox("Bit", filtra([x for x in db["bits"] if "Ratchet-Integrated" not in x["name"]], "bits", usa_col), key=f"{pref}_ubit", format_func=lambda x: f"{x['name']} ({x['type']})")
        return f"{u['name']} + {bit['name']}", *valuta_ux_inf(u, bit), [u["name"], bit["name"]], u["type"]
    else:
        is_6 = (lin == "6. CX Infinity (6 Pezzi)")
        lk = cont.selectbox("Lock Chip", filtra(db["cx_lock_chips"], "cx_locks", usa_col), key=f"{pref}_lk", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
        mb = cont.selectbox("Metal Blade" if is_6 else "Main Blade", filtra(db["cx_metal_blades"] if is_6 else db["cx_main_blades"], "cx_metals" if is_6 else "cx_mains", usa_col), key=f"{pref}_mb", format_func=lambda x: f"{x['name']} [{x['type']} - {x['weight_g']}g]")
        ov = cont.selectbox("Over Blade", filtra(db["cx_over_blades"], "cx_overs", usa_col), key=f"{pref}_ov", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)") if is_6 else {"name": "", "weight_g": 0.0}
        ab = cont.selectbox("Assist Blade", filtra(db["cx_assist_blades"], "cx_assists", usa_col), key=f"{pref}_ab", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)")
        bit = cont.selectbox("Bit", filtra(db["bits"], "bits", usa_col), key=f"{pref}_cbit", format_func=lambda x: f"{x['name']} ({x['type']})")
        is_i = "Ratchet-Integrated" in bit["name"]
        r = cont.selectbox("Ratchet", filtra(db["ratchets"], "ratchets", usa_col), key=f"{pref}_cr", format_func=lambda x: f"{x['name']} ({x['weight_g']}g)", disabled=is_i)
        ov_txt = f" + {ov['name']}" if is_6 else ""
        pz = [lk["name"], mb["name"], ab["name"], bit["name"]] + ([ov["name"]] if is_6 else []) + ([] if is_i else [r["name"]])
        return f"{mb['name']} [{lk['name']}{ov_txt} + {ab['name']}] {'' if is_i else r['name'] + ' '}{bit['name']}", *valuta_cx(lk, mb, ov, ab, r, bit, is_6), pz, mb["type"]

solo_mia_col = t1.checkbox("Filtra menu usando solo i pezzi della Mia Collezione", value=False)
linea = t1.radio("Linea:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], horizontal=True)
nome, sc, w, h, pros, cons, st_rad, pezzi_usati, _ = selettore_bey(t1, "t1", linea, solo_mia_col)

t1.subheader(f"Combo: {nome}")
col_sx, col_dx = t1.columns([1.4, 1])
m1, m2, m3 = col_sx.columns(3)
m1.metric("Voto", f"{sc} / 100"); m2.metric("Peso", f"{w} g"); m3.metric("Altezza", f"{h} mm")
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
lin1 = s1.selectbox("Linea Blader 1:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], key="lin1")
nome1, sc1, w1, h1, _, _, st1, _, tp1 = selettore_bey(s1, "p1", lin1, False)
s2.markdown("### 🔴 Blader 2")
lin2 = s2.selectbox("Linea Blader 2:", ["1. BX", "2. UX", "3. CX (5 Pezzi)", "4. BX Infinity", "5. UX Infinity", "6. CX Infinity (6 Pezzi)"], index=2, key="lin2")
nome2, sc2, w2, h2, _, _, st2, _, tp2 = selettore_bey(s2, "p2", lin2, False)
p1_pts = sc1 + (w1 - w2) * 3.0 + (12 if (tp1 == "Attack" and tp2 == "Stamina") or (tp1 == "Stamina" and tp2 == "Defense") or (tp1 == "Defense" and tp2 == "Attack") else 0) + (8 if (h1 < h2 and tp1 == "Attack") else 0)
p2_pts = sc2 + (w2 - w1) * 3.0 + (12 if (tp2 == "Attack" and tp1 == "Stamina") or (tp2 == "Stamina" and tp1 == "Defense") or (tp2 == "Defense" and tp1 == "Attack") else 0) + (8 if (h2 < h1 and tp2 == "Attack") else 0)
prob1 = max(10, min(90, round((p1_pts / max(1, p1_pts + p2_pts)) * 100)))
prob2 = 100 - prob1
t2.divider()
res_c1, res_c2, res_c3 = t2.columns(3)
res_c1.metric(f"🔵 {nome1}", f"{prob1}% Vittoria", f"{w1}g | Voto {sc1}")
res_c2.metric("Differenza Peso", f"{round(abs(w1 - w2), 2)} g", f"Vantaggio {'Blader 1' if w1 >= w2 else 'Blader 2'}")
res_c3.metric(f"🔴 {nome2}", f"{prob2}% Vittoria", f"{w2}g | Voto {sc2}")
win_n, win_st, lose_h, lose_st = (nome1, st1, h2, st2) if prob1 >= prob2 else (nome2, st2, h1, st1)
cond_win = "Xtreme / Over Finish (2-3 pt) per impatto pesante" if win_st["Attacco"] >= 8 else ("Burst Finish (2 pt) su Ratchet esposto" if lose_h >= 7.5 or lose_st["Anti-Burst"] <= 4 else "Spin Finish (1 pt) per resistenza superiore al centro")
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
res_sug = sorted([(valuta(tb, r, b), f"{tb['name']} {r['name']} {b['name']}") for r in r_pool for b in b_pool], key=lambda x: x, reverse=True) if (calc_s and tb) else (sorted([(valuta_ux_inf(tu, b), f"{tu['name']} + {b['name']}") for b in b_pool], key=lambda x: x, reverse=True) if (calc_s and tu) else (sorted([(valuta_cx(tlk, tmb, tov, ab, r, b, is_6_s), f"{tmb['name']} [{tlk['name']}{ov_t} + {ab['name']}] {r['name']} {b['name']}") for ab in ab_pool for r in r_pool for b in b_pool], key=lambda x: x, reverse=True) if (calc_s and tlk) else []))
_ = [t3.info(f"#{i} — {c_name} | Voto: {v}/100 | Peso: {v}g | Altezza: {v}mm\n\n✅ {' • '.join(v) if v else 'Bilanciata'}\n\n⚠️ {' • '.join(v) if v else 'Nessun rischio'}") for i, (v, c_name) in enumerate(res_sug[:5], 1)]
t4.subheader("🏆 Il tuo Deck da 3 Beyblade (Regolamento 3on3)")
_ = not st.session_state.deck and t4.info("Il tuo Deck è vuoto. Costruisci una combo nella prima scheda e clicca su '➕ Aggiungi questa Combo al Deck Torneo'.")
tutti_pezzi_deck = [p for item in st.session_state.deck for p in item["pezzi"]]
duplicati = set([p for p in tutti_pezzi_deck if tutti_pezzi_deck.count(p) > 1])
_ = st.session_state.deck and duplicati and t4.error(f"⛔ DECK NON VALIDO DA TORNEO! Hai inserito pezzi duplicati: {', '.join(duplicati)}")
_ = st.session_state.deck and not duplicati and t4.success("✅ DECK VALIDO DA TORNEO: Nessun pezzo ripetuto tra i Beyblade!")
_ = st.session_state.deck and t4.metric("Media Competitiva del Deck", f"{round(sum(x['voto'] for x in st.session_state.deck) / len(st.session_state.deck), 1)} / 100")
_ = [t4.write(f"Bey #{i+1}: {it['nome']} — Voto: {it['voto']}/100 ({it['peso']}g)") for i, it in enumerate(st.session_state.deck)]
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