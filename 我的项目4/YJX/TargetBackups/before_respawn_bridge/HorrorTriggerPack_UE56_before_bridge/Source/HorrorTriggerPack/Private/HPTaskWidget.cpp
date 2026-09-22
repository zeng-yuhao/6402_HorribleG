#include "HPTaskWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"

TSharedRef<SWidget> UHPTaskWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        UCanvasPanel* RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
        WidgetTree->RootWidget = RootCanvas;

        UBorder* TaskBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("TaskBorder"));
        TaskBorder->SetBrushColor(FLinearColor(0.015f, 0.025f, 0.035f, 0.9f));
        TaskBorder->SetPadding(FMargin(24.0f, 20.0f));
        RootCanvas->AddChild(TaskBorder);

        if (UCanvasPanelSlot* BorderSlot = Cast<UCanvasPanelSlot>(TaskBorder->Slot))
        {
            BorderSlot->SetAnchors(FAnchors(1.0f, 0.5f));
            BorderSlot->SetAlignment(FVector2D(1.0f, 0.5f));
            BorderSlot->SetPosition(FVector2D(-48.0f, 0.0f));
            BorderSlot->SetSize(FVector2D(560.0f, 260.0f));
        }

        UVerticalBox* TextColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("TextColumn"));
        TaskBorder->SetContent(TextColumn);

        TitleTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TaskTitle"));
        TitleTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(0.95f, 0.78f, 0.25f, 1.0f)));
        TitleTextBlock->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 25));
        TextColumn->AddChildToVerticalBox(TitleTextBlock);

        USpacer* TitleSpacer = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass(), TEXT("TitleSpacer"));
        TitleSpacer->SetSize(FVector2D(1.0f, 12.0f));
        TextColumn->AddChildToVerticalBox(TitleSpacer);

        DescriptionTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TaskDescription"));
        DescriptionTextBlock->SetAutoWrapText(true);
        DescriptionTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor::White));
        DescriptionTextBlock->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 19));
        if (UVerticalBoxSlot* DescriptionSlot = TextColumn->AddChildToVerticalBox(DescriptionTextBlock))
        {
            DescriptionSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        }

        PromptTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SubmitPrompt"));
        PromptTextBlock->SetJustification(ETextJustify::Right);
        PromptTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 0.75f, 1.0f, 1.0f)));
        PromptTextBlock->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 17));
        TextColumn->AddChildToVerticalBox(PromptTextBlock);
    }

    TSharedRef<SWidget> Result = Super::RebuildWidget();
    RefreshText();
    return Result;
}

void UHPTaskWidget::SetTaskContent(const FText& InTitle, const FText& InDescription, const FText& InSubmitKey)
{
    PendingTitle = InTitle;
    PendingDescription = InDescription;
    PendingSubmitKey = InSubmitKey;
    bPendingCompleted = false;
    bPendingRequirementMissing = false;
    RefreshText();
}

void UHPTaskWidget::SetCompleted(const FText& InCompletionText)
{
    PendingCompletionText = InCompletionText;
    bPendingCompleted = true;
    bPendingRequirementMissing = false;
    RefreshText();
}

void UHPTaskWidget::SetRequirementMissing(const FText& InRequirementMissingText)
{
    PendingRequirementMissingText = InRequirementMissingText;
    bPendingRequirementMissing = true;
    bPendingCompleted = false;
    RefreshText();
}

void UHPTaskWidget::RefreshText()
{
    if (TitleTextBlock)
    {
        TitleTextBlock->SetText(PendingTitle);
    }
    if (DescriptionTextBlock)
    {
        DescriptionTextBlock->SetText(PendingDescription);
    }
    if (PromptTextBlock)
    {
        if (bPendingCompleted)
        {
            PromptTextBlock->SetText(PendingCompletionText);
            PromptTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f, 0.95f, 0.45f, 1.0f)));
        }
        else if (bPendingRequirementMissing)
        {
            PromptTextBlock->SetText(PendingRequirementMissingText);
            PromptTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.37f, 0.28f, 1.0f)));
        }
        else
        {
            PromptTextBlock->SetText(FText::Format(
                NSLOCTEXT("HorrorTriggerPack", "SubmitTaskPrompt", "按 {0} 提交  /  Press {0} to Submit"),
                PendingSubmitKey));
            PromptTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 0.75f, 1.0f, 1.0f)));
        }
    }
}
