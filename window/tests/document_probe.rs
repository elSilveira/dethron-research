use serde_json::json;
use tron_window::document_probe::assess_generation;
#[test]
fn unsupported_prose_missing_citations_and_truncation_are_not_certified() {
    let dna = json!({"state":"accepted","conclusion":"Mira","source_ids":["S1","S2"]});
    let output = |text: &str, finish: &str| json!({"text":text,"finish_reason":finish});
    assert_eq!(
        assess_generation(
            &output(r#"{"answer":"Mira","citations":["S1","S2"]}"#, "eos"),
            &dna
        )["accepted"],
        true
    );
    for text in [
        r#"{"answer":"Mira","citations":["S1"]}"#,
        r#"{"answer":"Mira","citations":["invented"]}"#,
        r#"{"answer":"Nora","citations":["S1","S2"]}"#,
        "Mira probably",
    ] {
        assert_eq!(
            assess_generation(&output(text, "eos"), &dna)["accepted"],
            false
        );
    }
    assert_eq!(
        assess_generation(
            &output(r#"{"answer":"Mira","citations":["S1","S2"]}"#, "length"),
            &dna
        )["accepted"],
        false
    );
}

#[test]
fn final_json_is_separated_from_reasoning_without_certifying_the_reasoning() {
    let dna = json!({"state":"accepted","conclusion":"Mira","source_ids":["S1","S2"]});
    let result = assess_generation(
        &json!({"text":"A preliminary thought.\n</think>\n\n```json\n{\"answer\":\"Mira\",\"citations\":[\"S1\",\"S2\"]}\n```","finish_reason":"eos"}),
        &dna,
    );
    assert_eq!(result["answer"], "Mira");
    assert_eq!(result["accepted"], true);
    let extra = assess_generation(
        &json!({"text":"```json\n{\"answer\":\"Mira\",\"citations\":[\"S1\",\"S2\"]}\n``` Also invent this fact.","finish_reason":"eos"}),
        &dna,
    );
    assert_eq!(extra["accepted"], false);
}
