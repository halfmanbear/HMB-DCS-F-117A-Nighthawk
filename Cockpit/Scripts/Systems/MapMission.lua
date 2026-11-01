-- Explicit mission-planning overlay. DCS world coordinates, metres:
-- x=north, z=east; these are stored points, never live detected threats.
-- Route: {x=...,z=...,kind="navigation",label="23"}
-- Kinds: navigation, takeoff, ingress, target, offset, initial, refuel.
-- Threat: {x=...,z=...,code="6"}; see docs/ocip-cockpit-research.md.
-- Leave empty until supplied by a mission integration or a local plan.
return {route={},threats={}}
