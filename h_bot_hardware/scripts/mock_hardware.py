#!/usr/bin/env python3
"""
🦾 H-Bot Mock Hardware — Act I: Feel the joints

A standalone script (no ROS required) that simulates H-Bot's 13 actuators.
It prints joint states to the terminal so you can verify joint names, ranges,
and the basic actuator response model before wiring real servos.

Usage:
    python3 scripts/mock_hardware.py [--rate 10] [--duration 0]

Arguments:
    --rate     Terminal print rate in Hz (default: 10).
    --duration Seconds to run; 0 means run forever (default: 0).
"""

from __future__ import print_function

import argparse
import math
import sys
import time

# -----------------------------------------------------------------------------
# Common joint names for H-Bot
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


# -----------------------------------------------------------------------------
# Simple actuator simulator
# -----------------------------------------------------------------------------
class MockHardware(object):
    """Lightweight model of position-controlled servos with lag and limits."""

    def __init__(self, joint_names, update_rate_hz=50.0):
        self.joint_names = list(joint_names)
        self.rate_hz = float(update_rate_hz)
        self.dt = 1.0 / self.rate_hz
        self.positions = [0.0] * len(self.joint_names)
        self.velocities = [0.0] * len(self.joint_names)
        self.efforts = [0.0] * len(self.joint_names)
        self.commands = [0.0] * len(self.joint_names)
        self.start_time = time.time()

    def generate_test_pattern(self, t):
        """Create smooth periodic commands that exercise every joint."""
        commands = []
        for i, name in enumerate(self.joint_names):
            # Phase-shifted sines keep the output visually interesting
            freq = 0.5 + 0.1 * i
            amp = math.radians(15.0)
            if "knee" in name or "elbow" in name:
                amp = math.radians(20.0)
            commands.append(amp * math.sin(2.0 * math.pi * freq * t))
        return commands

    def step(self, t):
        """Advance physics one tick and return current joint state."""
        self.commands = self.generate_test_pattern(t)

        for i in range(len(self.joint_names)):
            error = self.commands[i] - self.positions[i]
            # Servo-like first-order lag
            self.velocities[i] = error * 8.0
            self.positions[i] += self.velocities[i] * self.dt

            # Fake effort from gravity/load
            if "hip" in self.joint_names[i] or "knee" in self.joint_names[i]:
                self.efforts[i] = -math.sin(self.positions[i]) * 0.6
            else:
                self.efforts[i] = 0.05 * math.cos(2.0 * math.pi * t)

        return {
            "time": t,
            "names": self.joint_names,
            "positions": list(self.positions),
            "velocities": list(self.velocities),
            "efforts": list(self.efforts),
        }


# -----------------------------------------------------------------------------
# Pretty printing helpers
# -----------------------------------------------------------------------------
def print_header():
    print("=" * 78, flush=True)
    print("🦾 H-Bot Mock Hardware", flush=True)
    print("Simulating {} joints without ROS. Press Ctrl+C to stop.".format(len(JOINT_NAMES)), flush=True)
    print("=" * 78, flush=True)


def print_state(state):
    line = "[{:.2f}s] ".format(state["time"])
    parts = []
    for name, pos, vel, eff in zip(
        state["names"], state["positions"], state["velocities"], state["efforts"]
    ):
        parts.append("{}: {:.3f} / {:.3f} / {:.3f}".format(name, pos, vel, eff))
    # Print in two chunks so lines fit on a normal terminal
    mid = len(parts) // 2
    print(line + " | ".join(parts[:mid]), flush=True)
    print(" " * len(line) + " | ".join(parts[mid:]), flush=True)


# -----------------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Standalone mock actuator loop for H-Bot."
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=10.0,
        help="Terminal print rate in Hz (default: 10).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Seconds to run; 0 means forever (default: 0).",
    )
    args = parser.parse_args()

    if args.rate <= 0:
        print("Error: --rate must be positive.", file=sys.stderr)
        sys.exit(1)

    hw = MockHardware(JOINT_NAMES, update_rate_hz=50.0)
    print_header()

    period = 1.0 / args.rate
    try:
        while True:
            t = time.time() - hw.start_time
            state = hw.step(t)
            print_state(state)

            if args.duration > 0 and t >= args.duration:
                print("\n✅ Reached requested duration. Mock hardware stopped.", flush=True)
                break

            time.sleep(period)
    except KeyboardInterrupt:
        print("\n👋 Mock hardware stopped by user.", flush=True)


if __name__ == "__main__":
    main()
