import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.medical_robot import MedicalRobot
from src.mission import VALID_PRIORITIES
from src.mission_manager import MissionManager
from src.simulation import Simulation

STEP_DELAY_SECONDS = 0.25

# Page Configuration
st.set_page_config(
    page_title="MedBot — Advanced Autonomous Medical Navigation",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ultra-Modern Custom Styling (Glassmorphism & Industrial Dashboard UI)
MODERN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global Typography & Font Setup */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #F8FAFC;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0B0F19;
        border-right: 1px solid #1E293B;
    }

    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label {
        color: #F1F5F9 !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        color: #94A3B8 !important;
        font-weight: 500;
    }

    /* Modern Metric Cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0EA5E9;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.07);
        border-color: #CBD5E1;
        border-left-color: #0284C7;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-size: 1.75rem;
        font-weight: 700;
    }

    /* Primary Action Buttons */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }

    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
    }

    /* Dataframe Container Aesthetics */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        background-color: #FFFFFF;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    }
</style>
"""

st.markdown(MODERN_CSS, unsafe_allow_html=True)


def init_state():
    if "manager" not in st.session_state:
        simulation = Simulation()
        robot = MedicalRobot(simulation)
        st.session_state.simulation = simulation
        st.session_state.robot = robot
        st.session_state.manager = MissionManager(robot)
        st.session_state.running = False
        st.session_state.message = None


def build_map_figure(simulation, robot):
    grid = [[0 for _ in range(simulation.width)] for _ in range(simulation.height)]
    for (x, y) in simulation.obstacles:
        grid[y][x] = 1

    fig = go.Figure()

    # Heatmap Grid Background
    fig.add_trace(
        go.Heatmap(
            z=grid,
            colorscale=[[0, "rgba(248, 250, 252, 0.4)"], [1, "#1E293B"]],
            showscale=False,
            xgap=4,
            ygap=4,
            hoverinfo="skip",
        )
    )

    # Department / Locations Markers
    names = list(simulation.locations.keys())
    fig.add_trace(
        go.Scatter(
            x=[simulation.locations[n][0] for n in names],
            y=[simulation.locations[n][1] for n in names],
            mode="markers+text",
            text=names,
            textposition="top center",
            textfont=dict(size=12, color="#1E293B", family="Plus Jakarta Sans", weight=600),
            marker=dict(
                size=22,
                color="#38BDF8",
                symbol="square",
                line=dict(width=2, color="#0284C7"),
            ),
            name="Departments",
        )
    )

    # Planned Path Line Trace
    if robot.path:
        path_cells = [robot.position] + list(robot.path)
        fig.add_trace(
            go.Scatter(
                x=[c[0] for c in path_cells],
                y=[c[1] for c in path_cells],
                mode="lines+markers",
                line=dict(color="#6366F1", width=4, dash="solid"),
                marker=dict(size=8, color="#4F46E5"),
                name="Planned Path",
            )
        )

    # Robot Marker Location
    fig.add_trace(
        go.Scatter(
            x=[robot.position[0]],
            y=[robot.position[1]],
            mode="markers",
            marker=dict(
                size=30,
                color="#F43F5E",
                symbol="circle",
                line=dict(width=3, color="#FFFFFF"),
            ),
            name="MedBot Agent",
        )
    )

    # Clean Modern Layout Aesthetics
    fig.update_layout(
        height=580,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            range=[-0.5, simulation.width - 0.5],
            showgrid=False,
            zeroline=False,
            dtick=1,
            color="#94A3B8",
        ),
        yaxis=dict(
            range=[simulation.height - 0.5, -0.5],
            showgrid=False,
            zeroline=False,
            dtick=1,
            scaleanchor="x",
            color="#94A3B8",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#475569", size=11),
        ),
    )
    return fig


def render_simulation_page(manager, robot, simulation):
    map_col, control_col = st.columns([3, 1], gap="large")

    with control_col:
        st.markdown("### 🎮 Control Center")
        pending = [m for m in manager.missions if m.status == "pending"]

        if pending and manager.current_mission is None:
            options = {
                f"#{m.mission_id} {m.start} ➔ {m.destination} ({m.priority})": m.mission_id
                for m in pending
            }
            choice = st.selectbox(
                "Select Pending Mission",
                list(options.keys()),
                disabled=st.session_state.get("running", False),
                filter_mode=None,
            )
            if st.button("🚀 Start Mission", use_container_width=True, type="primary"):
                try:
                    manager.start_mission(options[choice])
                    st.session_state.running = manager.current_mission is not None
                    st.session_state.message = None
                except ValueError as error:
                    st.session_state.message = str(error)
                st.rerun()
        elif manager.current_mission is None:
            st.info("No active or pending missions.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⏸️ Pause", use_container_width=True):
                robot.pause()
                st.session_state.running = False
                st.rerun()
        with c2:
            if st.button("▶️ Resume", use_container_width=True):
                robot.resume()
                st.session_state.running = manager.current_mission is not None
                st.rerun()

        if st.button("⏹️ Stop Mission", use_container_width=True):
            manager.stop_current()
            st.session_state.running = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 🚧 Obstacle Manager")
        x_options = list(range(simulation.width))
        y_options = list(range(simulation.height))
        
        c3, c4 = st.columns(2)
        with c3:
            obstacle_x = st.selectbox("Grid X", x_options, index=min(4, simulation.width - 1), filter_mode=None)
        with c4:
            obstacle_y = st.selectbox("Grid Y", y_options, index=min(4, simulation.height - 1), filter_mode=None)

        if st.button("➕ Add Obstacle", use_container_width=True):
            try:
                simulation.add_obstacle((int(obstacle_x), int(obstacle_y)))
                st.session_state.message = None
            except ValueError as error:
                st.session_state.message = str(error)
            st.rerun()

        if st.button("🧹 Clear Obstacles", use_container_width=True):
            for cell in list(simulation.obstacles):
                simulation.remove_obstacle(cell)
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Status Overview")
        st.markdown(f"**Status:** `{robot.status}`")
        st.markdown(f"**Position:** `{robot.position}`")

        if robot.alert:
            st.warning(f"⚠️ {robot.alert}")
        if st.session_state.message:
            st.error(f"❌ {st.session_state.message}")
            
        if manager.current_mission is not None:
            m = manager.current_mission
            st.success(f"**Active Mission #{m.mission_id}:** {m.start} ➔ {m.destination}")

    with map_col:
        st.markdown("### 🗺️ Live Navigation Grid")
        st.plotly_chart(build_map_figure(simulation, robot), use_container_width=True)


def render_mission_page(manager, simulation):
    form_col, table_col = st.columns([1, 2], gap="large")

    with form_col:
        st.markdown("### ➕ Dispatch New Mission")
        locations = list(simulation.locations.keys())
        
        start = st.selectbox("Origin Location", locations, index=0, filter_mode=None)
        destination = st.selectbox("Destination Location", locations, index=1 if len(locations) > 1 else 0, filter_mode=None)
        priority = st.selectbox("Priority Level", list(VALID_PRIORITIES), index=1 if len(VALID_PRIORITIES) > 1 else 0, filter_mode=None)
        
        submitted = st.button("Dispatch Mission", use_container_width=True, type="primary")

        if submitted:
            try:
                mission = manager.create_mission(start, destination, priority)
                st.success(f"Mission #{mission.mission_id} dispatched: {start} ➔ {destination}")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        st.markdown("---")
        st.markdown("### 🗑️ Delete Mission")
        
        all_missions = manager.missions
        if not all_missions:
            st.caption("No missions available to delete.")
        else:
            delete_options = {f"#{m.mission_id}: {m.start} ➔ {m.destination} ({m.status})": m.mission_id for m in all_missions}
            selected_to_delete = st.selectbox("Select Mission to Delete", list(delete_options.keys()), filter_mode=None)
            
            if st.button("Delete Selected Mission", use_container_width=True, type="secondary"):
                target_id = delete_options[selected_to_delete]
                try:
                    if hasattr(manager, "delete_mission"):
                        manager.delete_mission(target_id)
                    elif hasattr(manager, "remove_mission"):
                        manager.remove_mission(target_id)
                    else:
                        manager.missions = [m for m in manager.missions if m.mission_id != target_id]
                    
                    st.success(f"Mission #{target_id} has been deleted successfully.")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not delete mission: {error}")

    with table_col:
        st.markdown("### 📋 Mission Queue")
        records = manager.get_history()
        if not records:
            st.info("No missions in queue. Create one using the form on the left.")
        else:
            table = pd.DataFrame(records)[["mission_id", "start", "destination", "priority", "status"]]
            st.dataframe(table, use_container_width=True, hide_index=True)

        pending = [m for m in manager.missions if m.status == "pending"]
        if pending:
            st.caption("📌 *Head over to the 'Robot Simulation' tab to start execution on pending missions.*")


def render_history_page(manager):
    records = manager.get_history()
    if not records:
        st.info("No mission history available yet.")
        return

    table = pd.DataFrame(records).rename(
        columns={
            "mission_id": "ID",
            "created_at": "Timestamp",
            "start": "Origin",
            "destination": "Destination",
            "priority": "Priority",
            "status": "Result",
            "failure_reason": "Failure Reason",
        }
    )

    statuses = sorted(table["Result"].unique())
    selected = st.multiselect("Filter by status", statuses, default=statuses)
    filtered = table[table["Result"].isin(selected)]

    st.markdown("### 📜 Mission Logs")
    st.dataframe(
        filtered[["ID", "Timestamp", "Origin", "Destination", "Priority", "Result", "Failure Reason"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### 📊 Analytics: Missions by Outcome")
    counts = table["Result"].value_counts()
    st.bar_chart(counts)


def nearest_location_name(simulation, position):
    def distance(item):
        cell = item[1]
        return abs(cell[0] - position[0]) + abs(cell[1] - position[1])

    name, _ = min(simulation.locations.items(), key=distance)
    return name


def render_monitoring_page(manager, robot, simulation):
    st.markdown("### 🤖 Robot Diagnostics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Availability", "Available" if robot.is_available() else "Busy")
    c2.metric("Robot Status", robot.status)
    c3.metric("Coordinates", f"{robot.position}")
    c4.metric("Nearest Zone", nearest_location_name(simulation, robot.position))

    st.markdown("---")
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### 🎯 Current Mission")
        mission = manager.current_mission
        if mission is None:
            st.info("No active mission running.")
        else:
            st.markdown(f"**ID:** `#{mission.mission_id}`")
            st.markdown(f"**Route:** {mission.start} ➔ {mission.destination}")
            st.markdown(f"**Priority:** `{mission.priority}`")
            st.markdown(f"**Remaining Waypoints:** `{len(robot.path)}`")

    with right:
        st.markdown("### ⚠️ Hazard & Alert Monitoring")
        if robot.alert:
            st.warning(robot.alert)
        else:
            st.success("All systems nominal. No active obstacle alerts.")

        st.markdown("#### Detected Map Obstacles")
        if simulation.obstacles:
            table = pd.DataFrame(sorted(simulation.obstacles), columns=["Grid X", "Grid Y"])
            st.dataframe(table, use_container_width=True, hide_index=True)
        else:
            st.caption("No obstacles currently registered on the map.")


def render_dashboard_page(manager, robot, simulation):
    stats = manager.get_statistics()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Missions", stats["total"])
    c2.metric("Completed", stats["completed"])
    c3.metric("Pending", stats["pending"])
    c4.metric("Failed", stats["failed"])
    c5.metric("System Status", robot.status)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([2, 1], gap="large")

    with left:
        st.markdown("### 🛰️ Real-Time Location Map")
        st.caption(f"Current Position Coordinates: {robot.position}")
        st.plotly_chart(build_map_figure(simulation, robot), use_container_width=True)

    with right:
        st.markdown("### 📈 Performance Summary")
        if stats["total"] == 0:
            st.info("No mission data collected yet.")
        else:
            labels = ["Completed", "Failed", "Pending"]
            values = [stats["completed"], stats["failed"], stats["pending"]]
            pie = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.6,
                    marker=dict(colors=["#10B981", "#EF4444", "#F59E0B"]),
                )
            )
            pie.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(pie, use_container_width=True)

        st.markdown("### ⏱️ Recent Activity")
        records = manager.get_history()
        if records:
            latest = pd.DataFrame(records[-5:][::-1])[["mission_id", "destination", "status"]]
            st.dataframe(latest, use_container_width=True, hide_index=True)


# Initialize session state
init_state()

manager = st.session_state.manager
robot = st.session_state.robot
simulation = st.session_state.simulation

# Sidebar Navigation
st.sidebar.markdown("# 🏥 MedBot Control")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Robot Simulation", "Mission Management", "Mission History", "Robot Monitoring"],
)

# Render View Pages
if page == "Dashboard":
    render_dashboard_page(manager, robot, simulation)
elif page == "Robot Simulation":
    render_simulation_page(manager, robot, simulation)
    if st.session_state.running and manager.current_mission is not None and robot.status == "moving":
        manager.step()
        time.sleep(STEP_DELAY_SECONDS)
        if manager.current_mission is None:
            st.session_state.running = False
        st.rerun()
elif page == "Mission Management":
    render_mission_page(manager, simulation)
elif page == "Mission History":
    render_history_page(manager)
elif page == "Robot Monitoring":
    render_monitoring_page(manager, robot, simulation)
