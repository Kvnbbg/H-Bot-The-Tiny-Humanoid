cmake_minimum_required(VERSION 3.0.2)
project(h_bot_description)

# H-Bot: The Tiny Humanoid — CMakeLists.txt
#
# This package is data-only (URDF + YAML).  It does not compile any code,
# so we just declare a catkin package and install the description files.
#
# If you do not have ROS/catkin installed, these files are still useful:
#   * urdf/h_bot.urdf          → robot model
#   * config/joint_mapping.yaml → hardware mapping
#
# Build instructions once ROS is installed:
#   cd ~/catkin_ws/src
#   ln -s /path/to/H-Bot-The-Tiny-Humanoid/h_bot_description .
#   cd ..
#   catkin build h_bot_description
#   source devel/setup.bash

find_package(catkin REQUIRED)

catkin_package()

# Install URDF and configuration directories so other ROS packages can
# reference them via $(find h_bot_description)/urdf/h_bot.urdf
install(DIRECTORY urdf config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
