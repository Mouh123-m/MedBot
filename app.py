import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.medical_robot import MedicalRobot
from src.mission import VALID_PRIORITIES
from src.mission_manager import MissionManager
from src.simulation import Simulation

STEP_DELAY_SECONDS = 0.25

st.set_page_config(page_title="MedBot", page_icon="🏥", layout="wide")


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

    figure = go.Figure()
    figure.add_trace(
        go.Heatmap(
            z=grid,
            colorscale=[[0, "#EAF4F4"], [1, "#6B7280"]],
            showscale=False,
            xgap=2,
            ygap=2,
            hoverinfo="skip",
        )
    )

    names = list(simulation.locations.keys())
    figure.add_trace(
        go.Scatter(
            x=[simulation.locations[n][0] for n in names],
            y=[simulation.locations[n][1] for n in names],
            mode="markers+text",
            text=names,
            textposition="top center",
            marker=dict(size=22, color="#0E7C86", symbol="square"),
            name="Departments",
        )
    )

    if robot.path:
        path_cells = [robot.position] + list(robot.path)
        figure.add_trace(
            go.Scatter(
                x=[c[0] for c in path_cells],
                y=[c[1] for c in path_cells],
                mode="lines",
                line=dict(color="#F59E0B", width=3, dash="dot"),
                name="Planned path",
            )
        )

    figure.add_trace(
        go.Scatter(
            x=[robot.position[0]],
            y=[robot.position[1]],
            mode="markers",
            marker=dict(size=26, color="#DC2626", symbol="circle"),
            name="Robot",
        )
    )

    figure.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[-0.5, simulation.width - 0.5], showgrid=False, zeroline=False, dtick=1),
        yaxis=dict(
            range=[simulation.height - 0.5, -0.5],
            showgrid=False,
            zeroline=False,
            dtick=1,
            scaleanchor="x",
        ),
        legend=dict(orientation="h", y=-0.05),
    )
    return figure


def render_simulation_page(manager, robot, simulation):
    map_col, control_col = st.columns([3, 1])

    with control_col:
        st.subheader("Controls")
        pending = [m for m in manager.missions if m.status == "pending"]
        if pending and manager.current_mission is None:
            options = {f"#{m.mission_id} {m.start} -> {m.destination} ({m.priority})": m.mission_id for m in pending}
            choice = st.selectbox("Pending mission", list(options.keys()))
            if st.button("Start", use_container_width=True):
                try:
                    manager.start_mission(options[choice])
                    st.session_state.running = manager.current_mission is not None
                    st.session_state.message = None
                except ValueError as error:
                    st.session_state.message = str(error)
                st.rerun()
        elif manager.current_mission is None:
            st.info("No pending mission. Create one in Mission Management.")

        if st.button("Pause", use_container_width=True):
            robot.pause()
            st.session_state.running = False
            st.rerun()
        if st.button("Resume", use_container_width=True):
            robot.resume()
            st.session_state.running = manager.current_mission is not None
            st.rerun()
        if st.button("Stop", use_container_width=True):
            manager.stop_current()
            st.session_state.running = False
            st.rerun()

        st.divider()
        st.subheader("Obstacles")
        obstacle_x = st.number_input("x", min_value=0, max_value=simulation.width - 1, value=4, step=1)
        obstacle_y = st.number_input("y", min_value=0, max_value=simulation.height - 1, value=4, step=1)
        if st.button("Add obstacle", use_container_width=True):
            try:
                simulation.add_obstacle((int(obstacle_x), int(obstacle_y)))
                st.session_state.message = None
            except ValueError as error:
                st.session_state.message = str(error)
            st.rerun()
        if st.button("Clear obstacles", use_container_width=True):
            for cell in list(simulation.obstacles):
                simulation.remove_obstacle(cell)
            st.rerun()

    with map_col:
        st.plotly_chart(build_map_figure(simulation, robot), use_container_width=True)

    with control_col:
        st.divider()
        st.write(f"**Status:** {robot.status}")
        st.write(f"**Position:** {robot.position}")
        if robot.alert:
            st.warning(robot.alert)
        if st.session_state.message:
            st.error(st.session_state.message)
        if manager.current_mission is not None:
            mission = manager.current_mission
            st.write(f"**Mission:** #{mission.mission_id} {mission.start} -> {mission.destination}")


