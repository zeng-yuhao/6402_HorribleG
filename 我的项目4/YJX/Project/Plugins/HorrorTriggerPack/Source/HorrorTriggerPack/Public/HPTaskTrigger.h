#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "InputCoreTypes.h"
#include "HPTaskTrigger.generated.h"

class AHPTaskTrigger;
class APlayerController;
class APawn;
class UBoxComponent;
class UHPTaskWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
    FHPTaskSubmittedSignature,
    FName, TaskId,
    AHPTaskTrigger*, TaskTrigger);

/** Empty overlap actor that displays task UI and accepts a configurable submit key. */
UCLASS(Blueprintable)
class HORRORTRIGGERPACK_API AHPTaskTrigger : public AActor
{
    GENERATED_BODY()

public:
    AHPTaskTrigger();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Task Trigger")
    TObjectPtr<UBoxComponent> TaskZone;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Content",
        meta=(DisplayName="Task ID / 任务ID"))
    FName TaskId = TEXT("Task_001");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Content",
        meta=(DisplayName="Task Title / 任务标题"))
    FText TaskTitle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Content", meta=(MultiLine=true,
        DisplayName="Task Description / 任务说明"))
    FText TaskDescription;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Content",
        meta=(DisplayName="Completion Text / 完成提示"))
    FText CompletionText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Requirements",
        meta=(DisplayName="Require Rifle As Key / 需要步枪作为钥匙"))
    bool bRequireRifleAsKey = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Requirements",
        meta=(DisplayName="Consume Rifle On Submit / 提交时销毁步枪"))
    bool bConsumeRifleOnSubmit = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Requirements",
        meta=(DisplayName="Missing Key Text / 未持有钥匙提示"))
    FText MissingKeyText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Input",
        meta=(DisplayName="Submit Key / 提交按键"))
    FKey SubmitKey;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|Rules",
        meta=(DisplayName="One Shot / 只可完成一次"))
    bool bOneShot = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|UI",
        meta=(ClampMin="0.0", Units="s", DisplayName="Close Delay / 完成后关闭延迟"))
    float CloseDelayAfterSubmit = 1.25f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task Trigger|UI",
        meta=(DisplayName="Task Widget Class / 任务UI类"))
    TSubclassOf<UHPTaskWidget> TaskWidgetClass;

    UPROPERTY(BlueprintAssignable, Category="Task Trigger|Events",
        meta=(DisplayName="On Task Submitted / 任务已提交"))
    FHPTaskSubmittedSignature OnTaskSubmitted;

    UFUNCTION(BlueprintCallable, Category="Task Trigger",
        meta=(DisplayName="Submit Task / 提交任务"))
    void SubmitTask();

    UFUNCTION(BlueprintPure, Category="Task Trigger",
        meta=(DisplayName="Is Task Completed / 任务是否完成"))
    bool IsTaskCompleted() const { return bTaskCompleted; }

    UFUNCTION(BlueprintPure, Category="Task Trigger",
        meta=(DisplayName="Player Has Required Key / 玩家持有任务钥匙"))
    bool PlayerHasRequiredKey() const;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Task Trigger|Integration")
    uint8 TaskInteractionStateIndex = 2;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Task Trigger|Integration")
    uint8 NormalStateIndex = 0;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UFUNCTION()
    void HandleBeginOverlap(
        UPrimitiveComponent* OverlappedComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComp,
        int32 OtherBodyIndex,
        bool bFromSweep,
        const FHitResult& SweepResult);

    UFUNCTION()
    void HandleEndOverlap(
        UPrimitiveComponent* OverlappedComponent,
        AActor* OtherActor,
        UPrimitiveComponent* OtherComp,
        int32 OtherBodyIndex);

    UObject* FindPlayerStateManager() const;
    void RequestPlayerState(uint8 StateIndex) const;
    void ConsumeRifleKey();
    void CloseTaskUI();

    UPROPERTY(Transient)
    TObjectPtr<APlayerController> CachedController;

    UPROPERTY(Transient)
    TObjectPtr<APawn> ActivePawn;

    UPROPERTY(Transient)
    TObjectPtr<UHPTaskWidget> ActiveWidget;

    FTimerHandle CloseTimer;
    bool bTaskCompleted = false;
    bool bSubmitInputBound = false;
};
