local cockpit = folder.."../../../Cockpit/Scripts/"
dofile(cockpit.."command_defs.lua")
dofile(cockpit.."devices.lua")

local res = external_profile("Config/Input/Aircrafts/base_keyboard_binding.lua")
-- The inherited FC3 near/far/off label describes a three-state control; our
-- landing and taxi switches are independent. Keep command IDs and saved bindings.
for binding_index,binding in ipairs(res.keyCommands) do
    if binding.down == iCommandPlaneHeadLightOnOff then
        binding.name = _('Landing Light ON/OFF')
        binding.category = _('Lighting')
    end
end
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

{down = iCommandPlaneAHCPMasterArm, name = _('Master Arm'), category = _('F-117A Essential System Controls')},
{down = iCommandPlaneAHCPMasterSafe, name = _('Master Safe'), category = _('F-117A Essential System Controls')},
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
{combos = {{key = 'N'}}, down = iCommandPlane_HOTAS_NoseWheelSteeringButton, up = iCommandPlane_HOTAS_NoseWheelSteeringButtonOff, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, value_up = 0.0, name = _('Nosewheel Steering Authority (Hold for 45 deg Range)'), category = {_('Systems'), _('HOTAS')}},

-- Systems
{combos = {{key = 'R', reformers = {'LCtrl'}}}, down = iCommandPlaneAirRefuel, name = _('Refueling Hatch'), category = {_('Systems'), _('F-117A Essential System Controls')}},
{combos = {{key = 'P'}},						down = iCommandPlaneParachute, name = _('Drag Chute'),	category = {_('Systems'), _('F-117A Essential System Controls')}, features = {"dragchute"}},
{combos = {{key = 'G', reformers = {'LAlt'}}},  down = iCommandPlaneHook, name = _('Tail Hook'), category = {_('Systems'), _('F-117A Essential System Controls')}, features = {"tailhook"}},

-- Flight Control
{combos = {{key = 'T', reformers = {'LCtrl'}}}, down = iCommandPlaneTrimCancel, name = _('Trim Reset'), category = _('Flight Control')},

-- Modes
{combos = {{key = '7'}}, down = iCommandPlaneModeGround, name = _('(7) Air-To-Ground Mode'), category = {_('Modes'), _('F-117A Essential System Controls')}},

-- Sensors
{combos = defaultDeviceAssignmentFor("lock_aircraft"), down = iCommandPlaneChangeLock, up = iCommandPlaneChangeLockUp, name = _('Target Lock'), category = _('Sensors')},
{combos = defaultDeviceAssignmentFor("unlock_target"), down = iCommandSensorReset, name = _('IRADS Scan Return / Undesignate'), category = {_('Throttle Grip'), _('HOTAS'), _('Sensors'), _('F-117A IRADS')}},
{combos = {{key = 'I', reformers = {'RCtrl'}}}, down = iCommandPlaneRadarCenter, name = _('Target Designator To Center'), category = _('Sensors')},


