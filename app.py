import streamlit as st

from src.medical_robot import MedicalRobot
from src.mission_manager import MissionManager
from src.simulation import Simulation

st.set_page_config(page_title="MedBot", page_icon="🏥", layout="wide")


def init_state():
    if "manager" not in st.session_state:
        simulation = Simulation()
        robot = MedicalRobot(simulation)
        st.session_state.simulation = simulation
        st.session_state.robot = robot
        st.session_state.manager = MissionManager(robot)


init_state()

manager = st.session_state.manager
robot = st.session_state.robot

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
else:
    st.info("This page will be built in the next steps.")