import streamlit as st
import gspread
from google.oauth2 import service_account
from datetime import datetime
import pandas as pd
import plotly.express as px

# --- KONFIGURATION ---
SHEET_NAME = "bring-sally-up"  # <-- Name deines Google Sheets anpassen


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

    minuten = col3.number_input("⏱️ Dauer (Sekunden)", min_value=0, step=1)

    submit = st.form_submit_button("💾 Eintrag speichern", use_container_width=True)

# --- SPEICHERN ---
if submit:
    sheet = connect_to_sheet()
    if sheet:
        try:
            with st.spinner("Speichere..."):
                sheet.append_row([name, str(datum), int(minuten)])
            st.success(f"✅ Gut gemacht {name}! Eintrag gespeichert.")
            st.balloons()
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
            df["Datum"] = pd.to_datetime(df["Datum"])
            df["Sekunden"] = pd.to_numeric(df["Sekunden"], errors="coerce")

            # --- STATISTIKEN ---
            st.subheader("📊 Statistiken")

            namen = df["Name"].unique()
            cols = st.columns(len(namen))

            for i, name in enumerate(namen):
                person_df = df[df["Name"] == name]
                avg = person_df["Sekunden"].mean()
                best = person_df["Sekunden"].max()
                eintraege = len(person_df)
                with cols[i]:
                    st.metric(f"⌀ {name}", f"{avg:.0f} Sek")
                    st.caption(f"🏆 Bestzeit: {best:.0f} Sek | {eintraege} Versuche")

            st.divider()

            # --- LINIEN GRAPH ---
            st.subheader("📈 Fortschritt über die Zeit")

            fig = px.line(
                df.sort_values("Datum"),
                x="Datum",
                y="Sekunden",
                color="Name",
                markers=True,
                line_shape="spline",
                labels={"Sekunden": "Dauer (Sekunden)", "Datum": "Datum"},
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend_title="Person",
                hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
                yaxis=dict(showgrid=True, gridcolor="#eeeeee"),
                font=dict(size=14),
                height=450
            )

            fig.update_traces(line=dict(width=3), marker=dict(size=8))

            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # --- TABELLE ---
            st.subheader("📋 Alle Einträge")
            st.dataframe(
                df.sort_values("Datum", ascending=False).reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("Noch keine Einträge. Füge deinen ersten Eintrag hinzu!")

    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")