#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UObject/SoftObjectPath.h"
#include "HPKeyInventoryComponent.generated.h"

class AActor;
class APlayerController;
class UPrimitiveComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FHPKeyChangedSignature, FName, KeyId, bool, bHeld);

/** Records the existing BP_Key pickup on the PlayerController without modifying the team's key Blueprint. */
UCLASS(ClassGroup=(YJX), BlueprintType, Blueprintable, meta=(BlueprintSpawnableComponent))
class HORRORTRIGGERPACK_API UHPKeyInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UHPKeyInventoryComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="YJX|Key",
        meta=(DisplayName="Tracked Key Class / 追踪的钥匙类"))
    FSoftClassPath TrackedKeyClassPath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="YJX|Key",
        meta=(DisplayName="Key ID / 钥匙ID"))
    FName KeyId = TEXT("YYN_Key");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="YJX|Key",
        meta=(ClampMin="0.0", Units="cm", DisplayName="Pickup Max Distance / 拾取最大距离"))
    float PickupMaxDistance = 250.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="YJX|Key",
        meta=(ClampMin="0.0", Units="s", DisplayName="Watch Refresh Interval / 钥匙追踪刷新间隔"))
    float WatchRefreshInterval = 0.5f;

    UPROPERTY(BlueprintAssignable, Category="YJX|Key",
        meta=(DisplayName="On Key Changed / 钥匙状态改变"))
    FHPKeyChangedSignature OnKeyChanged;

    UFUNCTION(BlueprintPure, Category="YJX|Key", meta=(DisplayName="Has Key / 持有钥匙"))
    bool HasKey(FName RequestedKeyId) const;

    UFUNCTION(BlueprintCallable, Category="YJX|Key", meta=(DisplayName="Grant Key / 给予钥匙"))
    void GrantKey(FName GrantedKeyId);

    UFUNCTION(BlueprintCallable, Category="YJX|Key", meta=(DisplayName="Consume Key / 消耗钥匙"))
    bool ConsumeKey(FName RequestedKeyId);

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    void WatchExistingKeys();
    void WatchActor(AActor* Actor);
    void HandleActorSpawned(AActor* Actor);

    UFUNCTION()
    void HandleTrackedKeyOverlap(
        UPrimitiveComponent* OverlappedComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComp,
        int32 OtherBodyIndex,
        bool bFromSweep,
        const FHitResult& SweepResult);

    UFUNCTION()
    void HandleTrackedKeyDestroyed(AActor* DestroyedActor);

    UPROPERTY(Transient)
    TObjectPtr<APlayerController> CachedController;

    FDelegateHandle ActorSpawnedHandle;
    FTimerHandle WatchTimer;
    TSet<TWeakObjectPtr<AActor>> ObservedKeyActors;
    bool bHasKey = false;
};
