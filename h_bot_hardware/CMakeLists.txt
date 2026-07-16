cmake_minimum_required(VERSION 3.0.2)
project(h_bot_hardware)

## 🦾 H-Bot Hardware Bridge — Act I: Feel the joints
## This CMakeLists.txt is intentionally minimal so beginners can read it
## without drowning in boilerplate.

find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
  std_msgs
  trajectory_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy sensor_msgs std_msgs trajectory_msgs
)

## Tell catkin where to install Python executables.
## No C++ nodes yet, so we only install Python scripts and launch files.
catkin_install_python(PROGRAMS
  scripts/hardware_bridge.py
  scripts/mock_hardware.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## Install launch files so `roslaunch h_bot_hardware ...` works.
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
