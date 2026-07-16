#!/usr/bin/env python3
"""
🦾 H-Bot Hardware Bridge — Act I: Feel the joints

This node is the first concrete hardware-software bridge for H-Bot.
It does two things:
  1. Publishes sensor_msgs/JointState on /joint_states (real or mocked).
  2. Subscribes to sensor_msgs/JointState on /joint_commands and echoes them
     as actuator set-points.

If ROS (rospy) is not installed, the script falls back to a mock loop so you
can still see H-Bot "move" and verify the joint names.

Run directly without ROS:
    python3 scripts/hardware_bridge.py

Run as a ROS node:
    rosrun h_bot_hardware hardware_bridge.py
    # or
    roslaunch h_bot_hardware hardware_bringup.launch
"""

from __future__ import print_function

import math
import sys
import time

# -----------------------------------------------------------------------------
# Common joint names for H-Bot
# Keep this list in sync with URDF, controllers, and simulation!
# -----------------------------------------------------------------------------
JOINT_NAMES = [
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

PUBLISH_RATE_HZ = 50.0  # Typical ROS control loop rate


# -----------------------------------------------------------------------------
# Mock actuator backend
# Used both in the ROS-free fallback and as a placeholder when ROS is present
# but no real servos are wired up yet.
# -----------------------------------------------------------------------------
class MockActuatorBackend(object):
    """Simulates 13 hobby servos responding slowly to commanded positions."""

    def __init__(self, joint_names):
        self.joint_names = list(joint_names)
        # Start in a neutral standing pose
        self.positions = [0.0] * len(self.joint_names)
        self.velocities = [0.0] * len(self.joint_names)
        self.efforts = [0.0] * len(self.joint_names)
        self.commands = [0.0] * len(self.joint_names)
        self._start_time = time.time()

    def set_command(self, name, value):
        """Store a position command for a single joint."""
        if name in self.joint_names:
            idx = self.joint_names.index(name)
            self.commands[idx] = float(value)

    def set_commands(self, name_value_map):
        """Bulk update commands from a dictionary {joint_name: position}."""
        for name, value in name_value_map.items():
            self.set_command(name, value)

    def read(self):
        """
        Simulate actuator physics: current position drifts toward command.
        Returns (names, positions, velocities, efforts).
        """
        now = time.time()
        dt = 0.02  # Assume 50 Hz for the mock
        for i, name in enumerate(self.joint_names):
            error = self.commands[i] - self.positions[i]
            # Simple first-order lag: time constant ~0.1 s
            self.velocities[i] = error * 10.0
            self.positions[i] += self.velocities[i] * dt
            # Tiny fake effort from "gravity" on leg joints
            if "hip" in name or "knee" in name or "ankle" in name:
                self.efforts[i] = -math.sin(self.positions[i]) * 0.5
            else:
                self.efforts[i] = 0.0

            # Add a little idle wiggle so beginners see *something* happening
            if abs(self.commands[i]) < 0.01:
                self.positions[i] += math.sin(now * 2.0 + i) * 0.0005

        return self.joint_names, self.positions, self.velocities, self.efforts


# -----------------------------------------------------------------------------
# ROS-aware path
# -----------------------------------------------------------------------------
def run_ros_node():
    """Run as a real ROS node using rospy and sensor_msgs."""
    import rospy
    from sensor_msgs.msg import JointState

    rospy.init_node("h_bot_hardware_bridge", anonymous=True)

    backend = MockActuatorBackend(JOINT_NAMES)

    state_pub = rospy.Publisher("/joint_states", JointState, queue_size=10)

    def command_callback(msg):
        """Handle incoming /joint_commands."""
        # Guard against mismatched names
        if len(msg.name) != len(msg.position):
            rospy.logwarn_throttle(
                5.0,
                "/joint_commands name/position length mismatch ({} vs {})".format(
                    len(msg.name), len(msg.position)
                ),
            )
            return

        cmd_map = {}
        for name, pos in zip(msg.name, msg.position):
            if name in JOINT_NAMES:
                cmd_map[name] = pos
            else:
                rospy.logwarn_throttle(
                    5.0, "Unknown joint in /joint_commands: {}".format(name)
                )
        backend.set_commands(cmd_map)

    rospy.Subscriber("/joint_commands", JointState, command_callback)

    rate = rospy.Rate(PUBLISH_RATE_HZ)
    rospy.loginfo(
        "H-Bot hardware bridge online. Publishing /joint_states at %.1f Hz", PUBLISH_RATE_HZ
    )

    while not rospy.is_shutdown():
        names, positions, velocities, efforts = backend.read()

        msg = JointState()
        msg.header.stamp = rospy.Time.now()
        msg.name = names
        msg.position = positions
        msg.velocity = velocities
        msg.effort = efforts

        state_pub.publish(msg)
        rate.sleep()


# -----------------------------------------------------------------------------
# ROS-free fallback path
# -----------------------------------------------------------------------------
def run_mock_loop():
    """Run a pure-Python mock loop when rospy is unavailable."""
    backend = MockActuatorBackend(JOINT_NAMES)

    # Create a simple wandering command so the output is interesting
    for i, name in enumerate(JOINT_NAMES):
        # Alternate limbs move in opposite directions
        backend.commands[i] = math.radians(10) * (1 if i % 2 == 0 else -1)

    print("=" * 70, flush=True)
    print("🦾 H-Bot Hardware Bridge — MOCK MODE", flush=True)
    print("ROS/rospy is not available, so this script runs in pure Python.", flush=True)
    print("Install ROS Noetic to use this as a real ROS node:", flush=True)
    print("    sudo apt install ros-noetic-desktop-full", flush=True)
    print("=" * 70, flush=True)
    print("Publishing {} joints at {:.1f} Hz. Press Ctrl+C to stop.\n".format(
        len(JOINT_NAMES), PUBLISH_RATE_HZ
    ), flush=True)

    period = 1.0 / PUBLISH_RATE_HZ
    try:
        while True:
            names, positions, velocities, efforts = backend.read()
            now = time.time() - backend._start_time

            # Compact terminal-friendly print
            line = "[{:.2f}s] ".format(now)
            parts = []
            for n, p, v in zip(names, positions, velocities):
                parts.append("{}: {:.3f} rad (v={:.3f})".format(n, p, v))
            print(line + " | ".join(parts[:4]) + " ...", flush=True)

            time.sleep(period)
    except KeyboardInterrupt:
        print("\n👋 Mock hardware bridge stopped.", flush=True)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def main():
    try:
        import rospy  # noqa: F401
        run_ros_node()
    except ImportError:
        run_mock_loop()


if __name__ == "__main__":
    main()
