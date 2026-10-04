from app.bm25 import BM25
from app.fusion import rrf
from app.text import fold, terms, tokens


def test_fold_removes_diacritics_and_maps_d_bar():
    assert fold("Hạn mức Đồng") == "han muc dong"


def test_numbers_with_thousand_separators_become_one_token():
    assert "5000000" in tokens("tối đa 5.000.000 đồng")


def test_terms_include_bigrams():
    assert "tai_khoan" in terms("tài khoản")


def test_bm25_ranks_matching_document_first_even_without_diacritics():
    docs = ["Hạn mức giao dịch mỗi ngày", "Phí rút tiền về ngân hàng", "Khóa tài khoản do sai PIN"]
    top = BM25(docs).top("rut tien ve ngan hang", 3)
    assert top[0][0] == 1


def test_bm25_returns_nothing_for_unrelated_query():
    assert BM25(["Hạn mức giao dịch"]).top("thời tiết hôm nay", 3) == []


def test_rrf_rewards_items_ranked_well_in_both_lists():
    fused = rrf([[1, 2, 3], [3, 1, 4]])
    assert [item for item, _ in fused][:2] == [1, 3]


def test_rrf_handles_empty_input():
    assert rrf([]) == []
    assert rrf([[]]) == []
