-- Control stick visibility. Follows the DCS "Hide Stick" option through the
-- HIDE_STICK parameter, which mainpanel_init.lua maps to argument 153.
-- Cockpit_F-117.edm has no argument 153 yet, so the stick stays visible until
-- the cockpit model keys the stick's visibility to it.
get_param_handle("HIDE_STICK"):set(get_option_value("difficulty.hideStick", "local") == true and 1 or 0)

need_to_be_closed = true -- the parameter keeps its value after the state closes
