#include "HPCheckpointTrigger.h"

#include "HPRespawnBridgeComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

AHPCheckpointTrigger::AHPCheckpointTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    CheckpointZone = CreateDefaultSubobject<UBoxComponent>(TEXT("CheckpointZone"));
    SetRootComponent(CheckpointZone);
    CheckpointZone->SetBoxExtent(FVector(160.0, 160.0, 110.0));
    CheckpointZone->SetGenerateOverlapEvents(true);
    CheckpointZone->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    CheckpointZone->SetCollisionObjectType(ECC_WorldDynamic);
    CheckpointZone->SetCollisionResponseToAllChannels(ECR_Ignore);
    CheckpointZone->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
}

void AHPCheckpointTrigger::BeginPlay()
{
    Super::BeginPlay();
    CheckpointZone->OnComponentBeginOverlap.AddDynamic(this, &AHPCheckpointTrigger::HandleBeginOverlap);
}

void AHPCheckpointTrigger::HandleBeginOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    if (bOnlyFirstActivation && bActivated)
    {
        return;
    }

    APawn* Pawn = Cast<APawn>(OtherActor);
    APlayerController* Controller = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
    UHPRespawnBridgeComponent* Bridge = Controller
        ? Controller->FindComponentByClass<UHPRespawnBridgeComponent>()
        : nullptr;
    if (!Bridge)
    {
        return;
    }

    const FVector Location = GetActorLocation() + FVector(0.0f, 0.0f, SpawnHeightOffset);
    const FTransform SavedTransform(GetActorRotation(), Location, FVector::OneVector);
    if (Bridge->SaveCheckpoint(SavedTransform))
    {
        bActivated = true;
        OnCheckpointActivated.Broadcast(Controller, SavedTransform);
    }
}
