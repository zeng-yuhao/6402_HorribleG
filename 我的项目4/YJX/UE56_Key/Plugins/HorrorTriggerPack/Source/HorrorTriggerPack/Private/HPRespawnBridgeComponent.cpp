#include "HPRespawnBridgeComponent.h"

#include "Components/ActorComponent.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

namespace
{
UFunction* FindFunctionByCompactName(UObject* Object, const TCHAR* Name)
{
    if (!Object)
    {
        return nullptr;
    }
    for (TFieldIterator<UFunction> It(Object->GetClass(), EFieldIteratorFlags::IncludeSuper); It; ++It)
    {
        UFunction* Function = *It;
        FString CompactName = Function->GetName();
        CompactName.ReplaceInline(TEXT(" "), TEXT(""));
        if (CompactName.StartsWith(Name, ESearchCase::IgnoreCase))
        {
            return Function;
        }
    }
    return nullptr;
}

bool ReadBooleanReturn(UObject* Object, const TCHAR* Name)
{
    UFunction* Function = FindFunctionByCompactName(Object, Name);
    if (!Function)
    {
        return false;
    }
    FStructOnScope Params(Function);
    Object->ProcessEvent(Function, Params.GetStructMemory());
    for (TFieldIterator<FProperty> It(Function); It; ++It)
    {
        FProperty* Property = *It;
        if (Property->HasAnyPropertyFlags(CPF_ReturnParm))
        {
            if (const FBoolProperty* BoolProperty = CastField<FBoolProperty>(Property))
            {
                return BoolProperty->GetPropertyValue_InContainer(Params.GetStructMemory());
            }
        }
    }
    return false;
}

bool ReadTransformReturn(UObject* Object, const TCHAR* Name, FTransform& OutTransform)
{
    UFunction* Function = FindFunctionByCompactName(Object, Name);
    if (!Function)
    {
        return false;
    }
    FStructOnScope Params(Function);
    Object->ProcessEvent(Function, Params.GetStructMemory());
    for (TFieldIterator<FProperty> It(Function); It; ++It)
    {
        FProperty* Property = *It;
        if (Property->HasAnyPropertyFlags(CPF_ReturnParm))
        {
            if (const FStructProperty* StructProperty = CastField<FStructProperty>(Property))
            {
                if (StructProperty->Struct == TBaseStructure<FTransform>::Get())
                {
                    OutTransform = *StructProperty->ContainerPtrToValuePtr<FTransform>(Params.GetStructMemory());
                    return true;
                }
            }
        }
    }
    return false;
}
}

UHPRespawnBridgeComponent::UHPRespawnBridgeComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UHPRespawnBridgeComponent::BeginPlay()
{
    Super::BeginPlay();
    CachedController = Cast<APlayerController>(GetOwner());
    if (!CachedController)
    {
        UE_LOG(LogTemp, Error, TEXT("HPRespawnBridgeComponent must be on a PlayerController."));
        return;
    }
    CachedController->OnPossessedPawnChanged.AddDynamic(this, &UHPRespawnBridgeComponent::HandlePossessedPawnChanged);
    if (APawn* ExistingPawn = CachedController->GetPawn())
    {
        HandlePossessedPawnChanged(nullptr, ExistingPawn);
    }
}

void UHPRespawnBridgeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (CachedController)
    {
        CachedController->OnPossessedPawnChanged.RemoveDynamic(this, &UHPRespawnBridgeComponent::HandlePossessedPawnChanged);
    }
    CachedController = nullptr;
    Super::EndPlay(EndPlayReason);
}

void UHPRespawnBridgeComponent::HandlePossessedPawnChanged(APawn* OldPawn, APawn* NewPawn)
{
    if (!NewPawn || bInitialPawnSeen)
    {
        return;
    }
    bInitialPawnSeen = true;
    if (!HasCheckpoint())
    {
        SaveCheckpoint(NewPawn->GetActorTransform());
    }
}

UObject* UHPRespawnBridgeComponent::FindPlayerStateManager() const
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

