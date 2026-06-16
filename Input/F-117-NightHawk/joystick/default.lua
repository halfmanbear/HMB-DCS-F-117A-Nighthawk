local cockpit = folder.."../../../Cockpit/Scripts/"
dofile(cockpit.."command_defs.lua")

local res = external_profile("Config/Input/Aircrafts/base_joystick_binding.lua")
join(res.keyCommands,{

-- Autopilot
{down = iCommandPlaneAutopilot, name = _('Autopilot'), category = _('Autopilot')},
{down = iCommandPlaneStabPathHold, name 		= _('Autopilot Path Hold')			  , category = _('Autopilot')},
{down = iCommandPlaneStabHbarHeading, name 		= _('Autopilot Altitude/Heading Hold'), category = _('Autopilot')},
{down = iCommandPlane_EAC_ARM, name = _('EAC Arm'), category = _('Autopilot')},
{down = iCommandPlane_EAC_OFF, name = _('EAC Off'), category = _('Autopilot')},

-- Systems
{down = iCommandPlaneAirRefuel, name = _('Refueling Bay'), category = {_('Systems'), _('F-117A Essential System Controls')}},
{down = iCommandPlaneParachute,	name = _('Drag Chute'), category = {_('Systems'), _('F-117A Essential System Controls')}, features = {"dragchute"}},
{down = iCommandPlaneHook, 		name = _('Tail Hook'), category = {_('Systems'), _('F-117A Essential System Controls')}, features = {"tailhook"}},

-- Flight Control
{down = iCommandPlaneTrimCancel, name = _('Trim Reset'), category = _('Flight Control')},

-- Modes
{down = iCommandPlaneModeFI0, name = _('(6) Longitudinal Missile Aiming Mode'), category = _('Modes')},
{down = iCommandPlaneModeGround, name = _('(7) Air-To-Ground Mode'), category = {_('Modes'), _('F-117A Essential System Controls')}},

-- Sensors
{combos = defaultDeviceAssignmentFor("lock_aircraft"), down = iCommandPlaneChangeLock, up = iCommandPlaneChangeLockUp, name = _('Target Lock'), category = _('Sensors')},
{combos = defaultDeviceAssignmentFor("unlock_target"), down = iCommandSensorReset, name = _('Target Unlock'), category = _('Sensors')},
{down = iCommandPlaneRadarCenter, name = _('Target Designator To Center'), category = _('Sensors')},
{down = iCommandPlaneEOSOnOff, name = _('Electro-Optical System On/Off'), category = {_('Sensors'), _('F-117A Essential System Controls')}},
{down = iCommandPlaneLaserRangerOnOff, name = _('Laser Ranger On/Off'), category = {_('Sensors'), _('F-117A Essential System Controls')}},
{down = iCommandPlaneNightTVOnOff, name = _('Night Vision (FLIR or LLTV) On/Off'), category = _('Sensors')},
{pressed = iCommandPlaneRadarUp, up = iCommandPlaneRadarStop, name = _('Target Designator Up'), category = _('Sensors')},
{pressed = iCommandPlaneRadarDown, up = iCommandPlaneRadarStop, name = _('Target Designator Down'), category = _('Sensors')},
{pressed = iCommandPlaneRadarLeft, up = iCommandPlaneRadarStop, name = _('Target Designator Left'), category = _('Sensors')},
{pressed = iCommandPlaneRadarRight, up = iCommandPlaneRadarStop, name = _('Target Designator Right'), category = _('Sensors')},
{down = iCommandPlaneZoomIn, name = _('Display Zoom In'), category = {_('Sensors'), _('F-117A Essential System Controls')}},
{down = iCommandPlaneZoomOut, name = _('Display Zoom Out'), category = {_('Sensors'), _('F-117A Essential System Controls')}},

-- RWR
{down = iCommandChangeRWRMode, name = _('RWR/SPO Mode Select'), category = _('Sensors')},
{down = iCommandPlaneThreatWarnSoundVolumeDown, name = _('RWR/SPO Sound Signals Volume Down'), category = _('Sensors')},
{down = iCommandPlaneThreatWarnSoundVolumeUp, name = _('RWR/SPO Sound Signals Volume Up'), category = _('Sensors')},

-- F-117A IRADS
{down = iCommandTVSensor,    name = _('IRADS On/Off'),  category = {_('Sensors'), _('F-117A IRADS')}},
{down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_UP, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_UP, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Up'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DOWN, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DOWN, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Down'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_LEFT, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_LEFT, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Left'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_RIGHT, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_RIGHT, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Right'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, value_down = 1.0, value_up = 0.0, name = _('Throttle Designator Controller - Depress / Slew Stop'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{down = Keys.IRADSZoomIn,  value_down = 1.0, name = _('IRADS FOV - Narrow'), category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},
{down = Keys.IRADSZoomOut, value_down = 1.0, name = _('IRADS FOV - Wide'),   category = {_('Throttle Grip'), _('HOTAS'), _('F-117A IRADS')}},

-- Weapons
{combos = defaultDeviceAssignmentFor("weapon_release_button"), down = iCommandPlanePickleOn,	up = iCommandPlanePickleOff, name = _('Weapon Release'), category = {_('Weapons'), _('F-117A Essential System Controls')}},

--Night Vision Goggles
{down    = iCommandViewNightVisionGogglesOn   , name = _('Night Vision Goggles')   , category = _('Night Vision Goggles')},
{pressed = iCommandPlane_Helmet_Brightess_Up  , name = _('Night Vision Goggles Gain Up')  , category = _('Night Vision Goggles')},
{pressed = iCommandPlane_Helmet_Brightess_Down, name = _('Night Vision Goggles Gain Down'), category = _('Night Vision Goggles')},

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
{down = 10001, name = _('Panel Light ON/OFF'), category = _('Lighting')},
{down = 10002, name = _('Flood Light ON/OFF'), category = _('Lighting')},
{down = 10003, name = _('Landing Lights ON/OFF'), category = _('Lighting')},
{down = 10004, name = _('Navigation Lights ON/OFF'), category = _('Lighting')},
{down = 10005, name = _('Taxi Lights AUTO/ON/OFF'), category = _('Lighting')},
{down = 10006, name = _('Meme Light ON/OFF'), category = _('Lighting')},
{down = 10007, name = _('Beacon Light ON/OFF'), category = _('Lighting')},

-- Misc
{down = 10100, name = _('Bomb Bay Door Toggle'), category = {_('EFM Misc'), _('F-117A Essential System Controls')}},

})
-- joystick axes 
join(res.axisCommands,{
{action = iCommandPlaneSelecterHorizontalAbs, name = _('TDC Slew Horizontal'), category = _('F-117A Essential System Controls')},
{action = iCommandPlaneSelecterVerticalAbs	, name = _('TDC Slew Vertical'), category = _('F-117A Essential System Controls')},
{action = iCommandPlaneMFDZoomAbs 			, name = _('MFD Zoom'), category = _('F-117A Essential System Controls')},
{action = iCommandPlaneBase_DistanceAbs 	, name = _('Target Box Size'), category = _('F-117A Essential System Controls')},
})

return res