def render_mission_page(manager, simulation):
    form_col, table_col = st.columns([1, 2])

    with form_col:
        st.subheader("Create New Mission")
        locations = list(simulation.locations.keys())
        with st.form("create_mission_form", clear_on_submit=False):
            start = st.selectbox("Starting Location", locations, index=0)
            destination = st.selectbox("Destination", locations, index=1)
            priority = st.selectbox("Priority", list(VALID_PRIORITIES), index=1)
            submitted = st.form_submit_button("Create Mission", use_container_width=True)

        if submitted:
            try:
                mission = manager.create_mission(start, destination, priority)
                st.success(f"Mission #{mission.mission_id} created: {start} -> {destination}")
            except ValueError as error:
                st.error(str(error))

    with table_col:
        st.subheader("Current Missions")
        records = manager.get_history()
        if not records:
            st.info("No missions yet. Create the first one.")
        else:
            table = pd.DataFrame(records)[
                ["mission_id", "start", "destination", "priority", "status"]
            ]
            st.dataframe(table, use_container_width=True, hide_index=True)

        pending = [m for m in manager.missions if m.status == "pending"]
        if pending:
            st.caption("To run a pending mission, open the Robot Simulation page and press Start.")
            
def render_history_page(manager):
    records = manager.get_history()
    if not records:
        st.info("No missions yet.")
        return

    table = pd.DataFrame(records)
    table = table.rename(
        columns={
            "mission_id": "ID",
            "created_at": "Date",
            "start": "From",
            "destination": "To",
            "priority": "Priority",
            "status": "Result",
            "failure_reason": "Failure reason",
        }
    )

    statuses = sorted(table["Result"].unique())
    selected = st.multiselect("Filter by result", statuses, default=statuses)
    filtered = table[table["Result"].isin(selected)]

    st.dataframe(
        filtered[["ID", "Date", "From", "To", "Priority", "Result", "Failure reason"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Missions by result")
    counts = table["Result"].value_counts()
    st.bar_chart(counts)
def nearest_location_name(simulation, position):
    def distance(item):
          cell = item[1]
          return abs(cell[0] - position[0]) + abs(cell[1] - position[1])

    name, _ = min(simulation.locations.items(), key=distance)
    return name


def render_monitoring_page(manager, robot, simulation):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Availability", "Available" if robot.is_available() else "Busy")
    col2.metric("Status", robot.status)
    col3.metric("Position", f"{robot.position}")
    col4.metric("Nearest department", nearest_location_name(simulation, robot.position))

    st.subheader("Current mission")
    mission = manager.current_mission
    if mission is None:
        st.info("The robot has no active mission.")
    else:
        st.write(f"**#{mission.mission_id}** {mission.start} -> {mission.destination} ({mission.priority})")
        st.write(f"Steps remaining: {len(robot.path)}")

    st.subheader("Obstacle alerts")
    if robot.alert:
        st.warning(robot.alert)
    else:
        st.success("No obstacle alert.")

    st.subheader("Obstacles on the map")
    if simulation.obstacles:
        table = pd.DataFrame(
            sorted(simulation.obstacles), columns=["x", "y"]
        )
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        st.caption("The map has no obstacles.")
CARD_CSS = """
<style>
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #CFE3E5;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(14, 124, 134, 0.10);
}
</style>
"""


def render_dashboard_page(manager, robot, simulation):
    stats = manager.get_statistics()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Missions", stats["total"])
    col2.metric("Completed", stats["completed"])
    col3.metric("Pending", stats["pending"])
    col4.metric("Failed", stats["failed"])
    col5.metric("Robot Status", robot.status)

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Robot position")
        st.caption(f"Current position: {robot.position}")
        st.plotly_chart(build_map_figure(simulation, robot), use_container_width=True)

    with right:
        st.subheader("Missions by result")
        if stats["total"] == 0:
            st.info("No missions yet.")
        else:
            labels = ["Completed", "Failed", "Pending"]
            values = [stats["completed"], stats["failed"], stats["pending"]]
            pie = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(colors=["#16A34A", "#DC2626", "#F59E0B"]),
                )
            )
            pie.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(pie, use_container_width=True)

        st.subheader("Latest missions")
        records = manager.get_history()
        if records:
            latest = pd.DataFrame(records[-5:][::-1])[["mission_id", "destination", "status"]]
            st.dataframe(latest, use_container_width=True, hide_index=True)


init_state()

manager = st.session_state.manager
robot = st.session_state.robot
simulation = st.session_state.simulation

st.sidebar.title("🏥 MedBot")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Robot Simulation", "Mission Management", "Mission History", "Robot Monitoring"],
)

st.title(page)
st.markdown(CARD_CSS, unsafe_allow_html=True)
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