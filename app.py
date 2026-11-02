import time

import plotly.graph_objects as go
import streamlit as st

from src.medical_robot import MedicalRobot
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

if page == "Dashboard":
    stats = manager.get_statistics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Missions", stats["total"])
    col2.metric("Completed", stats["completed"])
    col3.metric("Pending", stats["pending"])
    col4.metric("Robot Status", robot.status)
    st.write(f"Current position: {robot.position}")
elif page == "Robot Simulation":
    render_simulation_page(manager, robot, simulation)
    if st.session_state.running and manager.current_mission is not None and robot.status == "moving":
        manager.step()
        time.sleep(STEP_DELAY_SECONDS)
        if manager.current_mission is None:
            st.session_state.running = False
        st.rerun()
else:
    st.info("This page will be built in the next steps.")