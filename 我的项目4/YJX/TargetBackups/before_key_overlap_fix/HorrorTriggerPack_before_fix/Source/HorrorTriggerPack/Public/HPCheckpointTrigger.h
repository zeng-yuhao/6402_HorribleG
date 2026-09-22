#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HPCheckpointTrigger.generated.h"

class APlayerController;
class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FHPCheckpointActivated, APlayerController*, PlayerController, FTransform, SavedTransform);

/** Empty box actor: stores a respawn position on the team's PlayerController, without destroying itself. */
UCLASS(Blueprintable)
class HORRORTRIGGERPACK_API AHPCheckpointTrigger : public AActor
{
    GENERATED_BODY()

public:
    AHPCheckpointTrigger();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Checkpoint")
    TObjectPtr<UBoxComponent> CheckpointZone;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Checkpoint",
        meta=(DisplayName="Only First Activation / 仅首次激活"))
    bool bOnlyFirstActivation = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Checkpoint",
        meta=(Units="cm", DisplayName="Spawn Height Offset / 重生高度偏移"))
    float SpawnHeightOffset = 100.0f;

    UPROPERTY(BlueprintAssignable, Category="Checkpoint",
        meta=(DisplayName="On Checkpoint Activated / 检查点激活后"))
    FHPCheckpointActivated OnCheckpointActivated;

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

    bool bActivated = false;
};
