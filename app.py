import streamlit as st
import pandas as pd
import json
import os
import random
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Sceriffi Stats Center 🏆", layout="wide")

# DATI BASE FISSI
BASE_ALL_TIME = { "Cosimo": 595, "Alessio DI": 450, "Simone": 191 }
BASE_2026 = { "Cosimo": 112, "Alessio DI": 89, "Simone": 22 }
NOMI = list(BASE_ALL_TIME.keys())
COLORI = ['#38bdf8', '#fbbf24', '#34d399']

# FILE DATABASE CONDIVISO (Sul server)
DB_FILE = "sceriffi_db_v2.json"

def carica_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def salva_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = carica_db()

# --- INPUT DI GIOCO (Nomi temporanei per il sorteggio) ---
if 'nomi_sorteggio' not in st.session_state:
    st.session_state.nomi_sorteggio = NOMI.copy()

# Titolo Principale
st.markdown("<h1 style='text-align: center;'>🏆 Portale Sceriffi</h1>", unsafe_allow_html=True)

# Layout a schede (Tabs) per un'interfaccia pulita
tab_sorteggio, tab_calendario, tab_classifiche = st.tabs(["🎡 Sorteggio Scontri", "📅 Calendario Live", "📊 Classifiche & Analisi"])

# ==========================================
# TAB 1: SORTEGGIO SCONTRI
# ==========================================
with tab_sorteggio:
    st.subheader("🎡 Sorteggio Scontri")
    
    # Modifica nomi temporanei
    with st.expander("✏️ Modifica nomi per questo sorteggio (Scherzi/Soprannomi)"):
        nomi_input = st.text_input("Nomi separati da virgola:", value=", ".join(st.session_state.nomi_sorteggio))
        if st.button("Aggiorna Nomi Temporanei"):
            st.session_state.nomi_sorteggio = [n.strip() for n in nomi_input.split(",") if n.strip()]
            st.success("Nomi aggiornati per il sorteggio!")

    col_w1, col_w2 = st.columns(2)
    
    if st.button("🔥 SFIDA!", use_container_width=True):
        if len(st.session_state.nomi_sorteggio) >= 2:
            p1 = random.choice(st.session_state.nomi_sorteggio)
            p2 = random.choice(st.session_state.nomi_sorteggio)
            while p1 == p2:
                p2 = random.choice(st.session_state.nomi_sorteggio)
            
            st.markdown(f"<h2 style='text-align: center; color: #fbbf24;'>{p1} ⚔️ {p2}</h2>", unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("Servono almeno 2 giocatori per il sorteggio!")

# ==========================================
# TAB 2: CALENDARIO LIVE
# ==========================================
with tab_calendario:
    st.subheader("📅 Gestione Calendario Giornaliero")
    
    # Selettore Data di Streamlit (Molto più comodo)
    data_selezionata = st.date_input("Seleziona il giorno da modificare o visualizzare:", datetime.now())
    data_key = data_selezionata.strftime("%Y-%m-%d")
    
    st.markdown(f"### Giorno: `{data_selezionata.strftime('%d/%m/%Y')}`")
    
    # Form per modificare i punteggi del giorno
    punti_giorno = db.get(data_key, {n: 0 for n in NOMI})
    
    col_inputs = st.columns(len(NOMI))
    nuovi_punti = {}
    for i, n in enumerate(NOMI):
        with col_inputs[i]:
            nuovi_punti[n] = st.number_input(f"Stelle per {n}", min_value=0, value=punti_giorno.get(n, 0), step=1, key=f"in_{n}")
            
    if st.button("Salva Punteggio Giorno"):
        # Se tutti i punti sono 0, elimina il giorno dal DB
        if sum(nuovi_punti.values()) == 0:
            if data_key in db:
                del db[data_key]
        else:
            db[data_key] = nuovi_punti
        salva_db(db)
        st.success("Dati salvati sul server!")
        st.rerun()

# ==========================================
# TAB 3: CLASSIFICHE & ANALISI
# ==========================================
with tab_classifiche:
    st.subheader("📊 Classifiche e Rendimento")
    
    # Selezione Mese/Anno per filtri statistici
    oggi = datetime.now()
    col_m, col_y = st.columns(2)
    with col_m:
        mese_sel = st.selectbox("Seleziona Mese per analisi:", list(range(1, 13)), index=oggi.month-1, format_func=lambda x: calendar.month_name[x].upper())
    with col_y:
        anno_sel = st.selectbox("Seleziona Anno per analisi:", [2026, 2027, 2028], index=0)
        
    year_key = str(anno_sel)
    month_key = f"{mese_sel:02d}"
    
    # Ricalcolo Statistiche
    stats_mese = {n: 0 for n in NOMI}
    stats_anno = {n: (BASE_2026[n] if year_key == "2026" else 0) for n in NOMI}
    stats_all = {n: BASE_ALL_TIME[n] for n in NOMI}
    
    for k, v in db.items():
        y, m, d = k.split('-')
        for n in NOMI:
            punti = v.get(n, 0)
            stats_all[n] += punti
            if y == year_key:
                stats_anno[n] += punti
            if y == year_key and m == month_key:
                stats_mese[n] += punti

    # Visualizzazione Classifiche in Colonne
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"#### 🔵 MENSILE ({calendar.month_name[mese_sel].upper()})")
        st.dataframe(pd.Series(stats_mese).sort_values(ascending=False), column_config={"value": "Stelle ⭐"}, use_container_width=True)
    with c2:
        st.markdown(f"#### 🟢 ANNUALE ({year_key})")
        st.dataframe(pd.Series(stats_anno).sort_values(ascending=False), column_config={"value": "Stelle ⭐"}, use_container_width=True)
    with c3:
        st.markdown("#### 🌍 ALL TIME")
        st.dataframe(pd.Series(stats_all).sort_values(ascending=False), column_config={"value": "Stelle ⭐"}, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 💡 RECORD DEL MESE (Esclusi i Weekend)")
    
    # LOGICA DI CALCOLO STRISCE E LETARGHI (SOLO LUN-VEN DEL MESE SELEZIONATO)
    num_giorni_mese = calendar.monthrange(anno_sel, mese_sel)[1]
    giorni_lavorativi = []
    for d in range(1, num_giorni_mese + 1):
        if calendar.weekday(anno_sel, mese_sel, d) < 5: # Da 0 (Lunedì) a 4 (Venerdì)
            giorni_lavorativi.append(f"{year_key}-{month_key}-{d:02d}")
            
    streaks = {n: {"max": 0, "curr": 0} for n in NOMI}
    letarghi = {n: {"max": 0, "curr": 0} for n in NOMI}
    fotofinish = {n: 0 for n in NOMI}
    
    # Calcolo Strisce e Letarghi
    for k in giorni_lavorativi:
        for n in NOMI:
            pts = db.get(k, {}).get(n, 0)
            if pts > 0:
                streaks[n]["curr"] += 1
                streaks[n]["max"] = max(streaks[n]["max"], streaks[n]["curr"])
                letarghi[n]["curr"] = 0
            else:
                streaks[n]["curr"] = 0
                letarghi[n]["curr"] += 1
                letarghi[n]["max"] = max(letarghi[n]["max"], letarghi[n]["curr"])
                
    # Calcolo Fotofinish (Ultimi 3 giorni lavorativi)
    for k in giorni_lavorativi[-3:]:
        for n in NOMI:
            fotofinish[n] += db.get(k, {}).get(n, 0)
            
    killer_name = max(fotofinish, key=fotofinish.get)
    killer_val = fotofinish[killer_name]
    killer_display = f"{killer_name} ({killer_val} ⭐)" if killer_val > 0 else "Nessuno"

    # Display dei record in colonne grafiche
    rec1, rec2, rec3 = st.columns(3)
    with rec1:
        st.metric("🔥 Striscia di Fuoco Massima", f"{max(streaks, key=lambda x: streaks[x]['max'])}", f"{max(streaks[n]['max'] for n in NOMI)} giorni")
    with rec2:
        st.metric("💤 Il Letargo Massimo", f"{max(letarghi, key=lambda x: letarghi[x]['max'])}", f"{max(letarghi[n]['max'] for n in NOMI)} giorni")
    with rec3:
        st.metric("📈 Killer del Fotofinish", killer_display)

    # GRAFICI CON STREAMLIT NATIVO
    st.markdown("### 📈 Grafici di Performance")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### Distribuzione Mese Corrente")
        st.bar_chart(pd.Series(stats_mese))
    with g2:
        st.markdown("#### Performance Storica All Time")
        st.line_chart(pd.Series(stats_all))

# Bottone di Reset Totale in fondo
st.markdown("<br><br><br>", unsafe_allow_html=True)
if st.button("🗑️ RESETTA SOLO LIVE CONDIVISO", type="primary"):
    if st.checkbox("Confermo di voler azzerare il database sul server"):
        salva_db({})
        st.success("Database azzerato!")
        st.rerun()
