import pandas as pd
import streamlit as st

# formatting text, colors, ...
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    .stSelectbox div div div {
        color: white !important;
    }

    .stSelectbox div div input {
        color: white !important;
    }

    .block-container {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# mapping for flag codes
country_to_iso = {
    "United States": "us",
    "Australia": "au",
    "England": "gb",
    "Italy": "it",
    "Canada": "ca",
    "Venezuela": "ve",
    "Sweden": "se",
    "Colombia": "co",
    "Ireland": "ie",
    "Chinese Taipei": "tw",
    "New Zealand": "nz",
    "Argentina": "ar",
    "Puerto Rico": "pr",
    "Republic of Korea": "kr",
    "Japan": "jp",
    "Belgium": "be",
    "Denmark": "dk",
    "Norway": "no",
    "Germany": "de",
    "Chile": "cl",
    "South Africa": "za",
    "France": "fr",
    "Austria": "at",
    "Philippines": "ph",
    "Finland": "fi",
    "People's Rep of China": "cn"
}

# reading data and sorting by last name (so dropdown box is in alphabetical order)
player_df = pd.read_csv("pga_player_data.csv")
player_df = player_df.sort_values("lastName")

# calculating tour scoring average
tour_average = player_df["ScoringAvg"].mean(numeric_only=True)

# calculating current rank amongst field for official money and fedex points
player_df["FedExRank"] = player_df["FedEx"].rank(method="min", ascending=False).astype(int)
player_df["MoneyRank"] = player_df["Money"].rank(method="min", ascending=False).astype(int)

# list of golfers
golfer_names = player_df["fullName"].unique()

# setting default selected player to scottie
default_index = list(golfer_names).index("Scottie Scheffler")


##### app #####
st.markdown(
    f"""
    <h1 style="margin-bottom: -50px; margin-top: -20px;">
    2025 PGA Tour Metrics
    </h1>
    """,
    unsafe_allow_html=True
)

# select dropdown box to let user choose golfer
selected_golfer = st.selectbox(
    "",
    golfer_names,
    index = default_index
)

# pulling selected golfer's data
golfer_data = player_df[player_df["fullName"] == selected_golfer].iloc[0]

# generating headshot url
player_id = golfer_data["playerId"]
headshot_url = (
    "https://pga-tour-res.cloudinary.com/image/upload/"
    "c_fill,g_face:center,q_auto,f_auto,dpr_2.0,h_250,w_200,"
    "d_stub:default_avatar_light.webp/"
    f"headshots_{player_id}"
)

# generating public flag repo url
iso = country_to_iso.get(golfer_data["country"], "us")
flag_url = f"https://flagcdn.com/w40/{iso}.png"

# store rankings
fedex_rank = golfer_data["FedExRank"]
money_rank = golfer_data["MoneyRank"]

# ordinal numbers for ranks
import inflect

p = inflect.engine()
fedex_rank_ord = p.ordinal(int(fedex_rank))
money_rank_ord = p.ordinal(int(money_rank))

# main page content column widths
col1, col2 = st.columns([.35, .65], gap="medium")

# col1 - headshot, name, country and flag, rankings
with col1:
    st.markdown(
        f"""
        <div style="
            background-color:#f0f0f0;
            border-radius:8px;
            padding:15px;
        ">
            <img src='{headshot_url}' width='200'>
            <div style="
                font-size: 28px;
                font-weight: 700;
                margin-top: 8px;
                line-height: 1.5;
                ">
                {golfer_data['fullName']}
                </div>
            <p style='margin-top:8px;'>
                <img src='{flag_url}' style='vertical-align:middle;'> &nbsp;
                <strong>{golfer_data['country']}</strong>
            </p>
            <p><strong>FedEx Points:</strong> {int(golfer_data['FedEx'])} <br>
            <nobr>(Rank: {fedex_rank_ord})</nobr>
            </p>
            <p><strong>Official Money:</strong> ${int(golfer_data['Money']):,} <br>
            (Rank: {money_rank_ord})
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# col2 - sub sections displaying performative metrics
with col2:

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    r3c1, r3c2 = st.columns(2)
    columns = [r1c2, r2c1, r2c2, r3c1, r3c2]

    r1c1.markdown(
        f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 0.75rem;
                text-align: center;
                background-color: #f8f8f8;
            ">
                <div style="font-size:0.9rem; color:#666;">Scoring Average</div>
                <div style="font-size:1.5rem; font-weight:bold; color:"black";">
                    {round(golfer_data["ScoringAvg"], 3)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
    )

    # storing the selected golfers strokes grained metrics and rounding to 3rd decimal place
    sg_metrics = [
        ("Strokes Gained Total", round(golfer_data["SGTotal"],3)),
        ("Off the Tee", round(golfer_data["SGOffTee"],3)),
        ("On Approach", round(golfer_data["SGApproach"],3)),
        ("Around the Green", round(golfer_data["SGAround"],3)),
        ("Putting", round(golfer_data["SGPutting"],3))
    ]

    # display color based on better/worse than the field
    for col2, (label, val) in zip(columns, sg_metrics):
        if val > 0:
            color = "green"
        elif val < 0:
            color = "red"
        else:
            color = "black"

        col2.markdown(
            f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 0.75rem;
                text-align: center;
                background-color: #f8f8f8;
            ">
                <div style="font-size:0.9rem; color:#666;">{label}</div>
                <div style="font-size:1.5rem; font-weight:bold; color:{color};">
                    {val}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# spacing
st.markdown("<div style='margin-top:50px;'></div>", unsafe_allow_html=True)

# creating radar chart
import plotly.graph_objects as go

sg_total = round(golfer_data["SGTotal"], 3)
sg_off_tee = round(golfer_data["SGOffTee"], 3)
sg_approach = round(golfer_data["SGApproach"], 3)
sg_around = round(golfer_data["SGAround"], 3)
sg_putting = round(golfer_data["SGPutting"], 3)

categories = [
    "Total",
    "Off the Tee",
    "On Approach",
    "Around the Green",
    "Putting"
]

values = [
    sg_total,
    sg_off_tee,
    sg_approach,
    sg_around,
    sg_putting
]

# closing the loop
categories += [categories[0]]
values += [values[0]]

# initialize empty figure
fig = go.Figure()

# create chart
fig.add_trace(go.Scatterpolar(
    r=values,
    theta=categories,
    fill='toself',
    name=golfer_data["fullName"],
    line=dict(color="#005a23"),
    marker=dict(size=6),
    # only show value, remove name
    hovertemplate="%{r}<extra></extra>"
))

# make chart pretty
fig.update_layout(
    title=f"{golfer_data['fullName']} - Strokes Gained Profile",
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[-3, 3],
            tickfont_size=10
        )
    ),
    
    showlegend=False,
    margin=dict(l=20, r=20, t=40, b=20)
)

st.plotly_chart(fig, use_container_width=True)