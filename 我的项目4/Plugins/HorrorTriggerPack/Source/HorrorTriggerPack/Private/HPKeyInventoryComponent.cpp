#include "HPKeyInventoryComponent.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/SphereComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"

UHPKeyInventoryComponent::UHPKeyInventoryComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    TrackedKeyClassPath = FSoftClassPath(TEXT("/Game/YYN/Blueprint_YYN/BP_Key.BP_Key_C"));
}

void UHPKeyInventoryComponent::BeginPlay()
{
    Super::BeginPlay();
    CachedController = Cast<APlayerController>(GetOwner());
    if (!CachedController || !GetWorld())
    {
        UE_LOG(LogTemp, Error, TEXT("HPKeyInventoryComponent must be on a PlayerController."));
        return;
    }

    WatchExistingKeys();
    ActorSpawnedHandle = GetWorld()->AddOnActorSpawnedHandler(
        FOnActorSpawned::FDelegate::CreateUObject(this, &UHPKeyInventoryComponent::HandleActorSpawned));
    if (WatchRefreshInterval > 0.0f)
    {
        GetWorld()->GetTimerManager().SetTimer(
            WatchTimer, this, &UHPKeyInventoryComponent::WatchExistingKeys, WatchRefreshInterval, true);
    }
    UE_LOG(LogTemp, Display, TEXT("YJX key inventory active: %s; watched=%d"),
        *TrackedKeyClassPath.ToString(), ObservedKeyActors.Num());
}

void UHPKeyInventoryComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (GetWorld())
    {
        GetWorld()->GetTimerManager().ClearTimer(WatchTimer);
    }
    if (GetWorld() && ActorSpawnedHandle.IsValid())
    {
        GetWorld()->RemoveOnActorSpawnedHandler(ActorSpawnedHandle);
    }
    CachedController = nullptr;
    ObservedKeyActors.Empty();
    Super::EndPlay(EndPlayReason);
}

void UHPKeyInventoryComponent::WatchExistingKeys()
{
    if (!GetWorld() || TrackedKeyClassPath.IsNull())
    {
        return;
    }
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        WatchActor(*It);
    }
}

void UHPKeyInventoryComponent::WatchActor(AActor* Actor)
{
    if (!Actor || TrackedKeyClassPath.IsNull())
    {
        return;
    }
    if (Actor->GetClass()->GetPathName() == TrackedKeyClassPath.ToString())
    {
        const TWeakObjectPtr<AActor> WeakActor(Actor);
        if (ObservedKeyActors.Contains(WeakActor))
        {
            return;
        }
        ObservedKeyActors.Add(WeakActor);
        Actor->OnDestroyed.AddUniqueDynamic(this, &UHPKeyInventoryComponent::HandleTrackedKeyDestroyed);
        if (USphereComponent* Sphere = Actor->FindComponentByClass<USphereComponent>())
        {
            Sphere->OnComponentBeginOverlap.AddUniqueDynamic(this, &UHPKeyInventoryComponent::HandleTrackedKeyOverlap);
            if (CachedController && CachedController->GetPawn() && Sphere->IsOverlappingActor(CachedController->GetPawn()))
            {
                GrantKey(KeyId);
            }
        }
        UE_LOG(LogTemp, Display, TEXT("YJX watching BP_Key actor: %s"), *Actor->GetName());
    }
}

void UHPKeyInventoryComponent::HandleActorSpawned(AActor* Actor)
{
    WatchActor(Actor);
}

void UHPKeyInventoryComponent::HandleTrackedKeyOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    if (CachedController && OtherActor && OtherActor == CachedController->GetPawn())
    {
        GrantKey(KeyId);
    }
}

void UHPKeyInventoryComponent::HandleTrackedKeyDestroyed(AActor* DestroyedActor)
{
    // BP_Key's original overlap event destroys the world actor on pickup. Its class is checked in WatchActor.
    APawn* Pawn = CachedController ? CachedController->GetPawn() : nullptr;
    if (!Pawn || !DestroyedActor || PickupMaxDistance <= 0.0f)
    {
        return;
    }
    if (FVector::Dist(Pawn->GetActorLocation(), DestroyedActor->GetActorLocation()) <= PickupMaxDistance)
    {
        GrantKey(KeyId);
    }
}

bool UHPKeyInventoryComponent::HasKey(FName RequestedKeyId) const
{
    return bHasKey && RequestedKeyId == KeyId;
}

void UHPKeyInventoryComponent::GrantKey(FName GrantedKeyId)
{
    if (GrantedKeyId != KeyId || bHasKey)
    {
        return;
    }
    bHasKey = true;
    OnKeyChanged.Broadcast(KeyId, true);
    UE_LOG(LogTemp, Display, TEXT("YJX key acquired: %s"), *KeyId.ToString());
}

bool UHPKeyInventoryComponent::ConsumeKey(FName RequestedKeyId)
{
    if (!HasKey(RequestedKeyId))
    {
        return false;
    }
    bHasKey = false;
    OnKeyChanged.Broadcast(KeyId, false);
    UE_LOG(LogTemp, Display, TEXT("YJX key consumed: %s"), *KeyId.ToString());
    return true;
}
