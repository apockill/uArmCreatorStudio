# -*- mode: python -*-
import os

# Set up some convenience variables to shorten up the path names
project_dir  = "."
resource_dir = "Resources"                         # Resources directory
icons_dir    = os.path.join(resource_dir, "Icons") # Icons directory in resources



# Files that need to be bundled that are in resource_dir
resourceList   = ["face_cascade.xml",
                  "smile_cascade.xml",
                  "eye_cascade.xml",
                  "User Manual.pdf"]

# Files that need to be bundled that are in icons_dir
iconsList = ["cancel.png",
             "record_start.png",
             "record_end.png",
             "button_delete.png",
             "button_create.png",
             "file_new.png",
             "file_save.png",
             "file_load.png",
             "forum_link_reddit.png",
             "script_run.png",
             "script_pause.png",
             "video_pause.png",
             "video_play.png",
             "video_not_connected.png",
             "window_icon.png",
             "window_settings.png",
             "window_calibrate.png",
             "window_object_manager.png",
             "window_wizard.png",
             "window_devices_robot.png",
             "window_devices_camera.png",
             "window_devices_both.png",
             "window_devices_neither.png",
             "event_creation.png",
             "event_destroy.png",
             "event_step.png",
             "event_keyboard.png",
             "event_tip.png",
             "event_motion.png",
             "event_recognize.png",
             "event_not_recognize.png",
             "command_xyz.png",
	         "command_xyz_vision.png",
             "command_speed.png",
             "command_move_wrist.png",
             "command_wrist_rel.png",
             "command_play_path.png",
             "command_detach.png",
             "command_attach.png",
             "command_wait.png",
             "command_grip.png",
             "command_drop.png",
             "command_buzzer.png",
             "command_move_rel_to.png",
             "command_pickup.png",
             "command_startblock.png",
             "command_endblock.png",
             "command_else.png",
             "command_set_var.png",
             "command_test_var.png",
             "command_loop.png",
             "command_test_see.png",
             "command_script.png",
             "command_exit_event.png",
             "command_end_script.png",
             "command_test_region.png",
             "command_test_angle.png",
             "command_run_task.png",
             "command_run_func.png",
             "help_lower_head.gif",
             "help_sel_marker.gif",
             "help_sel_obj.gif",
             "help_sel_pickuprect.gif",
             "help_add_detail.gif",
             "help_cam_overview.png",
             "help_make_sticker.png",
             "help_marker_on_head.png",
             "help_drag_command.gif",
             "help_add_event.gif",
             "help_connect_camera.gif",
             "help_rob_connect.gif",
             "help_star.png"]

# Create a list of all the necessary resources in the format that pyInstaller wants it in
d = []

# Add the icons from the icons directory
for icon in iconsList:
    d.append((os.path.join(icons_dir, icon), os.path.join(icons_dir, icon), 'DATA'))

# Add the cascades from the resources directory
for resource in resourceList:
    d.append((os.path.join(resource_dir, resource), os.path.join(resource_dir, resource), 'DATA'))


"smile_cascade.xml"
# Actual spec file here
block_cipher = None



a = Analysis(['MainGUI.py'],
             pathex=[project_dir],
             binaries=None,
             hiddenimports=['six','packaging', 'packaging.version', 'packaging.specifiers', 'packaging.requirements'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)


pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)


exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas + d,   # Add the icons list to the data
          name='uArmCreatorStudio',
          debug=False,
          strip=False,
          console=False,
          upx=True,
          icon=os.path.join(icons_dir, "exe_icon.ico"))

