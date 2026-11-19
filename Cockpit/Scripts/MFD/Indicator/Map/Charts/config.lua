-- Generic DCS chart producer. The native adapter checks the DCS layout at run time.
-- Disable here to restore the background-only fallback without changing EO.
-- render_target is the zero-based target, whose texture is mfd<render_target>.
return {enabled=true,render_target=5}
