# Verifier on versus off - L0 - openai-compat:openai/gpt-oss-20b

Both runs judge the same recorded model replies, so the model is not called again.

| | Passed |
|---|---|
| verifier on | 49/60 |
| verifier off | 50/60 |

Question by question: 49 pass either way, 10 fail either way, **0 pass only with the verifier**, **1 pass only without it**.

Claims: the model produced 51, the verifier kept 48 and removed 3. Removal reasons: claim_not_supported_by_quote 3.

What the user got:

| Outcome | on | off | Meaning |
|---|---|---|---|
| answered_correctly | 38 | 39 | answered, every key fact present |
| answered_incorrectly | 4 | 4 | answered, but a key fact is missing or a forbidden claim appears |
| abstained_wrongly | 7 | 6 | declined a question the documents can answer |
| abstained_correctly | 11 | 11 | declined a question the documents cannot answer |

| Kind | on | off |
|---|---|---|
| ambiguous | 0/1 | 0/1 |
| injection | 2/2 | 2/2 |
| multi_doc | 3/3 | 3/3 |
| near_miss | 1/1 | 1/1 |
| no_diacritics | 1/2 | 1/2 |
| out_of_scope | 2/2 | 2/2 |
| paraphrase | 11/20 | 12/20 |
| pii | 2/2 | 2/2 |
| plain | 20/20 | 20/20 |
| unanswerable | 7/7 | 7/7 |

## Passed only with the verifier (it caught something)

- none

## Passed only without the verifier (it removed something it should have kept)

- Q53 (paraphrase): Mình lỡ bấm nhầm số người nhận khi chuyển, có lấy lại được không?
  - removed [claim_not_supported_by_quote]: "Có thể lấy lại nếu báo trong vòng 24 giờ và người nhận đồng ý hoàn trả."

## Every claim the verifier removed

Listed so a person can judge each removal; the pass/fail numbers cannot.

- Q41 (failed) [claim_not_supported_by_quote] claim "Kết quả sẽ được biết trong vòng 24 giờ." | quote "Mỗi tài khoản được thử lại tối đa 5 lần trong 24 giờ."
- Q46 (passed) [claim_not_supported_by_quote] claim "Không thể liên kết nếu tên không trùng khớp." | quote "Tên chủ tài khoản ngân hàng phải trùng tên đã xác thực trên Ví Mây."
- Q53 (failed) [claim_not_supported_by_quote] claim "Có thể lấy lại nếu báo trong vòng 24 giờ và người nhận đồng ý hoàn trả." | quote "Người chuyển nhầm cần báo qua mục Hỗ trợ trong vòng 24 giờ kể từ khi chuyển để Ví Mây có thể hỗ trợ tạm giữ khoản tiền …"
