#include "HPTaskTrigger.h"

#include "HPTaskWidget.h"
#include "HPKeyInventoryComponent.h"
#include "Components/ActorComponent.h"
#include "Components/BoxComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

AHPTaskTrigger::AHPTaskTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    TaskZone = CreateDefaultSubobject<UBoxComponent>(TEXT("TaskZone"));
    SetRootComponent(TaskZone);
    TaskZone->SetBoxExtent(FVector(180.0, 180.0, 120.0));
    TaskZone->SetGenerateOverlapEvents(true);
    TaskZone->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TaskZone->SetCollisionObjectType(ECC_WorldDynamic);
    TaskZone->SetCollisionResponseToAllChannels(ECR_Ignore);
    TaskZone->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    TaskTitle = FText::FromString(TEXT("新任务"));
    TaskDescription = FText::FromString(TEXT("这里填写任务目标或提交说明。"));
    CompletionText = FText::FromString(TEXT("任务已提交  /  Task Submitted"));
    MissingKeyText = FText::FromString(TEXT("尚未持有钥匙"));
    SubmitKey = EKeys::F;
    TaskWidgetClass = UHPTaskWidget::StaticClass();
}

void AHPTaskTrigger::BeginPlay()
{
    Super::BeginPlay();
    TaskZone->OnComponentBeginOverlap.AddDynamic(this, &AHPTaskTrigger::HandleBeginOverlap);
    TaskZone->OnComponentEndOverlap.AddDynamic(this, &AHPTaskTrigger::HandleEndOverlap);
}

void AHPTaskTrigger::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    GetWorldTimerManager().ClearTimer(CloseTimer);
    CloseTaskUI();
    Super::EndPlay(EndPlayReason);
}

void AHPTaskTrigger::HandleBeginOverlap(
    UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    if (ActivePawn || (bOneShot && bTaskCompleted))
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
    RequestPlayerState(TaskInteractionStateIndex);

    if (TaskWidgetClass)
    {
        ActiveWidget = CreateWidget<UHPTaskWidget>(PlayerController, TaskWidgetClass);
        if (ActiveWidget)
        {
            ActiveWidget->SetTaskContent(TaskTitle, TaskDescription, SubmitKey.GetDisplayName());
            ActiveWidget->AddToViewport(55);
        }
    }

    EnableInput(PlayerController);
    if (InputComponent && !bSubmitInputBound)
    {
        FInputKeyBinding& Binding = InputComponent->BindKey(SubmitKey, IE_Pressed, this, &AHPTaskTrigger::SubmitTask);
        Binding.bConsumeInput = true;
        bSubmitInputBound = true;
    }
}

void AHPTaskTrigger::HandleEndOverlap(
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
    CloseTaskUI();
}

void AHPTaskTrigger::SubmitTask()
{
    if (!ActivePawn || bTaskCompleted)
    {
        return;
    }

    if (!PlayerHasRequiredKey())
    {
        if (ActiveWidget)
        {
            ActiveWidget->SetRequirementMissing(MissingKeyText);
        }
        return;
    }

    if (bRequireBPKey && bConsumeKeyOnSubmit && !ConsumeRequiredKey())
    {
        if (ActiveWidget)
        {
            ActiveWidget->SetRequirementMissing(MissingKeyText);
        }
        return;
    }

    bTaskCompleted = true;
    RequestPlayerState(NormalStateIndex);
    if (CachedController)
    {
        DisableInput(CachedController);
    }

    if (ActiveWidget)
    {
        ActiveWidget->SetCompleted(CompletionText);
    }

    OnTaskSubmitted.Broadcast(TaskId, this);

    if (CloseDelayAfterSubmit <= 0.0f)
    {
        CloseTaskUI();
    }
    else
    {
        GetWorldTimerManager().SetTimer(
            CloseTimer,
            this,
            &AHPTaskTrigger::CloseTaskUI,
            CloseDelayAfterSubmit,
            false);
    }
}

bool AHPTaskTrigger::PlayerHasRequiredKey() const
{
    if (!bRequireBPKey)
    {
        return true;
    }

    if (!CachedController)
    {
        return false;
    }

    const UHPKeyInventoryComponent* Inventory = CachedController->FindComponentByClass<UHPKeyInventoryComponent>();
    return Inventory && Inventory->HasKey(RequiredKeyId);
}

bool AHPTaskTrigger::ConsumeRequiredKey()
{
    UHPKeyInventoryComponent* Inventory = CachedController
        ? CachedController->FindComponentByClass<UHPKeyInventoryComponent>()
        : nullptr;
    return Inventory && Inventory->ConsumeKey(RequiredKeyId);
}

void AHPTaskTrigger::CloseTaskUI()
{
    GetWorldTimerManager().ClearTimer(CloseTimer);

    if (ActiveWidget)
    {
        ActiveWidget->RemoveFromParent();
        ActiveWidget = nullptr;
    }
    if (CachedController)
    {
        DisableInput(CachedController);
    }

    ActivePawn = nullptr;
    CachedController = nullptr;
    if (bOneShot && bTaskCompleted)
    {
        TaskZone->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    else if (!bOneShot)
    {
        bTaskCompleted = false;
    }
}

UObject* AHPTaskTrigger::FindPlayerStateManager() const
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

void AHPTaskTrigger::RequestPlayerState(uint8 StateIndex) const
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
