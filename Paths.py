"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import sys
__author__ = "Alexander Thiel"

#TODO: Make it possible to check if this is being run from within a package manager, and load icons from a diff dir.

################        PATHS FOR ALL       ################
resourcesLoc = "Resources"
settings_txt = os.path.join(resourcesLoc, "Settings.txt")
objects_dir  = os.path.join(resourcesLoc, "Objects", "")
saves_dir    = os.path.join(resourcesLoc, "Save Files", "")




def resourcePath(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

exeResourcesPath = resourcePath(resourcesLoc)

# Used by Vision
cascade_dir  = exeResourcesPath
user_manual  = os.path.join(exeResourcesPath, "User Manual.pdf")


################        GUI PATHS         ################
imageLoc = resourcePath(os.path.join(resourcesLoc, "Icons"))

create              = os.path.join(imageLoc, "button_create.png")
delete              = os.path.join(imageLoc, "button_delete.png")


# "File" Menu
file_new            = os.path.join(imageLoc, "file_new.png")
file_save           = os.path.join(imageLoc, "file_save.png")
file_load           = os.path.join(imageLoc, "file_load.png")
reddit_link         = os.path.join(imageLoc, "forum_link_reddit.png")


# Toolbar
run_script          = os.path.join(imageLoc, "script_run.png")
pause_script        = os.path.join(imageLoc, "script_pause.png")
pause_video         = os.path.join(imageLoc, "video_pause.png")
play_video          = os.path.join(imageLoc, "video_play.png")
video_not_connected = os.path.join(imageLoc, "video_not_connected.png")
record_start        = os.path.join(imageLoc, "record_start.png")
record_end          = os.path.join(imageLoc, "record_end.png")
taskbar             = os.path.join(imageLoc, "window_icon.png")
settings            = os.path.join(imageLoc, "window_settings.png")
calibrate           = os.path.join(imageLoc, "window_calibrate.png")
objectManager       = os.path.join(imageLoc, "window_object_manager.png")
objectWizard        = os.path.join(imageLoc, "window_wizard.png")

devices_robot       = os.path.join(imageLoc, "window_devices_robot.png")
devices_camera      = os.path.join(imageLoc, "window_devices_camera.png")
devices_both        = os.path.join(imageLoc, "window_devices_both.png")
devices_neither     = os.path.join(imageLoc, "window_devices_neither.png")


# Events
event_creation      = os.path.join(imageLoc, "event_creation.png")
event_destroy       = os.path.join(imageLoc, "event_destroy.png")
event_step          = os.path.join(imageLoc, "event_step.png")
event_keyboard      = os.path.join(imageLoc, "event_keyboard.png")
event_tip           = os.path.join(imageLoc, "event_tip.png")
event_motion        = os.path.join(imageLoc, "event_motion.png")
event_recognize     = os.path.join(imageLoc, "event_recognize.png")
event_not_recognize = os.path.join(imageLoc, "event_not_recognize.png")


# Commands
command_xyz         = os.path.join(imageLoc, "command_xyz.png")
command_xyz_vision  = os.path.join(imageLoc, "command_xyz_vision.png")
command_speed       = os.path.join(imageLoc, "command_speed.png")
command_move_wrist  = os.path.join(imageLoc, "command_move_wrist.png")
command_wrist_rel   = os.path.join(imageLoc, "command_wrist_rel.png")
command_play_path   = os.path.join(imageLoc, "command_play_path.png")
command_detach      = os.path.join(imageLoc, "command_detach.png")
command_attach      = os.path.join(imageLoc, "command_attach.png")
command_wait        = os.path.join(imageLoc, "command_wait.png")
command_grip        = os.path.join(imageLoc, "command_grip.png")
command_drop        = os.path.join(imageLoc, "command_drop.png")
command_buzzer      = os.path.join(imageLoc, "command_buzzer.png")
command_move_rel_to = os.path.join(imageLoc, "command_move_rel_to.png")
command_pickup      = os.path.join(imageLoc, "command_pickup.png")
command_startblock  = os.path.join(imageLoc, "command_startblock.png")
command_endblock    = os.path.join(imageLoc, "command_endblock.png")
command_else        = os.path.join(imageLoc, "command_else.png")
command_set_var     = os.path.join(imageLoc, "command_set_var.png")
command_test_var    = os.path.join(imageLoc, "command_test_var.png")
command_loop        = os.path.join(imageLoc, "command_loop.png")
command_script      = os.path.join(imageLoc, "command_script.png")
command_exit_event  = os.path.join(imageLoc, "command_exit_event.png")
command_end_script  = os.path.join(imageLoc, "command_end_script.png")
command_test_see    = os.path.join(imageLoc, "command_test_see.png")
command_test_region = os.path.join(imageLoc, "command_test_region.png")
command_test_angle  = os.path.join(imageLoc, "command_test_angle.png")
command_run_task    = os.path.join(imageLoc, "command_run_task.png")
command_run_func    = os.path.join(imageLoc, "command_run_func.png")

# Tutorial Materials
help_lower_head     = os.path.join(imageLoc, "help_lower_head.gif")
help_sel_marker     = os.path.join(imageLoc, "help_sel_marker.gif")
help_sel_obj        = os.path.join(imageLoc, "help_sel_obj.gif")
help_sel_pickuprect = os.path.join(imageLoc, "help_sel_pickuprect.gif")
help_add_detail     = os.path.join(imageLoc, "help_add_detail.gif")
help_cam_overview   = os.path.join(imageLoc, "help_cam_overview.png")
help_make_sticker   = os.path.join(imageLoc, "help_make_sticker.png")
help_marker_on_head = os.path.join(imageLoc, "help_sticker_on_head.png")
help_star           = os.path.join(imageLoc, "help_star.png")
help_drag_command   = os.path.join(imageLoc, "help_drag_command.gif")
help_add_event      = os.path.join(imageLoc, "help_add_event.gif")
help_connect_camera = os.path.join(imageLoc, "help_connect_camera.gif")
help_rob_connect    = os.path.join(imageLoc, "help_rob_connect.gif")


