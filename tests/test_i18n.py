from t2_agent.i18n import t


def test_english_upload_prompt_and_summary_labels_are_available():
    assert "received the file" in t("English", "upload_received")
    assert t("English", "structured_summary") == "View structured summary"
