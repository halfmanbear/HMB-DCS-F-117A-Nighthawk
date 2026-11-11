local cockpit = folder.."../../../Cockpit/Scripts/"
dofile(cockpit.."command_defs.lua")
dofile(cockpit.."devices.lua")

local res = external_profile("Config/Input/Aircrafts/base_keyboard_binding.lua")
join(res.keyCommands,{
{combos = {{key = 'M', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.DATABASE, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Database PMAP / DMAP'), category = _('F-117A Displays')},
{combos = {{key = 'F', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.FUNCTION, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Function Page'), category = _('F-117A Displays')},
{combos = {{key = 'L', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.LOOK, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Manual Look'), category = _('F-117A Displays')},
{combos = {{key = 'S', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.SCROLL, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Manual Scroll'), category = _('F-117A Displays')},
{combos = {{key = 'A', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.AUTO, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Return to Auto'), category = _('F-117A Displays')},
{combos = {{key = 'Left', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.PAN_LEFT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Pan Left'), category = _('F-117A Displays')},
{combos = {{key = 'Right', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.PAN_RIGHT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Pan Right'), category = _('F-117A Displays')},
{combos = {{key = 'Up', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.PAN_UP, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Pan Forward'), category = _('F-117A Displays')},
{combos = {{key = 'Down', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.PAN_DOWN, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Pan Back'), category = _('F-117A Displays')},
{combos = {{key = 'D', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.TACTICAL_DECLUTTER, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Tactical Declutter'), category = _('F-117A Displays')},
{combos = {{key = 'B', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.BACKGROUND_DECLUTTER, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Background Declutter'), category = _('F-117A Displays')},
{combos = {{key = 'R', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.REFERENCE_ELEVATION, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Reference Elevation Mode'), category = _('F-117A Displays')},
{combos = {{key = 'PgUp', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.ELEVATION_UP, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Elevation Increase'), category = _('F-117A Displays')},
{combos = {{key = 'PgDown', reformers = {'LCtrl','LAlt','LShift'}}}, down = map_commands.ELEVATION_DOWN, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Elevation Decrease'), category = _('F-117A Displays')},

{combos = {{key = ']', reformers = {'LCtrl','LShift'}}}, down = map_commands.RANGE_UP, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Range Increase'), category = _('F-117A Displays')},
{combos = {{key = '[', reformers = {'LCtrl','LShift'}}}, down = map_commands.RANGE_DOWN, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Range Decrease'), category = _('F-117A Displays')},
{combos = {{key = 'M', reformers = {'LCtrl','LShift'}}}, down = map_commands.ORIENTATION, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Central Map Orientation Cycle'), category = _('F-117A Displays')},
{combos = {{key = '.', reformers = {'LCtrl','LAlt','LShift'}}}, down = nav_commands.WP_NEXT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Navigation Next Waypoint'), category = _('F-117A Displays')},
{combos = {{key = ',', reformers = {'LCtrl','LAlt','LShift'}}}, down = nav_commands.WP_PREV, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Navigation Previous Waypoint'), category = _('F-117A Displays')},
-- CMDI format selections preserve sensor state.
{down = left_cmdi_commands.MAP_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Left CMDI Select MAP'), category = _('F-117A Displays')},
{down = left_cmdi_commands.HSD_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Left CMDI Select HSD'), category = _('F-117A Displays')},
{down = right_cmdi_commands.MAP_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Right CMDI Select MAP'), category = _('F-117A Displays')},
{down = right_cmdi_commands.HSD_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Right CMDI Select HSD'), category = _('F-117A Displays')},
{down = right_cmdi_commands.VSD_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Right CMDI Select VSD'), category = _('F-117A Displays')},
{combos = {{key = 'E', reformers = {'LCtrl','LShift'}}}, down = left_cmdi_commands.EO_TOGGLE, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Left CMDI EO / VSD Toggle'), category = _('F-117A Displays')},
{down = left_cmdi_commands.EO_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Left CMDI Select EO'), category = _('F-117A Displays')},
{down = left_cmdi_commands.VSD_SELECT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Left CMDI Select VSD'), category = _('F-117A Displays')},

{down = f117_commands.MASTER_ARM_TOGGLE, name = _('Master Arm / Safe'), category = _('F-117A Essential System Controls')},
{down = f117_commands.WEAPON_STATION_NEXT, name = _('Weapon Station Next'), category = _('F-117A Essential System Controls')},
{down = f117_commands.WEAPON_STATION_PREV, name = _('Weapon Station Previous'), category = _('F-117A Essential System Controls')},


-- Autopilot
{combos = {{key = 'A'}}, down = iCommandPlaneAutopilot, name = _('Autopilot'), category = _('Autopilot')},
{combos = {{key = '1', reformers = {'LAlt'}}},down = iCommandPlaneStabPathHold, name 		= _('Autopilot Path Hold')			  , category = _('Autopilot')},
{combos = {{key = '2', reformers = {'LAlt'}}},down = iCommandPlaneStabHbarHeading, name 	= _('Autopilot Altitude/Heading Hold'), category = _('Autopilot')},
{combos = {{key = '4', reformers = {'LAlt'}}},down = iCommandPlane_EAC_ARM, name = _('EAC Arm'), category = _('Autopilot')},
{combos = {{key = '5', reformers = {'LAlt'}}},down = iCommandPlane_EAC_OFF, name = _('EAC Off'), category = _('Autopilot')},
{combos = {{key = '9', reformers = {'LAlt'}}},down = iCommandPlaneStabCancel, name = _('A/P - A/T Disengage Paddle'), category = {_('Autopilot'), _('HOTAS')}},
{combos = {{key = '3', reformers = {'LAlt'}}},down = f117_commands.PAARS_TOGGLE, name = _('PAARS Automatic Recovery (ARS Switch)'), category = {_('Autopilot'), _('HOTAS'), _('F-117A Essential System Controls')}},
{combos = {{key = 'J'}}, down = f117_commands.AUTOTHROTTLE_ENGAGE, name = _('Autothrottle Engage / Disengage'), category = _('Autopilot')},
{combos = {{key = 'J', reformers = {'LCtrl'}}}, down = f117_commands.AUTOTHROTTLE_DISCONNECT, name = _('Autothrottle Disengage Button'), category = {_('Autopilot'), _('Throttle Grip'), _('HOTAS')}},
{combos = {{key = 'N'}}, down = f117_commands.NWS_AUTHORITY_ON, up = f117_commands.NWS_AUTHORITY_OFF, name = _('Nosewheel Steering Authority (Hold for 45 deg Range)'), category = {_('Systems'), _('HOTAS')}},

-- Systems
{combos = {{key = 'R', reformers = {'LCtrl'}}}, down = iCommandPlaneAirRefuel, name = _('Refueling Hatch'), category = {_('Systems'), _('F-117A Essential System Controls')}},
{combos = {{key = 'P'}},						down = iCommandPlaneParachute, name = _('Drag Chute'),	category = {_('Systems'), _('F-117A Essential System Controls')}, features = {"dragchute"}},
{combos = {{key = 'G', reformers = {'LAlt'}}},  down = iCommandPlaneHook, name = _('Tail Hook'), category = {_('Systems'), _('F-117A Essential System Controls')}, features = {"tailhook"}},

-- Flight Control
{combos = {{key = 'T', reformers = {'LCtrl'}}}, down = iCommandPlaneTrimCancel, name = _('Trim Reset'), category = _('Flight Control')},

-- Modes
{combos = {{key = '6'}}, down = iCommandPlaneModeFI0, name = _('(6) Longitudinal Missile Aiming Mode'), category = _('Modes')},
{combos = {{key = '7'}}, down = iCommandPlaneModeGround, name = _('(7) Air-To-Ground Mode'), category = {_('Modes'), _('F-117A Essential System Controls')}},

-- Sensors
{combos = defaultDeviceAssignmentFor("lock_aircraft"), down = iCommandPlaneChangeLock, up = iCommandPlaneChangeLockUp, name = _('Target Lock'), category = _('Sensors')},
{combos = defaultDeviceAssignmentFor("unlock_target"), down = iCommandSensorReset, name = _('Target Unlock'), category = _('Sensors')},
{combos = {{key = 'I', reformers = {'RCtrl'}}}, down = iCommandPlaneRadarCenter, name = _('Target Designator To Center'), category = _('Sensors')},
{combos = {{key = 'O', reformers = {'RCtrl'}}}, down = iCommandPlaneNightTVOnOff, name = _('Night Vision (FLIR or LLTV) On/Off'), category = _('Sensors')},

-- RWR
{combos = {{key = 'R', reformers = {'RShift'}}}, down = iCommandChangeRWRMode, name = _('RWR/SPO Mode Select'), category = _('Sensors')},
{combos = {{key = ',', reformers = {'RAlt'}}}, down = iCommandPlaneThreatWarnSoundVolumeDown, name = _('RWR/SPO Sound Signals Volume Down'), category = _('Sensors')},
{combos = {{key = '.', reformers = {'RAlt'}}}, down = iCommandPlaneThreatWarnSoundVolumeUp, name = _('RWR/SPO Sound Signals Volume Up'), category = _('Sensors')},

-- F-117A IRADS
{combos = {{key = 'PgUp', reformers = {'LCtrl','LShift'}}}, down = irads_image_commands.BRIGHTNESS_UP, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS Brightness Increase'), category = _('F-117A IRADS')},
{combos = {{key = 'PgDown', reformers = {'LCtrl','LShift'}}}, down = irads_image_commands.BRIGHTNESS_DOWN, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS Brightness Decrease'), category = _('F-117A IRADS')},
{combos = {{key = 'PgUp', reformers = {'LCtrl','LAlt'}}}, down = irads_image_commands.CONTRAST_UP, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS Contrast Increase'), category = _('F-117A IRADS')},
{combos = {{key = 'PgDown', reformers = {'LCtrl','LAlt'}}}, down = irads_image_commands.CONTRAST_DOWN, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS Contrast Decrease'), category = _('F-117A IRADS')},
{combos = {{key = 'Home', reformers = {'LCtrl','LShift'}}}, down = irads_image_commands.RESET, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS Reset Brightness / Contrast for Mission Time'), category = _('F-117A IRADS')},
{combos = {{key = 'O'}, {key = 'I', reformers = {'LCtrl'}}}, down = iCommandPlaneEOSOnOff, name = _('IRADS On/Off'), category = {_('Sensors'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{combos = {{key = ';'}}, down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_UP, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_UP, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Up'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = '.'}}, down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DOWN, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DOWN, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Down'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = ','}}, down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_LEFT, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_LEFT, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Left'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = '/'}}, down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_RIGHT, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_RIGHT, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Right'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'Enter'}}, down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Depress / Slew Stop'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = ']'}}, down = irads_fov_commands.NARROW, cockpit_device_id = devices.DISPLAYS, value_down = 1.0,  name = _('IRADS FOV - Narrow'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{combos = {{key = '['}}, down = irads_fov_commands.WIDE, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS FOV - Wide'),   category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{combos = {{key = 'Back'}}, down = f117_commands.IRADS_DESIGNATION_CLEAR, name = _('IRADS Designation Clear'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'L', reformers = {'LShift'}}}, down = f117_commands.IRADS_LASER_ARM_TOGGLE, name = _('IRADS Laser Arm/Safe'), category = {_('Weapons'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{down = Keys.MFDOverlayToggle, name = _('DLIR MFD Overlay Toggle'), category = {_('Sensors'), _('F-117A IRADS')}},
-- Battery is the stock Electric Power Switch (RShift+L). The APU or an engine then powers the displays.
{combos = {{key = 'U', reformers = {'RShift'}}}, down = Keys.APUToggle, name = _('APU Start / Stop'), category = _('Systems')},
-- Ground crew carts, on the ground and stopped: external electrical power, and start air for the engines.
{combos = {{key = 'P', reformers = {'RCtrl','RShift'}}}, down = Keys.GroundPowerToggle, name = _('Ground Power Connect / Disconnect'), category = _('Systems')},
{combos = {{key = 'A', reformers = {'RCtrl','RShift'}}}, down = Keys.GroundAirToggle, name = _('Ground Air Connect / Disconnect'), category = _('Systems')},

-- Weapons
{combos = {{key = 'Space', reformers = {'RAlt'}}}, down = iCommandPlanePickleOn, up = iCommandPlanePickleOff, name = _('Weapon Release (Pickle)'), category = {_('Weapons'), _('F-117A Essential System Controls')}},

--Night Vision Goggles
{combos = {{key = 'H', reformers = {'LShift'}}}		   , 	down    = iCommandViewNightVisionGogglesOn   , name = _('Night Vision Goggles')   , category = _('Night Vision Goggles')},
{combos = {{key = 'H', reformers = {'LShift','LCtrl'}}}, 	pressed = iCommandPlane_Helmet_Brightess_Up  , name = _('Night Vision Goggles Gain Up')  , category = _('Night Vision Goggles')},
{combos = {{key = 'H', reformers = {'LShift','LAlt'}}} , 	pressed = iCommandPlane_Helmet_Brightess_Down, name = _('Night Vision Goggles Gain Down'), category = _('Night Vision Goggles')},

-- RADIO 1
{down = iCommandDynamicRadioPushToTalkEnableVoice, up = iCommandDynamicRadioPushToTalkDisableVoice, value_down = 0.1, value_up = 0.0, name = _('r.1 VoIP PTT'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioModulationNext, value_down = 0.1, value_up = 0.0, name = _('r.1 Modulation change'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioFreqChangeSelectorNext, value_down = 0.1, value_up = 0.0, name = _('r.1 Frequency change selector'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioFrequencyUp, value_down = 0.1, value_up = 0.0, name = _('r.1 Frequency up'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioFrequencyDown, value_down = 0.1, value_up = 0.0, name = _('r.1 Frequency down'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioChannelIncrease, value_down = 0.1, value_up = 0.0, name = _('r.1 Channel increase'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioChannelDecrease, value_down = 0.1, value_up = 0.0, name = _('r.1 Channel decrease'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioGuardChangeNext, value_down = 0.1, value_up = 0.0, name = _('r.1 Guard change'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioEncryptionOnOff, value_down = 0.1, value_up = 0.0, name = _('r.1 Encryption On/Off'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioPowerChangeNext, value_down = 0.1, value_up = 0.0, name = _('r.1 Power change'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioSquelchOnOff, value_down = 0.1, value_up = 0.0, name = _('r.1 Squelch On/Off'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioVolumeUp, value_down = 0.1, value_up = 0.0, name = _('r.1 Volume up'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioVolumeDown, value_down = 0.1, value_up = 0.0, name = _('r.1 Volume down'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioBalanceLeft, value_down = 0.1, value_up = 0.0, name = _('r.1 Balance left'), category = {_('Radio'), _('Radio 1')} },
{down = iCommandDynamicRadioBalanceRight, value_down = 0.1, value_up = 0.0, name = _('r.1 Balance right'), category = {_('Radio'), _('Radio 1')} },

-- RADIO 2
{down = iCommandDynamicRadioPushToTalkEnableVoice, up = iCommandDynamicRadioPushToTalkDisableVoice, value_down = 0.2, value_up = 0.0, name = _('r.2 VoIP PTT'), category = {_('Radio'), _('Radio 2')} },
{down = iCommandDynamicRadioModulationNext, value_down = 0.2, value_up = 0.0, name = _('r.2 Modulation change'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioFreqChangeSelectorNext, value_down = 0.2, value_up = 0.0, name = _('r.2 Frequency change selector'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioFrequencyUp, value_down = 0.2, value_up = 0.0, name = _('r.2 Frequency up'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioFrequencyDown, value_down = 0.2, value_up = 0.0, name = _('r.2 Frequency down'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioChannelIncrease, value_down = 0.2, value_up = 0.0, name = _('r.2 Channel increase'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioChannelDecrease, value_down = 0.2, value_up = 0.0, name = _('r.2 Channel decrease'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioGuardChangeNext, value_down = 0.2, value_up = 0.0, name = _('r.2 Guard change'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioEncryptionOnOff, value_down = 0.2, value_up = 0.0, name = _('r.2 Encryption On/Off'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioPowerChangeNext, value_down = 0.2, value_up = 0.0, name = _('r.2 Power change'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioSquelchOnOff, value_down = 0.2, value_up = 0.0, name = _('r.2 Squelch On/Off'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioVolumeUp, value_down = 0.2, value_up = 0.0, name = _('r.2 Volume up'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioVolumeDown, value_down = 0.2, value_up = 0.0, name = _('r.2 Volume down'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioBalanceLeft, value_down = 0.2, value_up = 0.0, name = _('r.2 Balance left'), category = {_('Radio'), _('Radio 2')}},
{down = iCommandDynamicRadioBalanceRight, value_down = 0.2, value_up = 0.0, name = _('r.2 Balance right'), category = {_('Radio'), _('Radio 2')}},

-- Lights
{down = Keys.PanelLight, name = _('Panel Light ON/OFF'), category = _('Lighting')},
{down = Keys.FloodLight, name = _('Flood Light ON/OFF'), category = _('Lighting')},
{down = Keys.LdgLight, name = _('Landing Lights ON/OFF'), category = _('Lighting')},
{down = Keys.NavLight, name = _('Navigation Lights ON/OFF'), category = _('Lighting')},
{down = Keys.TaxiLgt, name = _('Taxi Lights AUTO/ON/OFF'), category = _('Lighting')},
{down = Keys.MemeLgt, name = _('Meme Light ON/OFF'), category = _('Lighting')},
{down = Keys.BcnLgt, name = _('Beacon Light ON/OFF'), category = _('Lighting')},

--Misc
{combos = {{key = 'T', reformers = {'LShift'}}}, down = f117_commands.BOMB_BAY_TOGGLE, name = _('Bomb Bay Doors Toggle (Both)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},
{combos = {{key = 'T', reformers = {'LShift','LCtrl'}}}, down = f117_commands.BOMB_BAY_SELECTED_TOGGLE, name = _('Bomb Bay Door Toggle (Selected Store)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},
{combos = {{key = 'T', reformers = {'LShift','LAlt'}}}, down = f117_commands.BOMB_BAY_LEFT_TOGGLE, name = _('Bomb Bay Door Toggle (Left)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},
{combos = {{key = 'T', reformers = {'LShift','RAlt'}}}, down = f117_commands.BOMB_BAY_RIGHT_TOGGLE, name = _('Bomb Bay Door Toggle (Right)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},

})

return res
