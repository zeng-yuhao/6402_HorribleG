#include "HPDialogueWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/CoreStyle.h"

TSharedRef<SWidget> UHPDialogueWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        UCanvasPanel* RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
        WidgetTree->RootWidget = RootCanvas;

        UBorder* DialogueBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("DialogueBorder"));
        DialogueBorder->SetBrushColor(FLinearColor(0.015f, 0.02f, 0.03f, 0.88f));
        DialogueBorder->SetPadding(FMargin(28.0f, 20.0f));
        RootCanvas->AddChild(DialogueBorder);

        if (UCanvasPanelSlot* BorderSlot = Cast<UCanvasPanelSlot>(DialogueBorder->Slot))
        {
            BorderSlot->SetAnchors(FAnchors(0.5f, 1.0f));
            BorderSlot->SetAlignment(FVector2D(0.5f, 1.0f));
            BorderSlot->SetPosition(FVector2D(0.0f, -64.0f));
            BorderSlot->SetSize(FVector2D(920.0f, 210.0f));
        }

        UVerticalBox* TextColumn = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("TextColumn"));
        DialogueBorder->SetContent(TextColumn);

        SpeakerTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SpeakerName"));
        SpeakerTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(0.92f, 0.74f, 0.30f, 1.0f)));
        SpeakerTextBlock->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 25));
        TextColumn->AddChildToVerticalBox(SpeakerTextBlock);

        USpacer* Spacer = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass(), TEXT("SpeakerSpacer"));
        Spacer->SetSize(FVector2D(1.0f, 10.0f));
        TextColumn->AddChildToVerticalBox(Spacer);

        DialogueTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DialogueText"));
        DialogueTextBlock->SetAutoWrapText(true);
        DialogueTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor::White));
        DialogueTextBlock->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 21));
        if (UVerticalBoxSlot* DialogueSlot = TextColumn->AddChildToVerticalBox(DialogueTextBlock))
        {
            DialogueSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        }

        UTextBlock* HintTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CloseHint"));
        HintTextBlock->SetText(FText::FromString(TEXT("离开区域结束对话  /  Leave area to close")));
        HintTextBlock->SetJustification(ETextJustify::Right);
        HintTextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(0.55f, 0.58f, 0.62f, 1.0f)));
        HintTextBlock->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 13));
        TextColumn->AddChildToVerticalBox(HintTextBlock);
    }

    TSharedRef<SWidget> Result = Super::RebuildWidget();
    SetDialogue(PendingSpeakerName, PendingDialogueText);
    return Result;
}

void UHPDialogueWidget::SetDialogue(const FText& InSpeakerName, const FText& InDialogueText)
{
    PendingSpeakerName = InSpeakerName;
    PendingDialogueText = InDialogueText;

    if (SpeakerTextBlock)
    {
        SpeakerTextBlock->SetText(PendingSpeakerName);
    }
    if (DialogueTextBlock)
    {
        DialogueTextBlock->SetText(PendingDialogueText);
    }
}
