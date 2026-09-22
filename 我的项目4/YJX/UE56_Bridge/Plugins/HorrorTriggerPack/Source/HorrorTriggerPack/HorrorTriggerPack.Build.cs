using UnrealBuildTool;

public class HorrorTriggerPack : ModuleRules
{
    public HorrorTriggerPack(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "LevelSequence",
            "MovieScene",
            "UMG",
            "Slate",
            "SlateCore"
        });
    }
}