-- F-117A IRADS
{combos = {{key = 'PgUp', reformers = {'LCtrl','LShift'}}}, down = iCommandPlane_I251_Brightness_Up, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IR Level Increase'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'PgDown', reformers = {'LCtrl','LShift'}}}, down = iCommandPlane_I251_Brightness_Down, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IR Level Decrease'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'PgUp', reformers = {'LCtrl','LAlt'}}}, down = iCommandPlane_I251_Contrast_Up, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IR Gain Increase'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'PgDown', reformers = {'LCtrl','LAlt'}}}, down = iCommandPlane_I251_Contrast_Down, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IR Gain Decrease'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'O'}, {key = 'I', reformers = {'LCtrl'}}}, down = iCommandPlaneEOSOnOff, name = _('IRADS On/Off'), category = {_('Sensors'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{combos = {{key = ';'}}, down = iCommandSelecterUp, up = iCommandSelecterStop, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Up'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = '.'}}, down = iCommandSelecterDown, up = iCommandSelecterStop, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Down'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = ','}}, down = iCommandSelecterLeft, up = iCommandSelecterStop, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Left'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = '/'}}, down = iCommandSelecterRight, up = iCommandSelecterStop, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Right'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = 'Enter'}}, down = iCommandPlane_HOTAS_TDC_depress_on, up = iCommandPlane_HOTAS_TDC_depress_off, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Depress / Slew Stop'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
-- Control-stick Designate Select switch: what the throttle X-Y slew/designate switch drives.
{combos = {{key = '1', reformers = {'RCtrl','RShift'}}}, down = iCommandPlane_HOTAS_TargetManagementSwitchOff, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Designate Select - Center (IRADS)'), category = {_('Control Stick'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = '2', reformers = {'RCtrl','RShift'}}}, down = iCommandPlane_HOTAS_TargetManagementSwitchUp, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Designate Select - Up (HUD)'), category = {_('Control Stick'), _('HOTAS'), _('F-117A IRADS')}},
{combos = {{key = '3', reformers = {'RCtrl','RShift'}}}, down = iCommandPlane_HOTAS_TargetManagementSwitchLeft, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Designate Select - Left (MAP)'), category = {_('Control Stick'), _('HOTAS'), _('F-117A IRADS')}},
{down = iCommandPlane_HOTAS_TargetManagementSwitchDown, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Designate Select - Down (not used)'), category = {_('Control Stick'), _('HOTAS'), _('F-117A IRADS')}},
{down = iCommandPlane_HOTAS_TargetManagementSwitchRight, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Designate Select - Right (not used)'), category = {_('Control Stick'), _('HOTAS'), _('F-117A IRADS')}},
-- MARK and sensor update (Systems/NavUpdate.lua): no default keys, assign in Controls.
{down = update_commands.MARK, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('MARK Point (94-98)'), category = {_('F-117A Displays'), _('F-117A IRADS')}},
{down = update_commands.SNSR, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('SNSR Sensor Update'), category = {_('F-117A Displays'), _('F-117A IRADS')}},
{down = update_commands.UPDT, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('Map UPDT Sensor Update'), category = {_('F-117A Displays'), _('F-117A IRADS')}},
{down = update_commands.ENTR, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('ENTR (Accept)'), category = {_('F-117A Displays'), _('F-117A IRADS')}},
{down = update_commands.CLR, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('CLR (Reject / Clear Alerts)'), category = {_('F-117A Displays'), _('F-117A IRADS')}},
{combos = {{key = ']'}}, down = iCommandPlaneZoomIn, cockpit_device_id = devices.DISPLAYS, value_down = 1.0,  name = _('IRADS FOV - Narrow'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{combos = {{key = '['}}, down = iCommandPlaneZoomOut, cockpit_device_id = devices.DISPLAYS, value_down = 1.0, name = _('IRADS FOV - Wide'),   category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{down = iCommandPlaneAHCPLaserArm, name = _('IRADS Laser Arm'), category = {_('Weapons'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
{down = iCommandPlaneAHCPLaserSafe, name = _('IRADS Laser Safe'), category = {_('Weapons'), _('F-117A IRADS'), _('F-117A Essential System Controls')}},
-- Battery is the stock Electric Power Switch (RShift+L). The APU or an engine then powers the displays.
{down = iCommandPlane_APU_Start, name = _('APU Start'), category = _('Systems')},
{down = iCommandPlane_APU_Off, name = _('APU Stop'), category = _('Systems')},
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
{down = Keys.FloodLight, name = _('Flood Light ON/OFF'), category = _('Lighting')},
{down = iCommandPlaneLGPTaxiLight, name = _('Taxi Light ON/OFF'), category = _('Lighting')},
{down = iCommandPlaneAntiCollisionLights, name = _('Beacon Light ON/OFF'), category = _('Lighting')},

--Misc
{combos = {{key = 'T', reformers = {'LShift'}}}, down = f117_commands.BOMB_BAY_TOGGLE, name = _('Bomb Bay Doors Toggle (Both)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},
{combos = {{key = 'T', reformers = {'LShift','LCtrl'}}}, down = f117_commands.BOMB_BAY_SELECTED_TOGGLE, name = _('Bomb Bay Door Toggle (Selected Store)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},
{combos = {{key = 'T', reformers = {'LShift','LAlt'}}}, down = f117_commands.BOMB_BAY_LEFT_TOGGLE, name = _('Bomb Bay Door Toggle (Left)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},
{combos = {{key = 'T', reformers = {'LShift','RAlt'}}}, down = f117_commands.BOMB_BAY_RIGHT_TOGGLE, name = _('Bomb Bay Door Toggle (Right)'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},

})

return res
