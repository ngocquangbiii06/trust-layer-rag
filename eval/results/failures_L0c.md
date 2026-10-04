# Failure analysis - L0c - openai-compat:openai/gpt-oss-20b - verifier on

Questions: 60. Failed: 7. Passed: 53.

| Cause | Count | Meaning |
|---|---|---|
| retrieval_miss | 3 | the passages sent to the model do not contain every key fact, so the answer was never in front of the model |
| model_abstained_with_evidence | 1 | every key fact was in the passages but the model said it could not answer |
| missing_key_facts | 3 | answered from the right document but a key fact is missing from the answer |

## Ceiling: key facts present in the top-k passages

Answerable questions whose every key fact is written in the k passages that hybrid search returns. The model cannot do better than this, whatever the prompt or verifier.

| passages sent (k) | questions covered |
|---|---|
| 3 | 46/49 |
| 4 | 46/49 |
| 5 | 47/49 |
| 6 | 47/49 |
| 8 | 47/49 |
| 10 | 48/49 |

## retrieval_miss (3)

the passages sent to the model do not contain every key fact, so the answer was never in front of the model

- **Q24** (no_diacritics, expect=answer): han muc giao dich moi ngay cua tai khoan cap 2 la bao nhieu
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['01', '02', '12', '08'], expected ['01']
- **Q35** (ambiguous, expect=answer): Hạn mức giao dịch mỗi ngày là bao nhiêu?
  - answer: Tổng giao dịch mỗi ngày: 200.000.000 đồng. [1] Tổng giao dịch mỗi ngày: 50.000.000 đồng. [2]
  - why failed: missing key facts: ['5.000.000']; retrieved docs ['01', '01', '01', '08'], expected ['01']
- **Q38** (paraphrase, expect=answer): Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['08', '12', '06', '12'], expected ['02']

## model_abstained_with_evidence (1)

every key fact was in the passages but the model said it could not answer

- **Q42** (paraphrase, expect=answer): Tại sao ảnh căn cước của mình bị trả lại?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['11', '04', '12', '06'], expected ['04']

## missing_key_facts (3)

answered from the right document but a key fact is missing from the answer

- **Q22** (multi_doc, expect=answer): Nếu tôi bị lừa chuyển tiền thì Ví Mây có chắc chắn lấy lại được không, và việc đầu tiên tôi nên làm là gì?
  - answer: Ví Mây không cam kết thu hồi được tiền đã chuyển cho người nhận. [1] Bạn nên báo qua mục Hỗ trợ trong vòng 24 giờ kể từ khi chuyển. [2]
  - why failed: missing key facts: ['khóa ví']; retrieved docs ['06', '12', '12', '12'], expected ['06']
- **Q53** (paraphrase, expect=answer): Mình lỡ bấm nhầm số người nhận khi chuyển, có lấy lại được không?
  - answer: Không có cam kết thu hồi tiền chuyển nhầm. [1] Có thể tạm giữ nếu báo trong 24 giờ. [2]
  - why failed: missing key facts: ['không cam kết']; retrieved docs ['12', '12', '06', '08'], expected ['12']
- **Q54** (paraphrase, expect=answer): Ví có tính tiền hằng tháng để giữ tài khoản không?
  - answer: Không có phí duy trì tài khoản. [1]
  - why failed: missing key facts: ['không thu phí']; retrieved docs ['02', '12', '11', '02'], expected ['02']
