#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "HPRespawnBridgeComponent.generated.h"

class APlayerController;
class APawn;

/** Keeps the team's PlayerController/GameMode/Pawn while connecting the imported state manager to respawn. */
UCLASS(ClassGroup=(YJX), Blueprintable, meta=(BlueprintSpawnableComponent))
class HORRORTRIGGERPACK_API UHPRespawnBridgeComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UHPRespawnBridgeComponent();

    UFUNCTION(BlueprintCallable, Category="YJX|Checkpoint",
        meta=(DisplayName="Save Checkpoint / 保存检查点"))
    bool SaveCheckpoint(const FTransform& NewCheckpointTransform);

    UFUNCTION(BlueprintPure, Category="YJX|Checkpoint",
        meta=(DisplayName="Has Checkpoint / 有有效检查点"))
    bool HasCheckpoint() const;

    UFUNCTION(BlueprintPure, Category="YJX|Checkpoint",
        meta=(DisplayName="Get Checkpoint Transform / 获取检查点变换"))
    FTransform GetCheckpointTransform() const;

    UFUNCTION(BlueprintCallable, Category="YJX|Respawn",
        meta=(DisplayName="Request Respawn / 请求重生"))
    bool RequestRespawn();

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UFUNCTION()
    void HandlePossessedPawnChanged(APawn* OldPawn, APawn* NewPawn);

    UObject* FindPlayerStateManager() const;
    void RequestNormalState() const;

    UPROPERTY(Transient)
    TObjectPtr<APlayerController> CachedController;

    FTransform LocalCheckpoint = FTransform::Identity;
    bool bHasLocalCheckpoint = false;
    bool bInitialPawnSeen = false;
};
