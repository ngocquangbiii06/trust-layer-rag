# Failure analysis - L0b - openai-compat:openai/gpt-oss-20b - verifier on

Questions: 60. Failed: 12. Passed: 48.

| Cause | Count | Meaning |
|---|---|---|
| answered_should_abstain | 1 | answered a question the documents cannot answer |
| verifier_false_drop | 1 | the verifier removed a claim that was needed; without the verifier the question passes |
| retrieval_miss | 5 | the passages sent to the model do not contain every key fact, so the answer was never in front of the model |
| model_abstained_with_evidence | 2 | every key fact was in the passages but the model said it could not answer |
| missing_key_facts | 3 | answered from the right document but a key fact is missing from the answer |

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

## answered_should_abstain (1)

answered a question the documents cannot answer

- **Q29** (unanswerable, expect=abstain): Bị phạt bao nhiêu tiền nếu nhập sai OTP nhiều lần?
  - answer: Không có phạt tiền, chỉ cần chờ 24 giờ rồi thử lại. [1]
  - why failed: answered but should have abstained; retrieved docs ['02', '12', '06', '03', '07', '02'], expected []

## verifier_false_drop (1)

the verifier removed a claim that was needed; without the verifier the question passes

- **Q50** (paraphrase, expect=answer): Mình muốn xóa hết dữ liệu cá nhân, mất bao lâu và có xóa được tất cả không?
  - answer: Bạn có thể yêu cầu xóa dữ liệu cá nhân và yêu cầu sẽ được xử lý trong 30 ngày. [1]
  - why failed: missing key facts: ['không thể xóa']; retrieved docs ['09', '09', '10', '10', '05', '09'], expected ['09']
  - verifier removed [number_not_in_quote]: claim "Dữ liệu giao dịch không thể xóa trước hết thời hạn lưu, vì phải lưu trữ tối thiểu 10 năm." quote "Người dùng có thể yêu cầu xem, sửa hoặc xóa dữ liệu. Yêu cầu được xử lý trong 30 ngày. Dữ liệu giao dịch thuộ…"

## retrieval_miss (5)

the passages sent to the model do not contain every key fact, so the answer was never in front of the model

- **Q41** (paraphrase, expect=answer): Chụp giấy tờ xong thì bao lâu mới biết kết quả?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (no_claim_survived_verification) but should have answered; retrieved docs ['04', '09', '12', '03', '06', '07'], expected ['04']
  - verifier removed [claim_not_supported_by_quote]: claim "Kết quả xác minh tài khoản thường được biết trong vòng 24 giờ." quote "Mỗi tài khoản được thử lại tối đa 5 lần trong 24 giờ. Quá số lần này, tài khoản phải chờ 24 giờ mới được thử …"
- **Q42** (paraphrase, expect=answer): Tại sao ảnh căn cước của mình bị trả lại?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['11', '04', '01', '09', '07', '05'], expected ['04']
- **Q51** (paraphrase, expect=answer): Mình không dùng ví nữa thì hủy ví bằng cách nào?
  - answer: Rút hoặc chuyển hết số dư về ngân hàng đã liên kết. Vào Cài đặt, chọn Đóng tài khoản và xác nhận bằng khuôn mặt. [1]
  - why failed: missing key facts: ['bằng 0']; retrieved docs ['03', '07', '11', '02', '05', '10'], expected ['10']
- **Q52** (paraphrase, expect=answer): Mã giảm giá để lâu quá có bị mất không?
  - answer: Voucher đã hết hạn không được cấp lại. [1]
  - why failed: missing key facts: ['30 ngày']; retrieved docs ['03', '12', '08', '06', '11', '10'], expected ['11']
- **Q54** (paraphrase, expect=answer): Ví có tính tiền hằng tháng để giữ tài khoản không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['02', '05', '07', '03', '11', '02'], expected ['02']

## model_abstained_with_evidence (2)

every key fact was in the passages but the model said it could not answer

- **Q38** (paraphrase, expect=answer): Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['06', '05', '12', '05', '12', '02'], expected ['02']
- **Q55** (paraphrase, expect=answer): Không dùng ví cả năm thì có sao không?
  - answer: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
  - why failed: abstained (model_found_no_answer) but should have answered; retrieved docs ['03', '02', '11', '10', '08', '02'], expected ['05']

## missing_key_facts (3)

answered from the right document but a key fact is missing from the answer

- **Q25** (no_diacritics, expect=answer): rut tien ve ngan hang co mat phi khong
  - answer: Có phí rút tiền, nhưng 3 lần đầu tiên mỗi tháng miễn phí. [1]
  - why failed: missing key facts: ['0,1%']; retrieved docs ['01', '02', '02', '01', '02', '10'], expected ['02']
- **Q43** (paraphrase, expect=answer): Có người gọi tự nhận là nhân viên ví và xin mã xác nhận gửi về điện thoại, mình nên làm gì?
  - answer: Không nên cung cấp mã OTP, vì nhân viên Ví Mây không bao giờ yêu cầu mã OTP. [1] Đây là dấu hiệu lừa đảo thường gặp. [2]
  - why failed: missing key facts: ['giả mạo']; retrieved docs ['06', '05', '01', '12', '12', '06'], expected ['06']
- **Q53** (paraphrase, expect=answer): Mình lỡ bấm nhầm số người nhận khi chuyển, có lấy lại được không?
  - answer: Có thể lấy lại nếu người nhận đồng ý và trong 3 ngày làm việc. [1] Không lấy lại nếu người nhận không đồng ý. [2] Cần báo trong 24h để Ví Mây tạm giữ…
  - why failed: missing key facts: ['không cam kết', '24 giờ']; retrieved docs ['12', '12', '08', '12', '12', '01'], expected ['12']
