#!/usr/bin/env python3
"""
web_bridge.py

A lightweight WebSocket bridge for H-Bot.

What it does:
  - Runs a WebSocket server on ws://localhost:8765.
  - Publishes live joint angles to every connected browser.
  - Receives high-level pose commands from the browser and forwards them
    to ROS on the /cmd_pose topic (when ROS is available).

Modes:
  - ROS mode:   subscribes to /joint_states and publishes /cmd_pose.
  - Mock mode:  runs without ROS, generating smooth sine-wave joint motion
                so the web UI can be tested on any machine.

Usage:
    python3 h_bot_hardware/scripts/web_bridge.py

Then open index.html in a browser.
"""

import asyncio
import json
import math
import time
from typing import Dict, List, Set

# ---------------------------------------------------------------------------
# WebSocket dependency (fallback path; ROS is optional)
# ---------------------------------------------------------------------------
try:
    import websockets
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "The 'websockets' package is required. Install it with:\n"
        "  pip install websockets\n"
    ) from e

# websockets 14+ renamed WebSocketServerProtocol to ServerConnection.
# This alias keeps the code compatible with older and newer releases.
if hasattr(websockets, "ServerConnection"):
    WebSocketConnection = websockets.ServerConnection
else:
    # pragma: no cover
    WebSocketConnection = websockets.WebSocketServerProtocol

# ---------------------------------------------------------------------------
# Optional ROS imports. If rospy is missing, the bridge falls back to mock data.
# ---------------------------------------------------------------------------
try:
    import rospy
    from sensor_msgs.msg import JointState
    from geometry_msgs.msg import PoseStamped
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    JointState = None  # type: ignore
    PoseStamped = None  # type: ignore


# ---------------------------------------------------------------------------
# H-Bot joint configuration
# ---------------------------------------------------------------------------
H_BOT_JOINTS: List[str] = [
    "head_pan",
    "left_shoulder_pitch",
    "left_elbow",
    "right_shoulder_pitch",
    "right_elbow",
    "left_hip_yaw",
    "left_hip_pitch",
    "left_knee",
    "left_ankle",
    "right_hip_yaw",
    "right_hip_pitch",
    "right_knee",
    "right_ankle",
]

# Update rate for the WebSocket broadcast loop (Hz).
PUBLISH_RATE_HZ = 30.0

# WebSocket server host and port.
WS_HOST = "localhost"
WS_PORT = 8765


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
connected_clients: Set[WebSocketConnection] = set()
latest_joint_states: Dict[str, float] = {name: 0.0 for name in H_BOT_JOINTS}
command_publisher = None


# ---------------------------------------------------------------------------
# ROS helpers
# ---------------------------------------------------------------------------
def ros_joint_state_callback(msg: "JointState") -> None:
    """Update the latest joint angles from a ROS /joint_states message."""
    global latest_joint_states
    if not msg.name or not msg.position:
        return

    for name, position in zip(msg.name, msg.position):
        if name in latest_joint_states:
            latest_joint_states[name] = float(position)


def init_ros_node() -> None:
    """Initialize the ROS node, subscriber and publisher when ROS is present."""
    global command_publisher
    rospy.init_node("h_bot_web_bridge", anonymous=True)
    rospy.Subscriber("/joint_states", JointState, ros_joint_state_callback)
    command_publisher = rospy.Publisher("/cmd_pose", PoseStamped, queue_size=10)
    rospy.loginfo("ROS mode active: listening on /joint_states, publishing /cmd_pose")


# ---------------------------------------------------------------------------
# Mock-mode helpers
# ---------------------------------------------------------------------------
def update_mock_joint_states(elapsed: float) -> None:
    """Generate smooth synthetic joint motion for browser-only testing."""
    global latest_joint_states
    for index, name in enumerate(H_BOT_JOINTS):
        # Each joint gets its own phase so the display looks lively.
        phase = elapsed * 0.5 + index * 0.4
        amplitude = 0.3 if "knee" in name or "elbow" in name else 0.15
        latest_joint_states[name] = amplitude * math.sin(phase)


# ---------------------------------------------------------------------------
# WebSocket helpers
# ---------------------------------------------------------------------------
def build_joint_state_message() -> str:
    """Create a JSON payload with the latest joint angles."""
    payload = {
        "type": "joint_states",
        "timestamp": time.time(),
        "joint_states": latest_joint_states.copy(),
    }
    return json.dumps(payload)


