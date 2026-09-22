#include "HPKeyInventoryComponent.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

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

    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        WatchActor(*It);
    }
    ActorSpawnedHandle = GetWorld()->AddOnActorSpawnedHandler(
        FOnActorSpawned::FDelegate::CreateUObject(this, &UHPKeyInventoryComponent::HandleActorSpawned));
}

void UHPKeyInventoryComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (GetWorld() && ActorSpawnedHandle.IsValid())
    {
        GetWorld()->RemoveOnActorSpawnedHandler(ActorSpawnedHandle);
    }
    CachedController = nullptr;
    Super::EndPlay(EndPlayReason);
}

void UHPKeyInventoryComponent::WatchActor(AActor* Actor)
{
    if (!Actor || TrackedKeyClassPath.IsNull())
    {
        return;
    }
    if (Actor->GetClass()->GetPathName() == TrackedKeyClassPath.ToString())
    {
        Actor->OnDestroyed.AddUniqueDynamic(this, &UHPKeyInventoryComponent::HandleTrackedKeyDestroyed);
    }
}

void UHPKeyInventoryComponent::HandleActorSpawned(AActor* Actor)
{
    WatchActor(Actor);
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
