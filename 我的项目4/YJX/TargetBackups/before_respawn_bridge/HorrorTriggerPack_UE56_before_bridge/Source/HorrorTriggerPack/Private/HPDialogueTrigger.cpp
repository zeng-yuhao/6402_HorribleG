#include "HPDialogueTrigger.h"

#include "HPDialogueWidget.h"
#include "Components/ActorComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

AHPDialogueTrigger::AHPDialogueTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    DialogueZone = CreateDefaultSubobject<UBoxComponent>(TEXT("DialogueZone"));
    SetRootComponent(DialogueZone);
    DialogueZone->SetBoxExtent(FVector(180.0, 180.0, 120.0));
    DialogueZone->SetGenerateOverlapEvents(true);
    DialogueZone->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    DialogueZone->SetCollisionObjectType(ECC_WorldDynamic);
    DialogueZone->SetCollisionResponseToAllChannels(ECR_Ignore);
    DialogueZone->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    SpeakerName = FText::FromString(TEXT("NPC"));
    DialogueText = FText::FromString(TEXT("这里填写NPC的对话内容。"));
    DialogueWidgetClass = UHPDialogueWidget::StaticClass();
}

void AHPDialogueTrigger::BeginPlay()
{
    Super::BeginPlay();
    DialogueZone->OnComponentBeginOverlap.AddDynamic(this, &AHPDialogueTrigger::HandleBeginOverlap);
    DialogueZone->OnComponentEndOverlap.AddDynamic(this, &AHPDialogueTrigger::HandleEndOverlap);
}

void AHPDialogueTrigger::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    CloseDialogue();
    Super::EndPlay(EndPlayReason);
}

void AHPDialogueTrigger::HandleBeginOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    if (ActivePawn)
    {
        return;
    }

    APawn* OverlappingPawn = Cast<APawn>(OtherActor);
    APlayerController* PlayerController = OverlappingPawn
        ? Cast<APlayerController>(OverlappingPawn->GetController())
        : nullptr;
    if (!PlayerController)
    {
        return;
    }

    ActivePawn = OverlappingPawn;
    CachedController = PlayerController;
    RequestPlayerState(DialogueStateIndex);

    if (DialogueWidgetClass)
    {
        ActiveWidget = CreateWidget<UHPDialogueWidget>(PlayerController, DialogueWidgetClass);
        if (ActiveWidget)
        {
            ActiveWidget->SetDialogue(SpeakerName, DialogueText);
            ActiveWidget->AddToViewport(50);
        }
    }
}

void AHPDialogueTrigger::HandleEndOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex)
{
    if (OtherActor != ActivePawn)
    {
        return;
    }

    RequestPlayerState(NormalStateIndex);
    CloseDialogue();
}

void AHPDialogueTrigger::CloseDialogue()
{
    if (ActiveWidget)
    {
        ActiveWidget->RemoveFromParent();
        ActiveWidget = nullptr;
    }
    ActivePawn = nullptr;
    CachedController = nullptr;
}

UObject* AHPDialogueTrigger::FindPlayerStateManager() const
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

void AHPDialogueTrigger::RequestPlayerState(uint8 StateIndex) const
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
