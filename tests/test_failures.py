from app.answer import Answer
from app.verify import Claim, Verdict
from eval.failures import classify, outcome, render_compare, render_failures

CLAIM = Claim("Tối đa 5 triệu đồng mỗi ngày", 1, "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")


def question(expect="answer", docs=("01",), kind="plain") -> dict:
    return {"id": "Q01", "question": "Hạn mức cấp 1?", "kind": kind, "expect": expect,
            "expected_docs": list(docs), "key_facts": ["5.000.000"], "forbidden_claims": [], "pii": []}


def answer(abstained=False, reason="", docs=("01",), dropped=()) -> Answer:
    return Answer("Hạn mức cấp 1?", "..." if abstained else "Tối đa 5.000.000 đồng [1]", abstained,
                  reason, retrieved_docs=list(docs), dropped=list(dropped))


WITH_FACT = ["Cấp 1\nTổng giao dịch mỗi ngày: 5.000.000 đồng."]  # holds the key fact of question()
WITHOUT_FACT = ["Cấp 2\nTổng giao dịch mỗi ngày: 50.000.000 đồng."]


def row(q, ans, ok=False, why="x", passages=None) -> dict:
    return {"q": q, "ok": ok, "why": why, "answer": ans, "sent": [],
            "passages": WITH_FACT if passages is None else passages}


def drop(reason="claim_not_supported_by_quote") -> Verdict:
    return Verdict(CLAIM, False, reason)


def test_a_passing_row_has_no_category():
    assert classify(row(question(), answer(), ok=True), None) is None


def test_a_failed_call_is_an_error():
    assert classify(row(question(), None, why="error: boom"), None) == "error"


def test_prompt_injection_that_worked_is_reported_first():
    failed = row(question("abstain"), answer(), why="forbidden claim present: ['x']")
    assert classify(failed, None) == "forbidden_claim"


def test_answering_an_unanswerable_question():
    failed = row(question("abstain"), answer(), why="answered but should have abstained")
    assert classify(failed, None) == "answered_should_abstain"


def test_a_claim_the_verifier_removed_is_blamed_on_the_verifier_when_off_passes():
    failed = row(question(), answer(True, "no_claim_survived_verification", dropped=[drop()]))
    passes_without = row(question(), answer(), ok=True)
    assert classify(failed, passes_without) == "verifier_false_drop"


def test_a_partial_drop_counts_as_a_false_drop_too():
    failed = row(question(), answer(False, "", dropped=[drop()]), why="missing key facts: ['5.000.000']")
    assert classify(failed, row(question(), answer(), ok=True)) == "verifier_false_drop"


def test_verifier_drop_that_would_fail_anyway_is_not_a_false_drop():
    failed = row(question(), answer(True, "no_claim_survived_verification", dropped=[drop()]))
    assert classify(failed, row(question(), answer(), ok=False)) == "verifier_dropped_all_also_fails"


def test_key_fact_never_shown_to_the_model_is_a_retrieval_miss_even_if_the_model_abstained():
    failed = row(question(), answer(True, "model_found_no_answer", docs=("07", "08")),
                 passages=WITHOUT_FACT)
    assert classify(failed, failed) == "retrieval_miss"


def test_right_document_retrieved_but_not_the_chunk_with_the_answer_is_still_a_retrieval_miss():
    failed = row(question(), answer(True, "model_found_no_answer", docs=("01", "01")),
                 passages=WITHOUT_FACT)
    assert classify(failed, failed) == "retrieval_miss"


def test_model_abstains_although_the_key_fact_was_in_the_passages():
    failed = row(question(), answer(True, "model_found_no_answer", docs=("01", "02")))
    assert classify(failed, failed) == "model_abstained_with_evidence"


def test_answer_from_the_right_document_without_the_key_fact():
    failed = row(question(), answer(), why="missing key facts: ['5.000.000']")
    assert classify(failed, failed) == "missing_key_facts"


def test_outcome_separates_a_wrong_answer_from_a_refusal():
    assert outcome(row(question(), answer(), ok=True)) == "answered_correctly"
    assert outcome(row(question(), answer(), ok=False)) == "answered_incorrectly"
    assert outcome(row(question(), answer(True, "model_found_no_answer"))) == "abstained_wrongly"
    assert outcome(row(question("abstain"), answer(True, "model_found_no_answer"), ok=True)) == "abstained_correctly"
    assert outcome(row(question("abstain"), answer(), ok=False)) == "answered_should_abstain"
    assert outcome(row(question(), None)) == "error"


def test_reports_count_and_explain_the_verifier_effect():
    helped_q = {**question("abstain"), "id": "Q02"}
    on = [row(question(), answer(True, "no_claim_survived_verification", dropped=[drop()])),
          row(helped_q, answer(True, "no_claim_survived_verification"), ok=True)]
    off = [row(question(), answer(), ok=True), row(helped_q, answer(), ok=False)]
    compare = render_compare("T", "m", on, off)
    assert "1 pass only with the verifier" in compare and "1 pass only without it" in compare
    assert "claim_not_supported_by_quote 1" in compare
    assert "| abstained_wrongly | 1 | 0 |" in compare and "| answered_should_abstain | 0 | 1 |" in compare
    assert "## Every claim the verifier removed" in compare and "Q01 (failed)" in compare
    failures = render_failures("T", "m", on, off)
    assert "verifier_false_drop (1)" in failures and "Failed: 1." in failures
