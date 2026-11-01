dofile(LockOn_Options.common_script_path.."devices_defs.lua")
indicator_type=indicator_types.COMMON
-- Texture producer only; no floating kneeboard UI or direct cockpit geometry.
purposes={100}
init_pageID=1
BASE,MAP=1,3
page_subsets={[BASE]=LockOn_Options.script_path.."MFD/Indicator/Map/Charts/base.lua"}
pages={{BASE,MAP}}
custom_images={}
number_of_additional_pages=0
default_page=1
function get_template()return nil end
function get_specific_element_name_by_id()return "" end
GetSelf():Add_Map_Page(MAP,LockOn_Options.script_path.."MFD/Indicator/Map/Charts/page.lua")
