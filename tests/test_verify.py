from app.verify import Claim, verify_claim

PASSAGES = [
    "Cấp 1: chỉ xác thực số điện thoại\n- Số dư ví tối đa: 10.000.000 đồng.\n- Tổng giao dịch mỗi ngày: 5.000.000 đồng.",
    "Rút tiền về ngân hàng\n- Phí 0,1% giá trị giao dịch, tối thiểu 1.000 đồng.",
]


def test_supported_claim_passes():
    claim = Claim("Tài khoản cấp 1 giao dịch tối đa 5.000.000 đồng mỗi ngày", 1,
                  "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")
    assert verify_claim(claim, PASSAGES).ok  # the "1" is backed by the passage heading "Cấp 1"


def test_number_restated_from_the_question_is_allowed():
    claim = Claim("Phí tối thiểu 1.000 đồng khi rút 3 lần", 2, "Phí 0,1% giá trị giao dịch, tối thiểu 1.000 đồng.")
    assert not verify_claim(claim, PASSAGES).ok  # 3 appears nowhere
    assert verify_claim(claim, PASSAGES, question="Rút 3 lần thì mất phí bao nhiêu?").ok


def test_quote_not_in_passage_is_rejected():
    claim = Claim("Hạn mức là 9.000.000 đồng", 1, "Tổng giao dịch mỗi ngày: 9.000.000 đồng.")
    verdict = verify_claim(claim, PASSAGES)
    assert not verdict.ok and verdict.reason == "quote_not_in_source"


def test_invented_number_with_true_quote_is_rejected():
    claim = Claim("Hạn mức mỗi ngày là 50.000.000 đồng", 1, "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")
    verdict = verify_claim(claim, PASSAGES)
    assert not verdict.ok and verdict.reason == "number_not_in_quote"


def test_true_quote_attached_to_unrelated_claim_is_rejected():
    claim = Claim("Ví Mây hoàn tiền trong ba ngày làm việc", 1, "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")
    verdict = verify_claim(claim, PASSAGES)
    assert not verdict.ok and verdict.reason == "claim_not_supported_by_quote"


def test_bad_source_index_is_rejected():
    assert verify_claim(Claim("x" * 20, 7, "y" * 20), PASSAGES).reason == "bad_source"


def test_quote_match_ignores_case_diacritics_and_spacing():
    claim = Claim("Phí rút là 0,1% giá trị giao dịch", 2, "phi 0,1%   gia tri giao dich")
    assert verify_claim(claim, PASSAGES).ok

def test_quote_match_ignores_quote_marks_and_list_bullets():
    passages = ['Khi nghi ngờ bị lừa\n- Khóa ví ngay trong mục Bảo mật.\n- Báo cáo qua mục Hỗ trợ, chọn "Báo cáo lừa đảo".']
    joined = Claim("Khóa ví ngay rồi báo cáo lừa đảo", 1,
                   "Khóa ví ngay trong mục Bảo mật. Báo cáo qua mục Hỗ trợ, chọn 'Báo cáo lừa đảo'.")
    assert verify_claim(joined, passages).ok


def test_quote_must_still_match_whole_words_in_order():
    passages = ["Phí\nPhí rút tiền là 10.000 đồng, phí chuyển tiền là 3.300 đồng."]
    assert verify_claim(Claim("Phí rút tiền là 3.300 đồng", 1, "Phí rút tiền là 3.300 đồng"), passages).reason == "quote_not_in_source"
    assert verify_claim(Claim("Phí rút tiền là 10.000 đồng", 1, "phí rút tiền là 10.00"), passages).reason == "quote_not_in_source"
