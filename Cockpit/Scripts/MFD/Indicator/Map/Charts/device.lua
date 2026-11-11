-- avKneeboard reads these values after injecting x_start/z_start.
use_lat_lon=false
lat_lon_aspect=1
number_of_additional_pages=0
need_to_be_closed=true
function generate_maps()
    -- Exactly one writable chart record, isolated from the user's kneeboard.
    map_pages={{scale=23150,chart=3,rotation=0,x=x_start,z=z_start}}
end
function on_waypoint_adding()end
