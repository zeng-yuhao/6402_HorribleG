#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "HPDialogueWidget.generated.h"

class UTextBlock;

/** Runtime-built dialogue panel used by HPDialogueTrigger. */
UCLASS(Blueprintable)
class HORRORTRIGGERPACK_API UHPDialogueWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Dialogue UI")
    void SetDialogue(const FText& InSpeakerName, const FText& InDialogueText);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> SpeakerTextBlock;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DialogueTextBlock;

    FText PendingSpeakerName;
    FText PendingDialogueText;
};
