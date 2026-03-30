import streamlit as st
import gspread
from google.oauth2 import service_account
from datetime import datetime
import pandas as pd
import plotly.express as px

# --- KONFIGURATION ---
SHEET_NAME = "bring-sally-up"

# --- VERBINDUNG ---
def connect_to_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

# --- HILFSFUNKTION ---
def sekunden_zu_mmss(sek):
    sek = int(sek)
    m = sek // 60
    s = sek % 60
    return f"{m}:{s:02d}"

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Bring Sally Up", page_icon="💪", layout="wide")
st.title("💪 Bring Sally Up – WG Tracker")
st.caption("Wer hält am längsten durch?")

st.divider()

# --- FORMULAR ---
with st.form("sally_form", clear_on_submit=True):
    st.subheader("Neuer Eintrag")

    col1, col2, col3 = st.columns(3)
    name = col1.selectbox("👤 Name", ["Till", "Jonas", "Jaro", "Eileen"])
    datum = col2.date_input("📅 Datum", datetime.now())
    zeit_input = col3.text_input("⏱️ Zeit (M:SS)", placeholder="z.B. 3:45")

    submit = st.form_submit_button("💾 Eintrag speichern", use_container_width=True)

# --- SPEICHERN ---
if submit:
    gesamt_sekunden = None
    try:
        teile = zeit_input.strip().split(":")
        if len(teile) == 2:
            gesamt_sekunden = int(teile[0]) * 60 + int(teile[1])
        else:
            st.error("⚠️ Bitte Zeit im Format M:SS eingeben, z.B. 3:45")
    except:
        st.error("⚠️ Ungültiges Format. Bitte M:SS eingeben, z.B. 3:45")

    if gesamt_sekunden is not None:
        sheet = connect_to_sheet()
        if sheet:
            try:
                # Prüfen ob Bestzeit
                alle_daten = sheet.get_all_records()
                ist_bestzeit = True
                if alle_daten:
                    df_check = pd.DataFrame(alle_daten)
                    df_check.columns = ["Name", "Datum", "Sekunden"]
                    df_check["Sekunden"] = pd.to_numeric(df_check["Sekunden"], errors="coerce")
                    person_werte = df_check[df_check["Name"] == name]["Sekunden"].dropna()
                    if not person_werte.empty:
                        ist_bestzeit = gesamt_sekunden > int(person_werte.max())

                with st.spinner("Speichere..."):
                    sheet.append_row([name, str(datum), gesamt_sekunden])

                if ist_bestzeit:
                    banner = st.empty()
                    banner.markdown(f"""
                    <style>
                    @keyframes pushup {{
                        0%   {{ transform: translateY(0px); }}
                        50%  {{ transform: translateY(-12px); }}
                        100% {{ transform: translateY(0px); }}
                    }}
                    @keyframes glow {{
                        0%   {{ box-shadow: 0 0 20px rgba(255,215,0,0.6); }}
                        50%  {{ box-shadow: 0 0 50px rgba(255,165,0,1); }}
                        100% {{ box-shadow: 0 0 20px rgba(255,215,0,0.6); }}
                    }}
                    .bestzeit-banner {{
                        background: linear-gradient(135deg, #FFD700, #FF8C00);
                        border-radius: 20px;
                        padding: 2.5rem;
                        text-align: center;
                        animation: glow 1.5s ease-in-out infinite;
                        margin: 1rem 0;
                    }}
                    .pushup-emoji {{
                        font-size: 4rem;
                        display: inline-block;
                        animation: pushup 0.6s ease-in-out infinite;
                    }}
                    </style>
                    <div class="bestzeit-banner">
                        <div style="font-size: 1rem; letter-spacing: 4px; color: white; font-weight: 700; opacity: 0.9;">🎉 NEUE</div>
                        <div style="font-size: 3rem; font-weight: 900; color: white; text-shadow: 3px 3px 6px rgba(0,0,0,0.2); line-height: 1.1;">
                            BESTZEIT!
                        </div>
                        <div style="font-size: 1.5rem; color: white; margin-top: 0.5rem; font-weight: 600;">
                            {name} &nbsp;–&nbsp; {zeit_input} ⏱️
                        </div>
                        <div class="pushup-emoji" style="margin-top: 1rem;">🤻</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                    import time
                    time.sleep(3)
                    banner.empty()
                else:
                    msg = st.empty()
                    msg.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #2c2c2c, #444);
                        border-radius: 16px;
                        padding: 1.5rem 2rem;
                        text-align: center;
                        margin: 1rem 0;
                        border: 1px solid #555;
                    ">
                        <div style="font-size: 2rem;">😤</div>
                        <div style="font-size: 1.4rem; font-weight: 700; color: #ccc;">
                            Heute leider keine Bestzeit.
                        </div>
                        <div style="font-size: 1.1rem; color: #aaa; margin-top: 0.3rem;">
                            Keep on pushing, {name}! 💪
                        </div>
                        <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                            Gespeichert: {zeit_input}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    import time
                    time.sleep(3)
                    msg.empty()

            except Exception as e:
                st.error(f"Speicherfehler: {e}")

st.divider()

# --- DATEN LADEN ---
sheet = connect_to_sheet()
if sheet:
    try:
        with st.spinner("Lade Daten..."):
            data = sheet.get_all_records()

        if data:
            df = pd.DataFrame(data)
            df.columns = ["Name", "Datum", "Sekunden"]
            df["Datum"] = pd.to_datetime(df["Datum"], format="mixed", dayfirst=True)
            df["Sekunden"] = pd.to_numeric(df["Sekunden"], errors="coerce")
            df = df.dropna(subset=["Sekunden"])
            df["Sekunden"] = df["Sekunden"].astype(int)

            # --- STATISTIKEN ---
            st.subheader("📊 Statistiken")

            namen = df["Name"].unique()
            cols = st.columns(len(namen))

            for i, n in enumerate(namen):
                person_df = df[df["Name"] == n].sort_values("Datum")
                avg = person_df["Sekunden"].mean()
                best = person_df["Sekunden"].max()
                eintraege = len(person_df)

                # Anzahl Tage mit 4:00 Min erreicht
                tage_ziel = int((person_df["Sekunden"] >= 240).sum())

                # Längster Streak mit >= 4:00 Min
                streak = 0
                max_streak = 0
                for sek in person_df["Sekunden"]:
                    if sek >= 240:
                        streak += 1
                        max_streak = max(max_streak, streak)
                    else:
                        streak = 0

                # Aktueller Streak
                akt_streak = 0
                for sek in reversed(person_df["Sekunden"].tolist()):
                    if sek >= 240:
                        akt_streak += 1
                    else:
                        break

                with cols[i]:
                    st.metric(f"⌀ {n}", sekunden_zu_mmss(avg))
                    st.caption(f"🏆 Bestzeit: {sekunden_zu_mmss(best)} | {eintraege} Versuche")
                    st.caption(f"🎯 4:00 erreicht: {tage_ziel}x")
                    st.caption(f"🔥 Längster Streak: {max_streak} Tage | Aktuell: {akt_streak} Tage")

            st.divider()

            # --- LINIEN GRAPH ---
            st.subheader("📈 Fortschritt über die Zeit")

            df["Zeit"] = df["Sekunden"].apply(sekunden_zu_mmss)

            fig = px.line(
                df.sort_values("Datum"),
                x="Datum",
                y="Sekunden",
                color="Name",
                markers=True,
                line_shape="spline",
                hover_data={"Zeit": True, "Sekunden": False},
                labels={"Sekunden": "Dauer (Sek)", "Datum": "Datum"},
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            max_sek = int(df["Sekunden"].max())
            tick_vals = list(range(0, max_sek + 60, 30))
            tick_text = [sekunden_zu_mmss(v) for v in tick_vals]

            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend_title="Person",
                hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#eeeeee",
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    title="Dauer (MM:SS)"
                ),
                font=dict(size=14),
                height=450
            )

            fig.update_traces(line=dict(width=3), marker=dict(size=8))

            # --- LINEARE REGRESSION ---
            from sklearn.linear_model import LinearRegression
            import numpy as np

            ZIEL_SEKUNDEN = 240  # 4:00 Minuten
            farben = px.colors.qualitative.Set2
            prognosen = []

            for i, n in enumerate(namen):
                person_df = df[df["Name"] == n].sort_values("Datum")
                if len(person_df) >= 2:
                    erster_tag = person_df["Datum"].min()
                    X = (person_df["Datum"] - erster_tag).dt.days.values.reshape(-1, 1)
                    y = person_df["Sekunden"].values

                    model = LinearRegression()
                    model.fit(X, y)

                    if model.coef_[0] > 0:
                        # Schätze wann 240 Sek erreicht
                        tage_bis_ziel = int((ZIEL_SEKUNDEN - model.intercept_) / model.coef_[0])
                        ziel_datum = erster_tag + pd.Timedelta(days=tage_bis_ziel)

                        # Trendlinie zeichnen
                        x_range = np.linspace(0, max(tage_bis_ziel, int(X.max())), 100)
                        y_range = model.predict(x_range.reshape(-1, 1))
                        datum_range = [erster_tag + pd.Timedelta(days=int(d)) for d in x_range]

                        farbe = farben[i % len(farben)]
                        fig.add_scatter(
                            x=datum_range,
                            y=y_range,
                            mode="lines",
                            name=f"{n} (Trend)",
                            line=dict(dash="dash", width=2, color=farbe),
                            opacity=0.5,
                            showlegend=True
                        )
                        prognosen.append((n, ziel_datum, farbe))

            # Ziellinie bei 4:00
            fig.add_hline(
                y=ZIEL_SEKUNDEN,
                line_dash="dot",
                line_color="red",
                line_width=2,
                annotation_text="🎯 Ziel: 4:00",
                annotation_position="top right"
            )

            # Y-Achse anpassen inkl. Ziel
            max_sek = max(int(df["Sekunden"].max()), ZIEL_SEKUNDEN)
            tick_vals = list(range(0, max_sek + 60, 30))
            tick_text = [sekunden_zu_mmss(v) for v in tick_vals]
            fig.update_layout(
                yaxis=dict(
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    title="Dauer (MM:SS)",
                    range=[0, max_sek + 30]
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- PROGNOSE KARTEN ---
            if prognosen:
                st.subheader("🎯 Prognose: Wann wird 4:00 Min erreicht?")
                prog_cols = st.columns(len(prognosen))
                for i, (n, ziel_datum, _) in enumerate(prognosen):
                    tage_noch = (ziel_datum - pd.Timestamp.now()).days
                    with prog_cols[i]:
                        if tage_noch > 0:
                            st.metric(f"📅 {n}", ziel_datum.strftime("%d.%m.%Y"), f"noch {tage_noch} Tage")
                        else:
                            st.metric(f"📅 {n}", "Ziel erreicht! 🏆")

            st.divider()

            # --- TABELLE ---
            st.subheader("📋 Alle Einträge")
            df_anzeige = df[["Name", "Datum", "Zeit"]].copy()
            df_anzeige.columns = ["Name", "Datum", "Zeit (MM:SS)"]
            st.dataframe(
                df_anzeige.sort_values("Datum", ascending=False).reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("Noch keine Einträge. Füge deinen ersten Eintrag hinzu!")

    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")