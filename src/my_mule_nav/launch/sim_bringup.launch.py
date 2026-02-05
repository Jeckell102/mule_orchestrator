```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_dir = get_package_share_directory('my_mule_nav')
    
    # Per PE-01: Switching to cafe.world as a diagnostic for empty world launch.
    # This world is more complex and serves as a better validation environment.
    world_file = '/usr/share/gazebo-11/worlds/cafe.world'
    
    params_file = os.path.join(pkg_dir, 'param', 'mule_params.yaml')
    bt_file = os.path.join(pkg_dir, 'param', 'mule_bt.xml')
    rviz_config = os.path.join(pkg_dir, 'param', 'mule_view.rviz')

    # 1. GAZEBO (The Cafe World)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
            launch_arguments={'world': world_file}.items()
    )

    # 2. THE BRAIN (Nav2)
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_dir, 'launch', 'bringup.launch.py')),
        launch_arguments={
            'params_file': params_file,
            'default_nav_to_pose_bt_xml': bt_file,
            'default_nav_through_poses_bt_xml': bt_file,
            'use_sim_time': 'True'
        }.items()
    )

    # 3. THE EYES (RViz)
    rviz_node = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        nav2_launch,
        rviz_node
    ])
```