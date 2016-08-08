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



################        PATHS FOR ALL       ################
resourcesLoc = "Resources\\"
settings_txt = resourcesLoc + "Settings.txt"
objects_dir  = resourcesLoc + "Objects\\"
saves_dir    = resourcesLoc + "Saves\\"




def resourcePath(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

exeResourcesPath = resourcePath(resourcesLoc)

# Used by Vision
cascade_dir  = exeResourcesPath



################        GUI PATHS         ################
imageLoc = resourcePath("Resources\\Icons\\")

create              = imageLoc + "button_create.png"
delete              = imageLoc + "button_delete.png"


# "File" Menu
file_new            = imageLoc + "file_new.png"
file_save           = imageLoc + "file_save.png"
file_load           = imageLoc + "file_load.png"
reddit_link         = imageLoc + "forum_link_reddit.png"


# Toolbar
run_script          = imageLoc + "script_run.png"
pause_script        = imageLoc + "script_pause.png"
pause_video         = imageLoc + "video_pause.png"
play_video          = imageLoc + "video_play.png"
video_not_connected = imageLoc + "video_not_connected.png"
record_start        = imageLoc + "record_start.png"
record_end          = imageLoc + "record_end.png"
taskbar             = imageLoc + "window_ufactory_logo.png"
settings            = imageLoc + "window_settings.png"
calibrate           = imageLoc + "window_calibrate.png"
objectManager       = imageLoc + "window_object_manager.png"
objectWizard        = imageLoc + "window_wizard.png"


# Events
event_creation      = imageLoc + "event_creation.png"
event_destroy       = imageLoc + "event_destroy.png"
event_step          = imageLoc + "event_step.png"
event_keyboard      = imageLoc + "event_keyboard.png"
event_tip           = imageLoc + "event_tip.png"
event_motion        = imageLoc + "event_motion.png"
event_recognize     = imageLoc + "event_recognize.png"
event_not_recognize = imageLoc + "event_not_recognize.png"


# Commands
command_xyz         = imageLoc + "command_xyz.png"
command_xyz_vision  = imageLoc + "command_xyz_vision.png"
command_speed       = imageLoc + "command_speed.png"
command_move_wrist  = imageLoc + "command_move_wrist.png"
command_wrist_rel   = imageLoc + "command_wrist_rel.png"
command_play_path   = imageLoc + "command_play_path.png"
command_detach      = imageLoc + "command_detach.png"
command_attach      = imageLoc + "command_attach.png"
command_refresh     = imageLoc + "command_refresh.png"
command_wait        = imageLoc + "command_wait.png"
command_grip        = imageLoc + "command_grip.png"
command_drop        = imageLoc + "command_drop.png"
command_buzzer      = imageLoc + "command_buzzer.png"
command_move_rel_to = imageLoc + "command_move_rel_to.png"
command_pickup      = imageLoc + "command_pickup.png"
command_startblock  = imageLoc + "command_startblock.png"
command_endblock    = imageLoc + "command_endblock.png"
command_else        = imageLoc + "command_else.png"
command_set_var     = imageLoc + "command_set_var.png"
command_test_var    = imageLoc + "command_test_var.png"
command_loop        = imageLoc + "command_loop.png"
command_script      = imageLoc + "command_script.png"
command_exit_event  = imageLoc + "command_exit_event.png"
command_end_script  = imageLoc + "command_end_script.png"
command_see_obj     = imageLoc + "command_see_obj.png"
command_see_loc     = imageLoc + "command_see_loc.png"
command_test_angle  = imageLoc + "command_test_angle.png"
command_run_task    = imageLoc + "command_run_task.png"
command_run_func    = imageLoc + "command_run_func.png"

# Tutorial Materials
help_lower_head     = imageLoc + "help_lower_head.gif"
help_sel_marker     = imageLoc + "help_sel_marker.gif"
help_sel_obj        = imageLoc + "help_sel_obj.gif"
help_sel_pickuprect = imageLoc + "help_sel_pickuprect.gif"
help_add_detail     = imageLoc + "help_add_detail.gif"
help_cam_overview   = imageLoc + "help_cam_overview.png"
help_make_sticker   = imageLoc + "help_make_sticker.png"
help_marker_on_head = imageLoc + "help_sticker_on_head.png"
help_star           = imageLoc + "help_star.png"
help_drag_command   = imageLoc + "help_drag_command.gif"
help_add_event      = imageLoc + "help_add_event.gif"
help_connect_camera = imageLoc + "help_connect_camera.gif"
help_rob_connect    = imageLoc + "help_rob_connect.gif"


