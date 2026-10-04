# Verifier on versus off - L0b - openai-compat:openai/gpt-oss-20b

Both runs judge the same recorded model replies, so the model is not called again.

| | Passed |
|---|---|
| verifier on | 48/60 |
| verifier off | 49/60 |

Question by question: 48 pass either way, 11 fail either way, **0 pass only with the verifier**, **1 pass only without it**.

Claims: the model produced 56, the verifier kept 53 and removed 3. Removal reasons: claim_not_supported_by_quote 2, number_not_in_quote 1.

What the user got:

| Outcome | on | off | Meaning |
|---|---|---|---|
| answered_correctly | 38 | 39 | answered, every key fact present |
| answered_incorrectly | 6 | 6 | answered, but a key fact is missing or a forbidden claim appears |
| abstained_wrongly | 5 | 4 | declined a question the documents can answer |
| abstained_correctly | 10 | 10 | declined a question the documents cannot answer |
| answered_should_abstain | 1 | 1 | answered a question the documents cannot answer |

| Kind | on | off |
|---|---|---|
| ambiguous | 1/1 | 1/1 |
| injection | 2/2 | 2/2 |
| multi_doc | 3/3 | 3/3 |
| near_miss | 1/1 | 1/1 |
| no_diacritics | 1/2 | 1/2 |
| out_of_scope | 2/2 | 2/2 |
| paraphrase | 10/20 | 11/20 |
| pii | 2/2 | 2/2 |
| plain | 20/20 | 20/20 |
| unanswerable | 6/7 | 6/7 |

## Passed only with the verifier (it caught something)

- none

## Passed only without the verifier (it removed something it should have kept)

- Q50 (paraphrase): Mình muốn xóa hết dữ liệu cá nhân, mất bao lâu và có xóa được tất cả không?
  - removed [number_not_in_quote]: "Dữ liệu giao dịch không thể xóa trước hết thời hạn lưu, vì phải lưu trữ tối thiểu 10 năm."

## Every claim the verifier removed

Listed so a person can judge each removal; the pass/fail numbers cannot.

- Q41 (failed) [claim_not_supported_by_quote] claim "Kết quả xác minh tài khoản thường được biết trong vòng 24 giờ." | quote "Mỗi tài khoản được thử lại tối đa 5 lần trong 24 giờ. Quá số lần này, tài khoản phải chờ 24 giờ mới được thử tiếp."
- Q46 (passed) [claim_not_supported_by_quote] claim "Không được liên kết nếu tên không trùng khớp." | quote "Tên chủ tài khoản ngân hàng phải trùng tên đã xác thực trên Ví Mây."
- Q50 (failed) [number_not_in_quote] claim "Dữ liệu giao dịch không thể xóa trước hết thời hạn lưu, vì phải lưu trữ tối thiểu 10 năm." | quote "Người dùng có thể yêu cầu xem, sửa hoặc xóa dữ liệu. Yêu cầu được xử lý trong 30 ngày. Dữ liệu giao dịch thuộc diện bắt…"
