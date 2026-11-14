import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

# Page configuration
st.set_page_config(
    page_title="Eartheareal | Earth & Climate Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #07111f;
        color: #e5edf7;
    }
    [data-testid="stSidebar"] {
        background-color: #0c1929;
        border-right: 1px solid #1b3045;
    }
    [data-testid="stHeader"] {
        background-color: transparent;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }
    .brand {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #e5edf7;
    }
    .brand span {
        color: #22d3c5;
    }
    .subtitle {
        color: #8ca3bb;
        font-size: 13px;
        margin-top: 3px;
    }
    .section-title {
        font-size: 19px;
        font-weight: 700;
        color: #e5edf7;
        margin-bottom: 5px;
    }
    .section-description {
        color: #8ca3bb;
        font-size: 12px;
        margin-bottom: 15px;
    }
    .metric-card {
        background: linear-gradient(145deg, #10253a, #0c1c2e);
        border: 1px solid #1d3a50;
        border-radius: 12px;
        padding: 18px;
        min-height: 112px;
    }
    .metric-label {
        color: #8ca3bb;
        font-size: 12px;
        font-weight: 500;
    }
    .metric-value {
        color: #e5edf7;
        font-size: 27px;
        font-weight: 700;
        margin-top: 8px;
    }
    .metric-caption {
        color: #22d3c5;
        font-size: 11px;
        margin-top: 3px;
    }
    .status-pill {
        background-color: #173b40;
        color: #48e0cf;
        border: 1px solid #23615f;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .info-panel {
        background-color: #0c1c2e;
        border: 1px solid #1d3a50;
        border-radius: 12px;
        padding: 18px;
    }
    .footer {
        color: #60788f;
        font-size: 11px;
        text-align: center;
        padding: 20px 0;
        border-top: 1px solid #1b3045;
    }
    hr {
        border-color: #1b3045;
    }
</style>
""", unsafe_allow_html=True)

# Placeholder data
rng = np.random.default_rng(42)
sample_locations = pd.DataFrame({
    "location": [
        "Philippines", "Japan", "Indonesia", "India",
        "Australia", "Brazil", "United States", "Canada",
        "China", "South Africa", "United Kingdom",
        "Madagascar", "Mexico", "Egypt", "New Zealand",
        "Argentina", "Thailand", "Kenya", "France", "Chile"
    ],
    "latitude": [
        12.8, 36.2, -2.5, 20.6, -25.3, -14.2,
        37.1, 56.1, 35.9, -30.6, 55.3,
        -19.0, 23.6, 26.8, -40.9, -38.4,
        15.8, 0.0, 46.2, -35.7
    ],
    "longitude": [
        121.8, 138.2, 118.0, 78.9, 133.8, -51.9,
        -96.7, -106.3, 104.2, 22.9, -3.4,
        46.7, -102.5, 30.8, 174.9, -63.6,
        101.0, 37.9, 2.2, -71.5
    ]
})
sample_locations["value"] = rng.uniform(0, 100, len(sample_locations))

dates = pd.date_range(start="2020-01-01", periods=72, freq="MS")
trend_data = pd.DataFrame({
    "date": dates,
    "temperature": (
        25 + 0.025 * np.arange(72)
        + 2.5 * np.sin(np.arange(72) * 2 * np.pi / 12)
        + rng.normal(0, 0.5, 72)
    ),
    "precipitation": (
        150 + 45 * np.sin(np.arange(72) * 2 * np.pi / 12)
        + rng.normal(0, 12, 72)
    ),
    "vegetation": (
        0.55 + 0.08 * np.sin(np.arange(72) * 2 * np.pi / 12)
        + rng.normal(0, 0.015, 72)
    )
})

# Sidebar
with st.sidebar:
    st.markdown("""
    <div class="brand">EARTH<span>WATCH</span></div>
    <div class="subtitle">Earth & Climate Explorer</div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio(
        "Navigate",
        ["Overview", "Explore Earth", "Historical Trends", "About"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("### Map Configuration")
    selected_layer = st.selectbox(
        "Climate Layer",
        ["Temperature", "Precipitation", "Cloud Cover", "Vegetation Index"]
    )
    selected_date = st.date_input("Observation Date", value=date(2024, 6, 15))
    selected_time = st.select_slider(
        "Time (UTC)",
        options=["00:00", "06:00", "12:00", "18:00"],
        value="12:00"
    )
    opacity = st.slider("Layer Opacity", min_value=0, max_value=100, value=75)
    show_markers = st.checkbox("Show sample observation markers", value=True)
    st.markdown("---")
    st.markdown("### Data Status")
    st.markdown(
        '<span class="status-pill">● DEMO MODE</span>',
        unsafe_allow_html=True
    )
    st.caption("No external datasets are currently connected.")

# Reusable Components
def section_header(title, description=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if description:
        st.markdown(f'<div class="section-description">{description}</div>', unsafe_allow_html=True)

def metric_card(label, value, caption):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-caption">{caption}</div>
    </div>
    """, unsafe_allow_html=True)

def create_world_map(layer, markers=True):
    color_settings = {
        "Temperature": ("Plasma", "Temperature (°C)"),
        "Precipitation": ("Blues", "Precipitation (mm)"),
        "Cloud Cover": ("Greys", "Cloud Cover (%)"),
        "Vegetation Index": ("Greens", "Vegetation Index")
    }
    colorscale, colorbar_title = color_settings[layer]
    values = sample_locations["value"]
    if layer == "Temperature":
        values = 15 + values * 0.25
    elif layer == "Precipitation":
        values = values * 10
    elif layer == "Cloud Cover":
        values = values
    else:
        values = values / 100

    fig = go.Figure()
    if markers:
        fig.add_trace(go.Scattergeo(
            lat=sample_locations["latitude"],
            lon=sample_locations["longitude"],
            text=sample_locations["location"],
            mode="markers",
            marker=dict(
                size=11,
                color=values,
                colorscale=colorscale,
                opacity=opacity / 100,
                colorbar=dict(
                    title=colorbar_title,
                    thickness=12,
                    tickfont=dict(color="#b7c9da")
                ),
                line=dict(color="#d5f4f1", width=0.5)
            ),
            hovertemplate="<b>%{text}</b><br>Latitude: %{lat:.2f}<br>Longitude: %{lon:.2f}<br>Value: %{marker.color:.2f}<extra></extra>"
        ))
    fig.update_geos(
        projection_type="natural earth",
        showland=True, landcolor="#162b3d",
        showocean=True, oceancolor="#081726",
        showcoastlines=True, coastlinecolor="#31536a",
        showcountries=True, countrycolor="#294255",
        showframe=False, bgcolor="#081726"
    )
    fig.update_layout(
        height=510, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#0c1c2e", plot_bgcolor="#0c1c2e",
        font=dict(color="#dce8f3"), geo=dict(bgcolor="#0c1c2e")
    )
    return fig

def create_trend_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_data["date"],
        y=trend_data["temperature"],
        name="Temperature",
        mode="lines",
        line=dict(width=2.5, color="#22d3c5"),
        fill="tozeroy",
        fillcolor="rgba(34,211,197,0.08)"
    ))
    fig.update_layout(
        height=320, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="#0c1c2e", plot_bgcolor="#0c1c2e",
        font=dict(color="#b7c9da"),
        xaxis=dict(title="Date", gridcolor="#1b3045"),
        yaxis=dict(title="Temperature (°C)", gridcolor="#1b3045"),
        legend=dict(orientation="h", y=1.12)
    )
    return fig

# App header
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("""
    <div class="brand">EARTH<span>WATCH</span></div>
    <div class="subtitle">Explore our planet through climate and Earth observation data.</div>
    """, unsafe_allow_html=True)
with header_col2:
    st.markdown('<div style="text-align:right; padding-top:12px;"><span class="status-pill">● SYSTEM ONLINE</span></div>', unsafe_allow_html=True)
st.markdown("---")

# Pages routing
if page == "Overview":
    st.markdown("## Global Earth Overview")
    st.caption(f"Selected layer: {selected_layer} | Date: {selected_date} | Time: {selected_time} UTC")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("GLOBAL TEMPERATURE", "24.8 °C", "Simulated global average")
    with col2:
        metric_card("PRECIPITATION", "112.4 mm", "Simulated monthly average")
    with col3:
        metric_card("CLOUD COVER", "64.2%", "Simulated global coverage")
    with col4:
        metric_card("VEGETATION INDEX", "0.68", "Simulated NDVI")
    st.markdown("")
    section_header("Interactive Global Map", "Explore simulated climate observations across the globe.")
    search_col, info_col = st.columns([3, 1])
    with search_col:
        location_search = st.text_input("Search location", placeholder="Enter a city, country, or coordinates...")
    with info_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Search", width='stretch'):
            if location_search:
                st.info("Location search will be connected to a geocoding service in a future version.")
    st.plotly_chart(create_world_map(selected_layer, show_markers), width='stretch')
    st.caption("DEMO VISUALIZATION — Markers and values are simulated. No live satellite or climate data are displayed.")
    st.markdown("---")
    section_header("Global Climate Trends", "Example of how historical climate data will be presented.")
    st.plotly_chart(create_trend_chart(), width='stretch')

elif page == "Explore Earth":
    st.markdown("## Explore Earth")
    st.caption("Interact with different Earth observation layers and explore spatial patterns.")
    left, right = st.columns([3, 1])
    with left:
        section_header("Global Visualization", f"Currently displaying: {selected_layer}")
        st.plotly_chart(create_world_map(selected_layer, show_markers), width='stretch')
    with right:
        section_header("Layer Information")
        layer_descriptions = {
            "Temperature": "Surface temperature observations and spatial temperature distributions.",
            "Precipitation": "Rainfall distribution and precipitation patterns across the globe.",
            "Cloud Cover": "Cloud coverage and atmospheric conditions.",
            "Vegetation Index": "Vegetation health and greenness using indices such as NDVI."
        }
        st.markdown(f'<div class="info-panel">{layer_descriptions[selected_layer]}</div>', unsafe_allow_html=True)
        st.markdown("")
        st.markdown("**Selected date**")
        st.write(selected_date)
        st.markdown("**Selected time**")
        st.write(selected_time, "UTC")
        st.markdown("**Layer opacity**")
        st.progress(opacity / 100)
        st.markdown("---")
        st.info("Satellite imagery, raster layers, and spatial NetCDF processing will be integrated later.")

elif page == "Historical Trends":
    st.markdown("## Historical Climate Trends")
    st.caption("Explore temporal changes in selected climate variables.")
    variable = st.selectbox("Select variable", ["Temperature", "Precipitation", "Vegetation Index"])
    column_mapping = {
        "Temperature": ("temperature", "Temperature (°C)"),
        "Precipitation": ("precipitation", "Precipitation (mm)"),
        "Vegetation Index": ("vegetation", "NDVI")
    }
    column_name, axis_title = column_mapping[variable]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_data["date"], y=trend_data[column_name], mode="lines", name=variable,
        line=dict(color="#22d3c5", width=2.5),
        fill="tozeroy", fillcolor="rgba(34,211,197,0.08)"
    ))
    fig.update_layout(
        height=430, paper_bgcolor="#0c1c2e", plot_bgcolor="#0c1c2e", font=dict(color="#dce8f3"),
        xaxis=dict(title="Date", gridcolor="#1b3045"),
        yaxis=dict(title=axis_title, gridcolor="#1b3045"),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown("---")
    section_header("Historical Data Table", "Preview of the format for future climate datasets.")
    st.dataframe(trend_data, width='stretch', hide_index=True)
    st.warning("Historical values are simulated placeholders, not actual measurements.")

elif page == "About":
    st.markdown("## About EarthWatch")
    st.markdown("""
    <div class="info-panel">
        <h3 style="color:#22d3c5;">Understanding our changing planet.</h3>
        EarthWatch is an interactive Earth and climate visualization
        platform designed to make geospatial and environmental data
        more accessible.<br><br>
        The platform aims to combine satellite imagery, climate
        observations, and historical datasets into a unified
        interactive environment.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")
    section_header("Planned Features")
    features = [
        ("🌍", "Interactive Global Map", "Explore the Earth through an interactive spatial interface."),
        ("🛰️", "Satellite Imagery", "Visualize satellite observations and cloud coverage."),
        ("🌡️", "Climate Layers", "Explore temperature, precipitation, and vegetation."),
        ("📅", "Temporal Exploration", "Navigate historical observations using date and time controls."),
        ("📊", "Climate Analytics", "Examine spatial patterns and historical climate trends.")
    ]
    for icon, title, description in features:
        st.markdown(f"""
        <div class="info-panel" style="margin-bottom:10px;">
            <b style="color:#22d3c5;">{icon} &nbsp; {title}</b>
            <p style="color:#8ca3bb; margin-bottom:0;">
                {description}
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    section_header("Planned Data Sources")
    st.markdown("""
    - **NASA GIBS** — Global satellite imagery and visualization layers.
    - **NASA Earthdata** — Earth observation and climate datasets.
    - **NOAA** — Atmospheric, oceanic, and environmental datasets.
    - **NetCDF** — Multidimensional scientific data storage and processing.
    """)
    st.info("External data integrations are planned for future versions.")
