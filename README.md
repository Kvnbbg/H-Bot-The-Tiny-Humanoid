# 🦾 H-Bot: The Tiny Humanoid

Welcome to      ____  
     /____\ 
     |·  ·|   H-Bot Awakes...
_o_   \__/   _o_
/   \  /||\  /   \


**A modular, ROS-based humanoid robotics framework for realistic simulation, control, and optional reinforcement-learning integration.**
The epic sandbox of **H-Bot**—your pint-sized, ROS-powered humanoid companion. This isn’t just another robot repo; it’s an interactive playground where balance, walking, and a dash of RL magic collide. Strap in for a journey from zero-moment point to zero-gravity dreams.

---

## 📖 Story Arc

1. **Prologue** – Build the world (URDF & Gazebo).  
2. **Act I** – Master the ROS control stack (joints, sensors, safety).  
3. **Act II** – Unleash walking & balancing (ZMP wizardry!).  
4. **Act III** – (Optional) Train a neural gait — let PPO take the reins.  
5. **Epilogue** – Visualize triumphs in RViz & rqt, replay in rosbag.

---

## ⭐️ Key Features

- **Gazebo Simulation**  
  URDF/Xacro model and Gazebo world for testing balance and walking (ODE or Bullet).

- **ROS Control Stack**  
  Preconfigured joint-trajectory and effort controllers, IMU and force-torque sensor drivers, safety limits.

- **Hardware Abstraction**  
  YAML-driven joint ↔ actuator mappings for easy porting to real hardware.

- **Balance & Walk Demos**  
  Zero-Moment-Point (ZMP) balance controller and scripted walking sequences.

- **Optional RL Module**  
  Gym-compatible environment wrapper plus example PPO training script for gait refinement.

---

## 🧩 Pieces of the Puzzle

- **`h_bot_description/`**  
  - URDF + Xacro spells  
  - Meshes, textures, collision tweaks  

- **`h_bot_gazebo/`**  
  - World definitions (ground, lights, cameras)  
  - Plugins for physics realism (ODE, Bullet)  

- **`h_bot_control/`**  
  - ROS controllers (trajectory, effort)  
  - Safety monitors & watchdogs  

- **`h_bot_sim/`**  
  - OpenAI-Gym wrappers  
  - Example scripts: `train_gait.py`  

- **`scripts/`**  
  - Teleop and calibration helpers  
  - Demo launchers  

- **`config/launch/`**  
  - Pre-tuned PID gains  
  - RViz & rqt dashboard layouts  

---

## 🛠️ Requirements

- **OS:** Ubuntu 20.04 LTS  
- **ROS:** Noetic  
- **Simulator:** Gazebo 11 (ODE or Bullet)  
- **Language:** Python 3.8+  
- **Optional:** MuJoCo 2.3+ & `stable-baselines3`

---

## ⚙️ Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/YourUsername/h-bot.git
   cd h-bot
```

2. **Install ROS dependencies**

   ```bash
   sudo apt update
   sudo apt install ros-noetic-desktop-full ros-noetic-gazebo-ros-control \
                    python3-rosdep python3-catkin-tools
   rosdep install --from-paths src --ignore-src -r -y
   ```

3. **Build the workspace**

   ```bash
   # Using catkin
   catkin build --cmake-args -DCMAKE_BUILD_TYPE=Release
   source devel/setup.bash

   # Or using colcon
   colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
   source install/setup.bash
   ```

4. **(Optional) Python RL dependencies**

   ```bash
   pip install -r requirements-rl.txt
   ```
   
---

## 🕹 “Let the Games Begin”

* **🌍 Gazebo Sandbox**

  ```bash
  roslaunch h_bot_gazebo playground.launch
  ```

  Watch H-Bot take its first (simulated) breath.

* **🛡 Balance Demo**

  ```bash
  roslaunch h_bot_control zmp_balance.launch
  ```

  Tiptoe across virtual tightropes.

* **🤖 “Neural Gait”** *(Optional)*

  ```bash
  pip install -r requirements-rl.txt
  python scripts/train_gait.py \
    --env h_bot_sim_env \
    --algo ppo \
    --timesteps 5e5 \
    --save checkpoints/
  ```

  Let deep learning refine every step.

---

## 📝 Notes from the Engineer’s Log

* **Real-world ready?**
  Adapt `config/joint_mapping.yaml` to your hardware.

* **Physics realism**
  Tweak friction, mass, contact parameters in `h_bot_gazebo/params.sdf`.

* **Logging & Playback**
  – RViz config: `launch/rviz_h_bot.rviz`
  – Record: `rosbag record /joint_states /cmd_vel`

---

## 📂 Repository Layout

```
h-bot/
├── h_bot_description/   # URDF, Xacro, meshes
├── h_bot_gazebo/        # Gazebo worlds & plugins
├── h_bot_control/       # ROS controller nodes & configs
├── h_bot_sim/           # Gym wrappers & RL scripts
├── scripts/             # Teleop, calibration, training scripts
├── config/              # Parameter files (PID gains, safety limits)
├── launch/              # Top-level launch files
├── requirements-rl.txt  # Optional Python deps for RL
└── README.md            # This file
```

---

## 🤝 Contributing, Join the H-Bot Guild

Found a bug? Dream up a new demo?

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit and push
4. Open a Pull Request

Every contribution is a step toward more epic robot tales.

Include tests or demos for new functionality where applicable.

---

## 📄 License

© 2025 Kevin Maeville • Apache-2.0 License

