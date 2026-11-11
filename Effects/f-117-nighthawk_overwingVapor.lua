Presets = 
{
    F_117_NightHawk =
    {
        {
            Type = "overwingVapor",
            ShadingFX = "ParticleSystem2/overwingVapor.fx",
            UpdateFX  = "ParticleSystem2/overwingVaporComp.fx",
            Technique = "techOverwingVapor",

            Texture = "overwingVapor.dds",
            TextureDetailNoise = "puffNoise.png",
            LODdistance = 2000,

            SpawnLocationsFile = "f-117-nighthawk_overwingVapor.owv",

            ParticlesCount = 400,
            ParticleSize = 1.5,
            ScaleOverAgeFactor = 1.8, -- scale = ParticleSize * (1 + (normalized age) * ScaleOverAgeFactor)
            
            VaporLengthMax = 3.0, -- meters
            
            AlbedoSRGB = 0.86,
            
            OpacityMax = 0.25,
            -- Vapour power -> opacity. For this aircraft the power stays near 0.05 below
            -- about 7 deg AoA and rises to about 0.12 at 12 deg, so the cloud starts near
            -- 8 deg and is full by 11.5 deg. The EFM fades the leading-edge vortices out
            -- over the same range, as the cloud replaces them.
            OpacityOverPower = {
                {0.0,   0.0},
                {0.07,  0.0},
                {0.09,  0.25},
                {0.5,   0.65},
                {1.0,   1.0},
            },
        }
    }
}