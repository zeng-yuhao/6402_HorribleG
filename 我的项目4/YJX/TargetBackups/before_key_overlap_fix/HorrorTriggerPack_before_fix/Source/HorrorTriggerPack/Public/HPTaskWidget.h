#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "HPTaskWidget.generated.h"

class UTextBlock;

/** Runtime-built task panel used by HPTaskTrigger. */
UCLASS(Blueprintable)
class HORRORTRIGGERPACK_API UHPTaskWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Task UI")
    void SetTaskContent(const FText& InTitle, const FText& InDescription, const FText& InSubmitKey);

    UFUNCTION(BlueprintCallable, Category="Task UI")
    void SetCompleted(const FText& InCompletionText);

    UFUNCTION(BlueprintCallable, Category="Task UI")
    void SetRequirementMissing(const FText& InRequirementMissingText);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    void RefreshText();

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> TitleTextBlock;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DescriptionTextBlock;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> PromptTextBlock;

    FText PendingTitle;
    FText PendingDescription;
    FText PendingSubmitKey;
    FText PendingCompletionText;
    FText PendingRequirementMissingText;
    bool bPendingCompleted = false;
    bool bPendingRequirementMissing = false;
};
