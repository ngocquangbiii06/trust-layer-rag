import pytest

from app.pii import mask_pii

PHONE_FORMS = [
    "0912 345 678", "0912.345.678", "0912-345-678",  # 4-3-3
    "091 234 5678", "091.234.5678", "091-234-5678",  # 3-3-4
    "091 2345 678", "0912 345678", "091 2345678",
    "+84 912 345 678", "+84.912.345.678", "+84-912-345-678", "+84 91 234 5678",
    "(+84) 912 345 678", "84 912 345 678", "+84912 345 678",
]
CCCD_FORMS = ["079 012 345 678", "079-012-345-678", "0790 1234 5678", "079012 345678"]
# Numbers, dates and legal references that look like personal data but are not.
NOT_PERSONAL = [
    "5.000.000 đồng", "100.000.000", "300.000.000.000 đồng", "84.000.000.000 đồng", "0,1%",
    "01.01.2026", "01-01-2026", "ngày 01-01-2026 đến 31-12-2026", "01-01-2026 02-02-2026",
    "ngày 05/11/2025", "91/2025/QH15", "40/2024/TT-NHNN", "12/2023/NĐ-CP", "Điều 12 khoản 3",
    "Điều 9 khoản 2 điểm a Luật 91/2025/QH15 có hiệu lực từ 01/01/2026 không?",
    "Tài khoản cấp 1 rút tối đa 10.000.000 đồng, phí 0,1% và tối thiểu 1.000 đồng",
]


def test_masks_vietnamese_mobile_number():
    result = mask_pii("Số 0912345678 của tôi bị khóa")
    assert "0912345678" not in result.text and "[SDT]" in result.text
    assert result.types == ("SDT",)


def test_masks_international_format_phone():
    assert "[SDT]" in mask_pii("gọi +84912345678 giúp").text


def test_twelve_digit_id_is_cccd_not_phone_or_account():
    result = mask_pii("CCCD 079012345678")
    assert result.text == "CCCD [CCCD]"
    assert result.types == ("CCCD",)


def test_masks_email_and_account_number():
    result = mask_pii("email a.b@mail.vn, tài khoản 1234567890123")
    assert "a.b@mail.vn" not in result.text and "1234567890123" not in result.text
    assert set(result.types) == {"EMAIL", "SO_TAI_KHOAN"}


def test_leaves_ordinary_numbers_alone():
    text = "Hạn mức 5.000.000 đồng, rút 3 lần mỗi tháng"
    assert mask_pii(text) == mask_pii(text) and mask_pii(text).text == text
    assert mask_pii(text).types == ()


@pytest.mark.parametrize("phone", PHONE_FORMS)
def test_masks_phone_numbers_written_with_spaces_dots_or_dashes(phone):
    result = mask_pii(f"SĐT {phone} bị khóa")
    assert result.text == "SĐT [SDT] bị khóa" and result.types == ("SDT",)


@pytest.mark.parametrize("phone", ["0912 345 678", "+84 912 345 678", "091-234-5678"])
def test_phone_is_masked_next_to_punctuation(phone):
    assert mask_pii(f"gọi {phone}.").text == "gọi [SDT]."
    assert mask_pii(f"({phone})").text == "([SDT])"


@pytest.mark.parametrize("cccd", CCCD_FORMS)
def test_masks_grouped_cccd(cccd):
    result = mask_pii(f"CCCD {cccd}")
    assert result.text == "CCCD [CCCD]" and result.types == ("CCCD",)


def test_grouped_card_number_is_one_account_number_not_a_cccd_with_a_tail():
    result = mask_pii("thẻ 1234 5678 9012 3456 bị khóa")
    assert result.text == "thẻ [SO_TAI_KHOAN] bị khóa" and result.types == ("SO_TAI_KHOAN",)


def test_phone_and_cccd_in_one_question_keep_their_own_labels():
    result = mask_pii("SĐT 0912 345 678, CCCD 079 012 345 678")
    assert result.text == "SĐT [SDT], CCCD [CCCD]" and result.types == ("SDT", "CCCD")


@pytest.mark.parametrize("text", NOT_PERSONAL)
def test_money_dates_and_legal_references_are_not_masked(text):
    assert mask_pii(text).text == text and mask_pii(text).types == ()
