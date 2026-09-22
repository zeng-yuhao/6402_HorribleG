#include "HPDeathCutsceneTrigger.h"
#include "HPRespawnBridgeComponent.h"

#include "Components/BoxComponent.h"
#include "Components/ActorComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
#include "TimerManager.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

AHPDeathCutsceneTrigger::AHPDeathCutsceneTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    DeathZone = CreateDefaultSubobject<UBoxComponent>(TEXT("DeathZone"));
    SetRootComponent(DeathZone);
    DeathZone->SetBoxExtent(FVector(150.0, 150.0, 100.0));
    DeathZone->SetGenerateOverlapEvents(true);
    DeathZone->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    DeathZone->SetCollisionObjectType(ECC_WorldDynamic);
    DeathZone->SetCollisionResponseToAllChannels(ECR_Ignore);
    DeathZone->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
}

void AHPDeathCutsceneTrigger::BeginPlay()
{
    Super::BeginPlay();
    DeathZone->OnComponentBeginOverlap.AddDynamic(this, &AHPDeathCutsceneTrigger::HandleBeginOverlap);
}

void AHPDeathCutsceneTrigger::HandleBeginOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    if (bTriggered)
    {
        return;
    }

    const APawn* OverlappingPawn = Cast<APawn>(OtherActor);
    APlayerController* PlayerController = OverlappingPawn
        ? Cast<APlayerController>(OverlappingPawn->GetController())
        : nullptr;
    if (!PlayerController)
    {
        return;
    }

    bTriggered = true;
    CachedController = PlayerController;
    DeathZone->SetGenerateOverlapEvents(false);
    RequestPlayerState(CutsceneStateIndex);

    if (DeathSequenceActor)
    {
        if (ULevelSequencePlayer* SequencePlayer = DeathSequenceActor->GetSequencePlayer())
        {
            SequencePlayer->OnFinished.RemoveAll(this);
            SequencePlayer->OnFinished.AddDynamic(this, &AHPDeathCutsceneTrigger::HandleSequenceFinished);
            SequencePlayer->Play();
            return;
        }
    }

    GetWorldTimerManager().SetTimer(
        FinishTimer,
        this,
        &AHPDeathCutsceneTrigger::FinishDeathFlow,
        FMath::Max(0.01f, FallbackDuration),
        false);
}

void AHPDeathCutsceneTrigger::HandleSequenceFinished()
{
    if (DeathSequenceActor)
    {
        if (ULevelSequencePlayer* SequencePlayer = DeathSequenceActor->GetSequencePlayer())
        {
            SequencePlayer->OnFinished.RemoveAll(this);
        }
    }
    FinishDeathFlow();
}

void AHPDeathCutsceneTrigger::FinishDeathFlow()
{
    RequestPlayerState(DeadStateIndex);

    if (!InvokeRespawnEvent())
    {
        UE_LOG(LogTemp, Error,
            TEXT("%s could not complete respawn through the PlayerController event or YJX respawn bridge."),
            *GetName());
    }

    GetWorldTimerManager().SetTimer(
        RearmTimer,
        this,
        &AHPDeathCutsceneTrigger::RearmTrigger,
        FMath::Max(0.01f, RearmDelay),
        false);
}

void AHPDeathCutsceneTrigger::RearmTrigger()
{
    CachedController = nullptr;
    bTriggered = false;
    DeathZone->SetGenerateOverlapEvents(true);
}

UObject* AHPDeathCutsceneTrigger::FindPlayerStateManager() const
{
    if (!CachedController)
    {
        return nullptr;
    }

    TInlineComponentArray<UActorComponent*> Components(CachedController);
    for (UActorComponent* Component : Components)
    {
        if (Component && Component->GetClass()->GetName().Contains(TEXT("BPC_PlayerStateManager")))
        {
            return Component;
        }
    }
    return nullptr;
}

void AHPDeathCutsceneTrigger::RequestPlayerState(uint8 StateIndex) const
{
    UObject* StateManager = FindPlayerStateManager();
    if (!StateManager)
    {
        UE_LOG(LogTemp, Error, TEXT("%s could not find BPC_PlayerStateManager on PlayerController."), *GetName());
        return;
    }

    UFunction* Function = StateManager->FindFunction(FName(TEXT("Request State Change")));
    if (!Function)
    {
        Function = StateManager->FindFunction(FName(TEXT("RequestStateChange")));
    }
    if (!Function)
    {
        UE_LOG(LogTemp, Error, TEXT("%s could not find Request State Change on BPC_PlayerStateManager."), *GetName());
        return;
    }

    FStructOnScope Parameters(Function);
    uint8* Memory = Parameters.GetStructMemory();
    for (TFieldIterator<FProperty> It(Function); It; ++It)
    {
        FProperty* Property = *It;
        if (!Property->HasAnyPropertyFlags(CPF_Parm) || Property->HasAnyPropertyFlags(CPF_ReturnParm))
        {
            continue;
        }

        if (Property->GetFName() == FName(TEXT("NewState")))
        {
            void* ValueAddress = Property->ContainerPtrToValuePtr<void>(Memory);
            if (FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
            {
                EnumProperty->GetUnderlyingProperty()->SetIntPropertyValue(ValueAddress, static_cast<uint64>(StateIndex));
            }
            else if (FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
            {
                ByteProperty->SetPropertyValue(ValueAddress, StateIndex);
            }
            break;
        }
    }
    StateManager->ProcessEvent(Function, Memory);
}

bool AHPDeathCutsceneTrigger::InvokeRespawnEvent() const
{
    if (!CachedController)
    {
        return false;
    }

    for (TFieldIterator<UFunction> It(CachedController->GetClass(), EFieldIteratorFlags::IncludeSuper); It; ++It)
    {
        UFunction* Function = *It;
        FString CompactName = Function->GetName();
        CompactName.ReplaceInline(TEXT(" "), TEXT(""));
        if (!CompactName.StartsWith(TEXT("RequestRespawn"), ESearchCase::IgnoreCase))
        {
            continue;
        }

        FStructOnScope Parameters(Function);
        CachedController->ProcessEvent(Function, Parameters.GetStructMemory());
        return true;
    }

    // The merged project keeps the team's PlayerController, which has no Blueprint RequestRespawn event.
    if (UHPRespawnBridgeComponent* Bridge = CachedController->FindComponentByClass<UHPRespawnBridgeComponent>())
    {
        return Bridge->RequestRespawn();
    }
    return false;
}
