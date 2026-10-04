# Failure analysis - L0 - openai-compat:openai/gpt-oss-20b - verifier on

Questions: 60. Failed: 11. Passed: 49.

| Cause | Count | Meaning |
|---|---|---|
| verifier_false_drop | 1 | the verifier removed a claim that was needed; without the verifier the question passes |
| retrieval_miss | 10 | the passages sent to the model do not contain every key fact, so the answer was never in front of the model |

## Ceiling: key facts present in the top-k passages

Answerable questions whose every key fact is written in the k passages that hybrid search returns. The model cannot do better than this, whatever the prompt or verifier.

| passages sent (k) | questions covered |
|---|---|
| 3 | 36/49 |
| 4 | 38/49 |
| 5 | 41/49 |
| 6 | 43/49 |
| 8 | 45/49 |
| 10 | 45/49 |

## verifier_false_drop (1)

the verifier removed a claim that was needed; without the verifier the question passes

- **Q53** (paraphrase, expect=answer): Mình lỡ bấm nhầm số người nhận khi chuyển, có lấy lại được không?
  - answer: Nếu người nhận không đồng ý, Ví Mây không có quyền tự ý lấy lại tiền. [1] Ví Mây không cam kết thu hồi được tiền chuyển nhầm. [2]
  - why failed: missing key facts: ['24 giờ']; retrieved docs ['12', '12', '08', '12'], expected ['12']
  - verifier removed [claim_not_supported_by_quote]: claim "Có thể lấy lại nếu báo trong vòng 24 giờ và người nhận đồng ý hoàn trả." quote "Người chuyển nhầm cần báo qua mục Hỗ trợ trong vòng 24 giờ kể từ khi chuyển để Ví Mây có thể hỗ trợ tạm giữ k…"

## retrieval_miss (10)

the passages sent to the model do not contain every key fact, so the answer was never in front of the model

- **Q25** (no_diacritics, expect=answer): rut tien ve ngan hang co mat phi khong
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['01', '02', '02', '01'], expected ['02']
- **Q35** (ambiguous, expect=answer): Hạn mức giao dịch mỗi ngày là bao nhiêu?
  - answer: Cấp 2: Tổng giao dịch mỗi ngày là 50.000.000 đồng. [1] Cấp 3: Tổng giao dịch mỗi ngày là 200.000.000 đồng. [2]
  - why failed: missing key facts: ['5.000.000']; retrieved docs ['08', '01', '01', '01'], expected ['01']
- **Q38** (paraphrase, expect=answer): Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['06', '05', '12', '05'], expected ['02']
- **Q41** (paraphrase, expect=answer): Chụp giấy tờ xong thì bao lâu mới biết kết quả?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (no_claim_survived_verification) but should have answered; retrieved docs ['04', '09', '12', '03'], expected ['04']
  - verifier removed [claim_not_supported_by_quote]: claim "Kết quả sẽ được biết trong vòng 24 giờ." quote "Mỗi tài khoản được thử lại tối đa 5 lần trong 24 giờ."
- **Q42** (paraphrase, expect=answer): Tại sao ảnh căn cước của mình bị trả lại?
  - answer: Bạn cần xác thực lại nếu đổi số căn cước hoặc họ tên. [1]
  - why failed: missing key facts: ['ảnh mờ']; retrieved docs ['11', '04', '01', '09'], expected ['04']
- **Q43** (paraphrase, expect=answer): Có người gọi tự nhận là nhân viên ví và xin mã xác nhận gửi về điện thoại, mình nên làm gì?
  - answer: Đây là dấu hiệu lừa đảo, không nên cung cấp mã OTP. [1]
  - why failed: missing key facts: ['giả mạo']; retrieved docs ['06', '05', '01', '12'], expected ['06']
- **Q49** (paraphrase, expect=answer): Ví có bán thông tin của mình cho bên thứ ba không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['06', '01', '04', '09'], expected ['09']
- **Q51** (paraphrase, expect=answer): Mình không dùng ví nữa thì hủy ví bằng cách nào?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['03', '07', '11', '02'], expected ['10']
- **Q52** (paraphrase, expect=answer): Mã giảm giá để lâu quá có bị mất không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['03', '12', '08', '10'], expected ['11']
- **Q54** (paraphrase, expect=answer): Ví có tính tiền hằng tháng để giữ tài khoản không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['02', '05', '07', '03'], expected ['02']
