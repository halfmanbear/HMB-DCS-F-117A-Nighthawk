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
            LODdistance = 1500,

            SpawnLocationsFile = "f-117-nighthawk_overwingVapor.owv",

            ParticlesCount = 300,
            ParticleSize = 4.5,
            ScaleOverAgeFactor = 1.8, -- scale = ParticleSize * (1 + (normalized age) * ScaleOverAgeFactor)

            VaporLengthMax = 6.0, -- meters; photos show the cloud from the canopy back over the aft body

            AlbedoSRGB = 0.80,

            OpacityMax = 0.55,
            -- Vapour power -> opacity. Photos show this cloud only near the AoA limit
            -- (12.6 deg below M0.53, TO 1F-117A-1 Figure 5-7), never together with the
            -- leading-edge vortex pair, which the EFM fades out between 10 and 11 deg.
            -- DCS computes the power from both AoA and speed. Measured in steady turns at
            -- 600 m (tools/missions/vortex_shots.py --owv-probe), power first passes:
            --   0.15  at  8 deg at 170-200 m/s, 10 deg at 132 m/s
            --   0.25  by  9 deg at 200 m/s,     11 deg at 132 m/s
            --   0.40  at 10 deg at 200 m/s,     12.6 deg at 132 m/s
            --   0.60  at 11.5 deg at 200 m/s,   not reached at 132 m/s
            --   0.80  only at full aft stick (12.2 deg, 6.2 g) at 200 m/s
            -- So at about 380 KCAS the cloud starts at 11.5 deg and is full near the limit;
            -- slower passes (about 250 KCAS) show the vortices only.
            OpacityOverPower = {
                {0.0,   0.0},
                {0.6,   0.0},
                {0.63,  0.6},
                {0.75,  1.0},
                {1.0,   1.0},
            },
        }
    }
}