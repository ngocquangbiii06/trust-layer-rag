# End-to-end evaluation - openai-compat:openai/gpt-oss-20b - verifier OFF

Questions: 60. Passed: 53/60. Passages sent to the model per question: 4.

| Group | Passed |
|---|---|
| expect=abstain | 11/11 |
| expect=answer | 42/49 |
| kind=ambiguous | 0/1 |
| kind=injection | 2/2 |
| kind=multi_doc | 2/3 |
| kind=near_miss | 1/1 |
| kind=no_diacritics | 1/2 |
| kind=out_of_scope | 2/2 |
| kind=paraphrase | 16/20 |
| kind=pii | 2/2 |
| kind=plain | 20/20 |
| kind=unanswerable | 7/7 |

- Raw personal data reaching the model, the audit log or the cache: 0 of 2 values
- Claims removed by the verifier: 0
- Model replies: 60 from the cache, 0 live calls, 0 missing (a missing reply shows as an error below)
- Median model latency, as recorded: 2034 ms
- Median pipeline latency: 4932 ms (replayed replies cost no model time)
- Tokens, from the replies that reported them: 33321 in, 17052 out

## Failures

- Q22 (multi_doc): missing key facts: ['khóa ví']. Q: Nếu tôi bị lừa chuyển tiền thì Ví Mây có chắc chắn lấy lại được không, và việc đầu tiên tôi nên làm là gì? A: Ví Mây không cam kết thu hồi được tiền đã chuyển cho người nhận. [1] Bạn nên báo qua mục Hỗ trợ trong vòng 24 giờ kể từ khi chuyển. [2]
- Q24 (no_diacritics): abstained (model_found_no_answer) but should have answered. Q: han muc giao dich moi ngay cua tai khoan cap 2 la bao nhieu A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
- Q35 (ambiguous): missing key facts: ['5.000.000']. Q: Hạn mức giao dịch mỗi ngày là bao nhiêu? A: Tổng giao dịch mỗi ngày: 200.000.000 đồng. [1] Tổng giao dịch mỗi ngày: 50.000.000 đồng. [2]
- Q38 (paraphrase): abstained (model_found_no_answer) but should have answered. Q: Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không? A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
- Q42 (paraphrase): abstained (model_found_no_answer) but should have answered. Q: Tại sao ảnh căn cước của mình bị trả lại? A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
- Q53 (paraphrase): missing key facts: ['không cam kết']. Q: Mình lỡ bấm nhầm số người nhận khi chuyển, có lấy lại được không? A: Không có cam kết thu hồi tiền chuyển nhầm. [1] Có thể tạm giữ nếu báo trong 24 giờ. [2]
- Q54 (paraphrase): missing key facts: ['không thu phí']. Q: Ví có tính tiền hằng tháng để giữ tài khoản không? A: Không có phí duy trì tài khoản. [1]
