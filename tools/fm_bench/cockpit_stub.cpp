// Stands in for the cockpit parameter API so the EFM can run outside DCS.
// The EFM looks this API up in CockpitBase.dll, so the bench builds this file under that name
// and loads it first. It keeps parameters in memory and has no other cockpit behaviour.
#include <cstring>
#include <map>
#include <string>

namespace
{
    struct Param
    {
        double number = 0.0;
        std::string text;
    };

    std::map<std::string, Param> g_params; // Map nodes don't move, so handles stay valid.
}

extern "C"
{
    __declspec(dllexport) void* ed_cockpit_get_parameter_handle(const char* name)
    {
        return &g_params[name];
    }

    __declspec(dllexport) void ed_cockpit_update_parameter_with_string(void* handle, const char* value)
    {
        static_cast<Param*>(handle)->text = value;
    }

    __declspec(dllexport) void ed_cockpit_update_parameter_with_number(void* handle, double value)
    {
        static_cast<Param*>(handle)->number = value;
    }

    __declspec(dllexport) bool ed_cockpit_parameter_value_to_number(const void* handle, double& result, bool)
    {
        result = static_cast<const Param*>(handle)->number;
        return true;
    }

    __declspec(dllexport) bool ed_cockpit_parameter_value_to_string(const void* handle, char* buffer, unsigned size)
    {
        strncpy_s(buffer, size, static_cast<const Param*>(handle)->text.c_str(), _TRUNCATE);
        return true;
    }
}