async def broadcast_joint_states() -> None:
    """Send the current joint state to every connected browser."""
    if not connected_clients:
        return

    message = build_joint_state_message()
    # websockets.broadcast is the cleanest way to fan-out one message.
    websockets.broadcast(connected_clients, message)


async def handle_incoming_command(websocket: WebSocketConnection) -> None:
    """Read JSON commands from a browser and forward them to ROS or stdout."""
    async for raw_message in websocket:
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON payload",
            }))
            continue

        msg_type = data.get("type")
        if msg_type == "cmd_pose":
            await process_cmd_pose(data, websocket)
        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            }))


async def process_cmd_pose(
    data: dict,
    websocket: WebSocketConnection,
) -> None:
    """Forward a pose command to /cmd_pose (ROS) or echo it (mock)."""
    pose = data.get("pose", {})
    x = float(pose.get("x", 0.0))
    y = float(pose.get("y", 0.0))
    z = float(pose.get("z", 0.0))
    roll = float(pose.get("roll", 0.0))
    pitch = float(pose.get("pitch", 0.0))
    yaw = float(pose.get("yaw", 0.0))

    if ROS_AVAILABLE and command_publisher is not None:
        # Build a PoseStamped message from the browser JSON.
        msg = PoseStamped()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = "base_link"
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = z
        msg.pose.orientation.x = roll
        msg.pose.orientation.y = pitch
        msg.pose.orientation.z = yaw
        msg.pose.orientation.w = 1.0
        command_publisher.publish(msg)
        rospy.loginfo(f"/cmd_pose <- x={x:.3f} y={y:.3f} z={z:.3f}")
    else:
        print(f"[MOCK /cmd_pose] x={x:.3f} y={y:.3f} z={z:.3f} "
              f"roll={roll:.3f} pitch={pitch:.3f} yaw={yaw:.3f}")

    await websocket.send(json.dumps({
        "type": "ack",
        "command": "cmd_pose",
        "pose": {"x": x, "y": y, "z": z, "roll": roll, "pitch": pitch, "yaw": yaw},
    }))


async def register_client(websocket: WebSocketConnection) -> None:
    """Track a newly connected browser."""
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address} "
          f"(total: {len(connected_clients)})")
    # Send the current state immediately so the UI is not empty.
    await websocket.send(build_joint_state_message())


async def unregister_client(websocket: WebSocketConnection) -> None:
    """Remove a disconnected browser from the fan-out list."""
    connected_clients.discard(websocket)
    print(f"Client disconnected: {websocket.remote_address} "
          f"(total: {len(connected_clients)})")


async def websocket_handler(websocket: WebSocketConnection, path: str = "") -> None:
    """Main handler for each client connection."""
    await register_client(websocket)
    try:
        # handle_incoming_command loops until the client disconnects.
        await handle_incoming_command(websocket)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister_client(websocket)


# ---------------------------------------------------------------------------
# Main loops
# ---------------------------------------------------------------------------
async def publish_loop() -> None:
    """Periodically broadcast joint states to all connected clients."""
    period = 1.0 / PUBLISH_RATE_HZ
    start_time = time.time()
    while True:
        if not ROS_AVAILABLE:
            update_mock_joint_states(time.time() - start_time)
        await broadcast_joint_states()
        await asyncio.sleep(period)


def start_ros_spin_thread() -> None:
    """Run the ROS subscriber loop in a background thread."""
    import threading

    def spin() -> None:
        rospy.spin()

    thread = threading.Thread(target=spin, daemon=True)
    thread.start()


async def main() -> None:
    """Start the WebSocket server and the joint-state broadcast loop."""
    if ROS_AVAILABLE:
        init_ros_node()
        start_ros_spin_thread()
        print("ROS node initialized.")
    else:
        print("ROS not detected. Running in MOCK mode with synthetic joint motion.")
        print("To use ROS, source your workspace and ensure rospy is on PYTHONPATH.")

    server = await websockets.serve(
        websocket_handler,
        WS_HOST,
        WS_PORT,
    )
    print(f"WebSocket server listening on ws://{WS_HOST}:{WS_PORT}")

    # Run the broadcaster alongside the server.
    await asyncio.gather(
        server.wait_closed(),
        publish_loop(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down H-Bot web bridge.")
