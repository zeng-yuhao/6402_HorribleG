#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HPDialogueTrigger.generated.h"

class APlayerController;
class APawn;
class UBoxComponent;
class UHPDialogueWidget;

/** Empty overlap actor that enters Dialogue state and displays a text panel. */
UCLASS(Blueprintable)
class HORRORTRIGGERPACK_API AHPDialogueTrigger : public AActor
{
    GENERATED_BODY()

public:
    AHPDialogueTrigger();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="NPC Dialogue")
    TObjectPtr<UBoxComponent> DialogueZone;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Dialogue|Content",
        meta=(DisplayName="Speaker Name / NPC名称"))
    FText SpeakerName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Dialogue|Content", meta=(MultiLine=true,
        DisplayName="Dialogue Text / 对话内容"))
    FText DialogueText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="NPC Dialogue|UI",
        meta=(DisplayName="Dialogue Widget Class / 对话UI类"))
    TSubclassOf<UHPDialogueWidget> DialogueWidgetClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="NPC Dialogue|Integration")
    uint8 DialogueStateIndex = 1;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="NPC Dialogue|Integration")
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
    void CloseDialogue();

    UPROPERTY(Transient)
    TObjectPtr<APlayerController> CachedController;

    UPROPERTY(Transient)
    TObjectPtr<APawn> ActivePawn;

    UPROPERTY(Transient)
    TObjectPtr<UHPDialogueWidget> ActiveWidget;
};
