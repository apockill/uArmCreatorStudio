"""
This is for storing the location of directories that don't move
"""
from Resources import CompiledImages

resourcesLoc = "Resources\\"
settings_txt = resourcesLoc + "Settings.txt"
objects_dir  = resourcesLoc + "Objects\\"


#####     ICONS     #####
# The colon before the filename is so that it access the "compiled" images from CompiledImages.py, a QT resources system
imageLoc = ":/Icons/"

# Other
cancel             = imageLoc + "cancel.png"
delete             = imageLoc + "delete.png"


# "File" Menu
new_file            = imageLoc + "file_new.png"
save_file           = imageLoc + "file_save.png"
load_file           = imageLoc + "file_load.png"
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
creation_event      = imageLoc + "event_creation.png"
destroy_event       = imageLoc + "event_destroy.png"
step_event          = imageLoc + "event_step.png"
keyboard_event      = imageLoc + "event_keyboard.png"
tip_event           = imageLoc + "event_tip.png"
motion_event        = imageLoc + "event_motion.png"
recognize_event     = imageLoc + "event_recognize.png"


# Commands
xyz_command         = imageLoc + "command_xyz.png"
speed_command       = imageLoc + "command_speed.png"
move_wrist_command  = imageLoc + "command_move_wrist.png"
detach_command      = imageLoc + "command_detach.png"
attach_command      = imageLoc + "command_attach.png"
refresh_command     = imageLoc + "command_refresh.png"
wait_command        = imageLoc + "command_wait.png"
grip_command        = imageLoc + "command_grip.png"
drop_command        = imageLoc + "command_drop.png"
colortrack_command  = imageLoc + "command_colortrack.png"
buzzer_command      = imageLoc + "command_buzzer.png"

move_over_command   = imageLoc + "command_move_over.png"
pickup_command      = imageLoc + "command_pickup_object.png"
startblock_command  = imageLoc + "command_startblock.png"
endblock_command    = imageLoc + "command_endblock.png"
else_command        = imageLoc + "command_else.png"
set_var_command     = imageLoc + "command_set_var.png"
test_var_command    = imageLoc + "command_test_var.png"
exit_event_command  = imageLoc + "command_exit_event.png"
end_prgrm_command   = imageLoc + "command_end_program.png"
see_obj_command     = imageLoc + "command_test_see_object.png"

# Tutorial
robot_lower_head    = imageLoc + "tutorial_robot_lowering_head.gif"
selecting_marker    = imageLoc + "tutorial_selecting_marker.gif"
selecting_object    = imageLoc + "tutorial_selecting_object.gif"
selecting_pickArea  = imageLoc + "tutorial_selecting_pickup_rect.gif"
robot_cam_overview  = imageLoc + "tutorial_robot_cam_overview.png"
make_sticker        = imageLoc + "tutorial_make_sticker.png"
sticker_on_head     = imageLoc + "tutorial_sticker_on_robot_head.png"





