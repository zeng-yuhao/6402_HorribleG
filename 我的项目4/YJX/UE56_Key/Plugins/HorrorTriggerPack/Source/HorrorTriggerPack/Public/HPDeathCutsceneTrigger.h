#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HPDeathCutsceneTrigger.generated.h"

class ALevelSequenceActor;
class APlayerController;
class UBoxComponent;

/**
 * Empty trigger actor that enters Cutscene state, plays a Level Sequence,
 * enters Dead state, and finally asks the project's PlayerController to respawn.
 */
UCLASS(Blueprintable)
class HORRORTRIGGERPACK_API AHPDeathCutsceneTrigger : public AActor
{
    GENERATED_BODY()

public:
    AHPDeathCutsceneTrigger();

    /** Box used only for player overlap queries. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Death Trigger")
    TObjectPtr<UBoxComponent> DeathZone;

    /** Level Sequence Actor to play. Leave empty to use the fallback delay. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Death Trigger|Cutscene",
        meta=(DisplayName="Death Sequence Actor / 死亡过场序列Actor"))
    TObjectPtr<ALevelSequenceActor> DeathSequenceActor;

    /** Used only when no valid Level Sequence Actor is assigned. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Death Trigger|Cutscene",
        meta=(ClampMin="0.0", Units="s", DisplayName="Fallback Duration / 备用时长"))
    float FallbackDuration = 3.0f;

    /** Delay before this trigger can be activated again after requesting respawn. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Death Trigger",
        meta=(ClampMin="0.0", Units="s", DisplayName="Rearm Delay / 重新启用延迟"))
    float RearmDelay = 0.5f;

    /** State enum index used by E_PlayerState: Cutscene is 3 in this project. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Death Trigger|Integration")
    uint8 CutsceneStateIndex = 3;

    /** State enum index used by E_PlayerState: Dead is 4 in this project. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Death Trigger|Integration")
    uint8 DeadStateIndex = 4;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void HandleBeginOverlap(
        UPrimitiveComponent* OverlappedComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComp,
        int32 OtherBodyIndex,
        bool bFromSweep,
        const FHitResult& SweepResult);

    UFUNCTION()
    void HandleSequenceFinished();

    void FinishDeathFlow();
    void RearmTrigger();
    UObject* FindPlayerStateManager() const;
    void RequestPlayerState(uint8 StateIndex) const;
    bool InvokeRespawnEvent() const;

    UPROPERTY(Transient)
    TObjectPtr<APlayerController> CachedController;

    FTimerHandle FinishTimer;
    FTimerHandle RearmTimer;
    bool bTriggered = false;
};