bool UHPRespawnBridgeComponent::SaveCheckpoint(const FTransform& NewCheckpointTransform)
{
    LocalCheckpoint = NewCheckpointTransform;
    LocalCheckpoint.SetScale3D(FVector::OneVector);
    bHasLocalCheckpoint = true;

    UObject* Manager = FindPlayerStateManager();
    UFunction* Function = FindFunctionByCompactName(Manager, TEXT("SetCheckpoint"));
    if (!Function)
    {
        UE_LOG(LogTemp, Warning, TEXT("%s saved a local checkpoint but could not call BPC SetCheckpoint."), *GetName());
        return true;
    }

    FStructOnScope Params(Function);
    bool bWroteTransform = false;
    for (TFieldIterator<FProperty> It(Function); It; ++It)
    {
        FProperty* Property = *It;
        if (!Property->HasAnyPropertyFlags(CPF_Parm) || Property->HasAnyPropertyFlags(CPF_ReturnParm))
        {
            continue;
        }
        if (FStructProperty* StructProperty = CastField<FStructProperty>(Property))
        {
            if (StructProperty->Struct == TBaseStructure<FTransform>::Get())
            {
                StructProperty->CopyCompleteValue(
                    StructProperty->ContainerPtrToValuePtr<void>(Params.GetStructMemory()),
                    &LocalCheckpoint);
                bWroteTransform = true;
                break;
            }
        }
    }
    if (!bWroteTransform)
    {
        UE_LOG(LogTemp, Warning, TEXT("%s found BPC SetCheckpoint but no Transform input."), *GetName());
        return true;
    }
    Manager->ProcessEvent(Function, Params.GetStructMemory());
    return true;
}

bool UHPRespawnBridgeComponent::HasCheckpoint() const
{
    if (ReadBooleanReturn(FindPlayerStateManager(), TEXT("HasValidCheckpoint")))
    {
        return true;
    }
    return bHasLocalCheckpoint;
}

FTransform UHPRespawnBridgeComponent::GetCheckpointTransform() const
{
    UObject* Manager = FindPlayerStateManager();
    FTransform SavedTransform;
    if (ReadBooleanReturn(Manager, TEXT("HasValidCheckpoint"))
        && ReadTransformReturn(Manager, TEXT("GetCheckpointTransform"), SavedTransform))
    {
        SavedTransform.SetScale3D(FVector::OneVector);
        return SavedTransform;
    }
    return LocalCheckpoint;
}

void UHPRespawnBridgeComponent::RequestNormalState() const
{
    UObject* Manager = FindPlayerStateManager();
    UFunction* Function = FindFunctionByCompactName(Manager, TEXT("RequestStateChange"));
    if (!Function)
    {
        return;
    }
    FStructOnScope Params(Function);
    for (TFieldIterator<FProperty> It(Function); It; ++It)
    {
        FProperty* Property = *It;
        if (!Property->HasAnyPropertyFlags(CPF_Parm) || Property->HasAnyPropertyFlags(CPF_ReturnParm))
        {
            continue;
        }
        if (Property->GetFName() == FName(TEXT("NewState")))
        {
            void* Address = Property->ContainerPtrToValuePtr<void>(Params.GetStructMemory());
            if (FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
            {
                EnumProperty->GetUnderlyingProperty()->SetIntPropertyValue(Address, static_cast<uint64>(0));
            }
            else if (FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
            {
                ByteProperty->SetPropertyValue(Address, 0);
            }
            break;
        }
    }
    Manager->ProcessEvent(Function, Params.GetStructMemory());
}

bool UHPRespawnBridgeComponent::RequestRespawn()
{
    if (!CachedController || !GetWorld())
    {
        return false;
    }
    AGameModeBase* GameMode = GetWorld()->GetAuthGameMode();
    if (!GameMode || !GameMode->GetDefaultPawnClassForController(CachedController))
    {
        UE_LOG(LogTemp, Error, TEXT("%s could not find an authoritative GameMode/default Pawn class."), *GetName());
        return false;
    }

    FTransform RespawnTransform = GetCheckpointTransform();
    if (!HasCheckpoint())
    {
        if (APawn* ExistingPawn = CachedController->GetPawn())
        {
            RespawnTransform = ExistingPawn->GetActorTransform();
        }
        else
        {
            UE_LOG(LogTemp, Error, TEXT("%s has no checkpoint or current Pawn to respawn at."), *GetName());
            return false;
        }
    }
    RespawnTransform.SetScale3D(FVector::OneVector);

    APawn* OldPawn = CachedController->GetPawn();
    CachedController->UnPossess();
    if (OldPawn)
    {
        OldPawn->Destroy();
    }
    GameMode->RestartPlayerAtTransform(CachedController, RespawnTransform);
    if (!IsValid(CachedController->GetPawn()))
    {
        UE_LOG(LogTemp, Error, TEXT("%s failed to spawn the team's default Pawn at checkpoint."), *GetName());
        return false;
    }

    CachedController->SetControlRotation(RespawnTransform.Rotator());
    RequestNormalState();
    return true;
}
