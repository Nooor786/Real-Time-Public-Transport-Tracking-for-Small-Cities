import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Real-Time Public Transport Tracker", layout="wide")
st.title("🚌 Real-Time Public Transport Tracker")

# -------------------------
# Initialize session state
# -------------------------
if 'bus_progress' not in st.session_state:
    st.session_state.bus_progress = []
if 'running' not in st.session_state:
    st.session_state.running = True
if 'speed' not in st.session_state:
    st.session_state.speed = 0.1  # fractional steps for smooth movement
if 'routes' not in st.session_state:
    st.session_state.routes = {
        "Route 1: Kodumur → St. John's College": ([15.8200, 78.0300], [15.8291, 78.0506])
    }
if 'current_route' not in st.session_state:
    st.session_state.current_route = None

# -------------------------
# Sidebar controls
# -------------------------
st.sidebar.title("Settings")
st.session_state.speed = st.sidebar.slider("Bus Speed (step size)", 0.05, 0.5, st.session_state.speed, 0.05)
if st.sidebar.button("Start/Stop Tracking"):
    st.session_state.running = not st.session_state.running

# -------------------------
# Route selection / addition
# -------------------------
selected_route = st.selectbox("Select Route:", ["--Select--"] + list(st.session_state.routes.keys()))

with st.form("add_route_form"):
    route_name = st.text_input("Add New Route Name")
    src_coords = st.text_input("Source Coordinates (lat,lon)", "15.8200,78.0300")
    dest_coords = st.text_input("Destination Coordinates (lat,lon)", "15.8291,78.0506")
    add_submitted = st.form_submit_button("Add Route")

if add_submitted and route_name:
    try:
        src = [float(x.strip()) for x in src_coords.split(",")]
        dest = [float(x.strip()) for x in dest_coords.split(",")]
        st.session_state.routes[route_name] = (src, dest)
        st.success(f"Route '{route_name}' added!")
    except:
        st.error("Invalid coordinates format. Use lat,lon")

# -------------------------
# Initialize route points
# -------------------------
if selected_route != "--Select--":
    st.session_state.current_route = selected_route
    src, dest = st.session_state.routes[selected_route]
    st.session_state.source_coords = src
    st.session_state.dest_coords = dest

if st.session_state.current_route and 'route_points' not in st.session_state:
    num_points = 20
    st.session_state.route_points = [
        [
            st.session_state.source_coords[0] + i*(st.session_state.dest_coords[0]-st.session_state.source_coords[0])/num_points,
            st.session_state.source_coords[1] + i*(st.session_state.dest_coords[1]-st.session_state.source_coords[1])/num_points
        ] for i in range(num_points+1)
    ]
    st.session_state.bus_progress = [0, 5, 10]  # fractional indices for buses

# -------------------------
# Map & tracking
# -------------------------
if st.session_state.current_route:
    st_autorefresh(interval=1000, key="bus_tracker")

    if st.session_state.running:
        for i in range(len(st.session_state.bus_progress)):
            st.session_state.bus_progress[i] += st.session_state.speed
            if st.session_state.bus_progress[i] > len(st.session_state.route_points)-1:
                st.session_state.bus_progress[i] = 0

    # interpolate positions
    bus_coords = []
    for p in st.session_state.bus_progress:
        idx = int(p)
        frac = p - idx
        if idx+1 < len(st.session_state.route_points):
            lat = st.session_state.route_points[idx][0] + frac * (st.session_state.route_points[idx+1][0] - st.session_state.route_points[idx][0])
            lon = st.session_state.route_points[idx][1] + frac * (st.session_state.route_points[idx+1][1] - st.session_state.route_points[idx][1])
            bus_coords.append([lat, lon])
        else:
            bus_coords.append(st.session_state.route_points[-1])

    center_coords = [
        (st.session_state.source_coords[0] + st.session_state.dest_coords[0])/2,
        (st.session_state.source_coords[1] + st.session_state.dest_coords[1])/2
    ]
    m = folium.Map(location=center_coords, zoom_start=14)
    folium.Marker(st.session_state.source_coords, popup="Source",
                  icon=folium.Icon(color="green", icon="home", prefix="fa")).add_to(m)
    folium.Marker(st.session_state.dest_coords, popup="Destination",
                  icon=folium.Icon(color="blue", icon="flag", prefix="fa")).add_to(m)
    folium.PolyLine(st.session_state.route_points, color="orange", weight=5).add_to(m)

    for idx, bus in enumerate(bus_coords):
        folium.Marker(bus, popup=f"Bus {idx+1}", icon=folium.Icon(color="red", icon="bus", prefix="fa")).add_to(m)

    st_folium(m, width=900, height=600)
    st.subheader("Bus Locations")
    for idx, bus in enumerate(bus_coords):
        st.write(f"Bus {idx+1}: {bus[0]:.5f}, {bus[1]:.5f}")

    status = "Running" if st.session_state.running else "Stopped"
    st.info(f"Status: {status} | Speed: {st.session_state.speed}")
    if st.button("Stop Tracking"):
        st.session_state.running = False
