-- Manual-derived presentation; geographic backgrounds are not installed.
local M={}
-- navigation (Systems/Navigation.lua) supplies the mission route and active
-- waypoint; plan supplies stored threats, and a route when navigation is absent.
-- options.manual_allowed() gates entering LOOK / SCROLL: the manual allows them only with the
-- Designate Select switch LEFT (TO 1F-117A-1A, map section). Default: always allowed.
function M.new(sensor,plan,navigation,options)
    options=options or {}
    local manual_allowed=options.manual_allowed or function()return true end
    sensor=sensor or get_base_data()
    plan=plan or dofile(LockOn_Options.script_path.."Systems/MapMission.lua")
    local source=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_source.lua")
    local source_config=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/render_source.lua")
    local source_configured=source.configured(source_config)
    -- The chart and aperture fill the whole CMDI glass; symmetric half extents in map units.
    local window=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_window.lua").cmdi()
    local chart_backend=dofile(LockOn_Options.script_path.."Systems/ChartBackend.lua").new(source_config)
    local handles={}
    local function h(name)
        if not handles[name] then handles[name]=get_param_handle("F117_MAP_"..name) end
        return handles[name]
    end
    local function set(name,value)h(name):set(value)end
    -- Labels are drawn with "%s" and may look numeric, so never use set() for them.
    local text=dofile(LockOn_Options.script_path.."Systems/TextParameter.lua").new()
    local function set_label(prefix,label)
        text.set("F117_MAP_"..prefix.."LABEL",tostring(label):sub(1,6))
    end
    local function finite(v)return type(v)=="number" and v==v and math.abs(v)<1e12 end
    local ranges={10,25,50,100,140}
    local modes={"CNUP","CTUP","DNUP","DTUP"}
    local kinds={navigation=1,takeoff=1,ingress=1,target=2,offset=3,initial=4,refuel=5}
    local codes={Q=true,TR=true,HF=true,GC=true,C=true,R=true,H=true,A=true,E=true,
        ["2"]=true,["3"]=true,["4"]=true,["5"]=true,["6"]=true,["8"]=true,
        ["10"]=true,["11"]=true,["12"]=true,N1=true,N3=true,N4=true,N6=true,N7=true}
    local range_index,orientation,database,fn,manual,tdc,bgd,refel,elevation
    local cx,cz,last_up=0,0,0
    local view_x,view_z=0,0   -- world point under the screen centre (the manual-mode cursor)
    local ux,uz,upd_cursor=0,0,false -- map UPDT cursor: free in auto mode, in world metres
    local lock=get_param_handle("F117_IRADS_LOCK_VALID")
    local tx,tz=get_param_handle("F117_IRADS_LOCK_X"),get_param_handle("F117_IRADS_LOCK_Z")
    local terrain
    local ok,value=pcall(require,"terrain")
    if ok and type(value)=="table" then terrain=value end
    -- Clip route segments to the map window, rather than dropping a crossing
    -- leg when both of its endpoints are outside the current scale.
    local function clip(ax,ay,bx,by)
        local dx,dy=bx-ax,by-ay
        local lo,hi=0,1
        local hw,hh=window.half_width,window.half_height
        local p,q={-dx,dx,-dy,dy},{ax+hw,hw-ax,ay+hh,hh-ay}
        for i=1,4 do
            if math.abs(p[i])<1e-12 then if q[i]<0 then return end
            else
                local r=q[i]/p[i]
                if p[i]<0 then lo=math.max(lo,r) else hi=math.min(hi,r) end
                if lo>hi then return end
            end
        end
        return ax+lo*dx,ay+lo*dy,ax+hi*dx,ay+hi*dy
    end
    -- The selected TO point: a route point or a stored mark.
    local function active_point()
        local route=navigation and navigation.route() or plan.route or {}
        if navigation and navigation.active_point then return navigation.active_point() end
        return navigation and route[navigation.active()] or route[1]
    end
    local function update()
        local range=ranges[range_index]
        set("RANGE",range);set("RANGE_TEXT",string.format("%d NM",range))
        set("ORIENTATION_TEXT",modes[orientation]);set("DATABASE_TEXT",database==1 and "DMAP" or "PMAP")
        set("FUNCTION",fn);set("FUNCTION_TEXT",fn==1 and "FNC1" or "FUNC");set("MANUAL",manual);set("LOOK",manual==1 and 1 or 0)
        set("SCROLL",manual==2 and 1 or 0);set("TDC_TEXT","TDC"..tdc)
        set("BGD_TEXT","BGD "..bgd);set("REFEL_TEXT",refel==1 and "REFEL" or "ABS EL")
        local heading=sensor.getHeading and sensor.getHeading()
        local heading_valid=finite(heading)
        heading=heading_valid and -heading or 0
        set("HDG_TEXT",heading_valid and string.format("HDG %03.0f T",math.floor(math.deg(heading)%360+.5)%360) or "HDG ---")
        local vn,vu,ve
        if sensor.getSelfVelocity then vn,vu,ve=sensor.getSelfVelocity() end
        local velocity_valid=finite(vn) and finite(ve)
        local speed=velocity_valid and math.sqrt(vn*vn+ve*ve) or 0
        local track=velocity_valid and speed>5 and (math.atan2 or math.atan)(ve,vn) or heading
        set("CRS_TEXT",velocity_valid and speed>5 and string.format("CRS %03.0f",math.floor(math.deg(track)%360+.5)%360) or "CRS ---")
        set("GS_TEXT",velocity_valid and string.format("GS %03.0f",speed*1.94384449) or "GS ---")
        local up=(orientation==2 or orientation==4) and track or 0
        last_up=up
        local own_y=orientation>=3 and -.0265 or 0
        set("OWN_Y",own_y);set("OWN_ROT",up-heading);set("NORTH_ROT",up)
        local x,y,z
        if sensor.getSelfCoordinates then x,y,z=sensor.getSelfCoordinates() end
        local position_valid=finite(x) and finite(z)
        if position_valid and manual==0 then cx,cz=x,z end
        local scale=.106/(range*1852) -- full map height; exact Harris scale semantics unverified
        -- One view contract drives the future background and all Lua overlays.
        -- View centre is the world point at screen (0,0), including decentering.
        local view_valid=position_valid and heading_valid
        set("VIEW_VALID",view_valid and 1 or 0)
        view_x,view_z=cx-own_y/scale*math.cos(up),cz-own_y/scale*math.sin(up)
        set("VIEW_CENTER_X",view_valid and view_x or 0)
        set("VIEW_CENTER_Z",view_valid and view_z or 0)
        set("VIEW_UP_RAD",up);set("VIEW_SCALE",scale)
        set("VIEW_WIDTH_M",2*window.half_width/scale);set("VIEW_HEIGHT_M",2*window.half_height/scale)
        set("DATABASE",database);set("BACKGROUND_DECLUTTER",bgd)
        set("REFERENCE_ELEVATION",refel);set("ELEVATION_FT",elevation)
        chart_backend.update()
        set("SOURCE_VISIBLE",source_configured and view_valid and h("SOURCE_READY"):get()>.5 and 1 or 0)
        local function project(nx,ez)
            local north,east=nx-cx,ez-cz
            return (east*math.cos(up)-north*math.sin(up))*scale,
                (north*math.cos(up)+east*math.sin(up))*scale+own_y
        end
        local function inside(px,py)
            return math.abs(px)<window.half_width-.003 and math.abs(py)<window.half_height-.003
        end
        local ox,oy=0,own_y
        if position_valid then ox,oy=project(x,z) end
        set("OWN_X",ox);set("OWN_Y",oy)
        set("VALID",heading_valid and position_valid and inside(ox,oy) and 1 or 0)
        local coords="POSITION UNAVAILABLE"
        if position_valid and terrain and type(terrain.convertMetersToLatLon)=="function" then
            local good,lat,lon=pcall(terrain.convertMetersToLatLon,x,z)
            if good and finite(lat) and finite(lon) and math.abs(lat)<=90 and math.abs(lon)<=180 then
                coords=string.format("%s %06.3f  %s %07.3f",lat<0 and "S" or "N",math.abs(lat),lon<0 and "W" or "E",math.abs(lon))
            end
        end
        set("POSITION_TEXT",coords)
        -- Cursor: at the screen centre in manual mode, or free (UPDT) in auto mode.
        if upd_cursor then
            local px,py=project(ux,uz)
            set("CURSOR_X",px);set("CURSOR_Y",py);set("CURSOR_VISIBLE",position_valid and inside(px,py) and 1 or 0)
        else
            set("CURSOR_X",0);set("CURSOR_Y",0);set("CURSOR_VISIBLE",manual~=0 and 1 or 0)
        end
        set("TARGET_VISIBLE",0)
        local target_x,target_z=tx:get(),tz:get()
        if position_valid and lock:get()>.5 and finite(target_x) and finite(target_z) then
            -- The lock point is true world data; the map is in the INS frame, where it reads true + bias.
            if sensor.getInsBias then
                local bn,be=sensor.getInsBias()
                if finite(bn) and finite(be) then target_x,target_z=target_x+bn,target_z+be end
            end
            local px,py=project(target_x,target_z)
            if inside(px,py) then set("TARGET_X",px);set("TARGET_Y",py);set("TARGET_VISIBLE",1) end
        end
        local route=navigation and navigation.route() or plan.route or {}
        -- Steering leg from ownship to the active waypoint, as in the track-up video frames.
        set("STEER_VISIBLE",0)
        local steer=navigation and active_point()
        if position_valid and tdc<2 and type(steer)=="table" and finite(steer.x) and finite(steer.z) then
            local px,py=project(steer.x,steer.z)
            local ax,ay,bx,by=clip(ox,oy,px,py)
            if ax then
                set("STEER_X",ax);set("STEER_Y",ay);set("STEER_BX",bx);set("STEER_BY",by)
                set("STEER_VISIBLE",1)
            end
        end
        local previous
        for i=1,64 do
            local prefix="WP_"..i.."_"
            local point=route[i]
            set(prefix.."VISIBLE",0);set("LEG_"..i.."_VISIBLE",0)
            if position_valid and type(point)=="table" and finite(point.x) and finite(point.z) then
                local px,py=project(point.x,point.z)
                if tdc<2 and inside(px,py) then
                    set(prefix.."X",px);set(prefix.."Y",py);set(prefix.."KIND",kinds[point.kind] or 1)
                    set_label(prefix,point.label or i);set(prefix.."VISIBLE",1)
                end
                if previous and tdc<2 then
                    local ax,ay,bx,by=clip(previous[1],previous[2],px,py)
                    if ax then
                        local dx,dy=bx-ax,by-ay
                        set("LEG_"..i.."_X",ax);set("LEG_"..i.."_Y",ay)
                        set("LEG_"..i.."_BX",bx);set("LEG_"..i.."_BY",by)
                        set("LEG_"..i.."_VISIBLE",1)
                    end
                end
                previous={px,py}
            else previous=nil end -- never bridge invalid/missing route records
        end
        -- Stored MARK points (INS frame), drawn like waypoints.
        local marks=navigation and navigation.marks and navigation.marks() or {}
        for i=1,5 do
            local point=marks[i];local prefix="MARK_"..i.."_"
            set(prefix.."VISIBLE",0)
            if position_valid and tdc<2 and type(point)=="table" and finite(point.x) and finite(point.z) then
                local px,py=project(point.x,point.z)
                if inside(px,py) then
                    set(prefix.."X",px);set(prefix.."Y",py);set_label(prefix,point.label);set(prefix.."VISIBLE",1)
                end
            end
        end
        for i=1,32 do
            local point=(plan.threats or {})[i];local prefix="THREAT_"..i.."_"
            set(prefix.."VISIBLE",0)
            if position_valid and tdc==0 and type(point)=="table" and finite(point.x) and finite(point.z) and codes[point.code] then
                local px,py=project(point.x,point.z)
                if inside(px,py) then
                    set(prefix.."X",px);set(prefix.."Y",py);set_label(prefix,point.code);set(prefix.."VISIBLE",1)
                end
            end
        end
    end
    -- The selected destination: LOOK and SCROLL start there and SCAN RETURN brings the cursor back to it.
    local function dp_position()
        local point=active_point()
        if type(point)=="table" and finite(point.x) and finite(point.z) then return point.x,point.z end
    end
    local function return_to_dp()
        if manual==0 then return end
        local x,z=dp_position()
        if x then cx,cz=x,z end
    end
    -- Held TDC deflection while the Designate Select switch is on MAP. dx, dy are -1..1 screen axes.
    local function slew(dx,dy,dt)
        if (manual==0 and not upd_cursor) or not finite(dx) or not finite(dy) or not finite(dt) then return end
        local rate=ranges[range_index]*1852*.25*dt -- a quarter of the range per second at full deflection
        local east,north=dx*rate,dy*rate
        local dn=north*math.cos(last_up)-east*math.sin(last_up)
        local de=north*math.sin(last_up)+east*math.cos(last_up)
        if upd_cursor then ux,uz=ux+dn,uz+de else cx,cz=cx+dn,cz+de end
    end
    -- Map UPDT cursor (sensor update from the map). Starts at (x, z) and is slewed by the TDC.
    local function set_update_cursor(active,x,z)
        upd_cursor=active and true or false
        if upd_cursor and finite(x) and finite(z) then ux,uz=x,z end
    end
    -- World position of the cursor: the UPDT cursor, or the view centre in manual mode; nil in plain auto mode.
    local function pick()
        if upd_cursor then return ux,uz end
        if manual~=0 then return view_x,view_z end
    end
    local function initialize()
        range_index,orientation,database,fn,manual,tdc,bgd,refel,elevation=2,1,1,0,0,0,0,1,3000
        set("SOURCE_READY",0) -- producer owns subsequent readiness updates
        for i=1,64 do set_label("WP_"..i.."_","") end
        for i=1,32 do set_label("THREAT_"..i.."_","") end
        for i=1,5 do set_label("MARK_"..i.."_","") end
        chart_backend.initialize()
        cx,cz=0,0;update()
    end
    local function set_command(command,value)
        local action
        for name,id in pairs(map_commands) do if command==id then action=name;break end end
        if not action then return false end
        if value and value>0 then
            if action=="RANGE_UP" then range_index=math.min(#ranges,range_index+1)
            elseif action=="RANGE_DOWN" then range_index=math.max(1,range_index-1)
            elseif action=="ORIENTATION" then orientation=orientation%#modes+1
            elseif action=="DATABASE" then database=3-database
            elseif action=="FUNCTION" then fn=1-fn
            elseif action=="LOOK" or action=="SCROLL" then
                local mode=action=="LOOK" and 1 or 2
                if manual==mode then manual=0
                elseif manual_allowed() then
                    manual=mode
                    local x,z=dp_position()
                    if x then cx,cz=x,z end
                    if mode==1 then orientation=1 end -- LOOK is North-up, centred
                end
            elseif action=="AUTO" then manual=0
            elseif action=="TACTICAL_DECLUTTER" then tdc=(tdc+1)%3
            elseif action=="BACKGROUND_DECLUTTER" then bgd=(bgd+1)%4
            elseif action=="REFERENCE_ELEVATION" then refel=1-refel
            elseif action=="ELEVATION_UP" then elevation=math.min(60000,elevation+1000)
            elseif action=="ELEVATION_DOWN" then elevation=math.max(0,elevation-1000)
            elseif manual~=0 then
                local step=ranges[range_index]*1852*.05
                local east=(action=="PAN_RIGHT" and step or action=="PAN_LEFT" and -step or 0)
                local north=(action=="PAN_UP" and step or action=="PAN_DOWN" and -step or 0)
                cx=cx+north*math.cos(last_up)-east*math.sin(last_up)
                cz=cz+north*math.sin(last_up)+east*math.cos(last_up)
            end
            update()
        end
        return true
    end
    return {initialize=initialize,update=update,set_command=set_command,slew=slew,return_to_dp=return_to_dp,
        set_update_cursor=set_update_cursor,pick=pick,manual=function()return manual end}
end
return M
