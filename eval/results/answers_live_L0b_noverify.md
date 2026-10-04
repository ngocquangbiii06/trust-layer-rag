# End-to-end evaluation - openai-compat:openai/gpt-oss-20b - verifier OFF

Questions: 60. Passed: 49/60. Passages sent to the model per question: 6.

| Group | Passed |
|---|---|
| expect=abstain | 10/11 |
| expect=answer | 39/49 |
| kind=ambiguous | 1/1 |
| kind=injection | 2/2 |
| kind=multi_doc | 3/3 |
| kind=near_miss | 1/1 |
| kind=no_diacritics | 1/2 |
| kind=out_of_scope | 2/2 |
| kind=paraphrase | 11/20 |
| kind=pii | 2/2 |
| kind=plain | 20/20 |
| kind=unanswerable | 6/7 |

- Raw personal data reaching the model, the audit log or the cache: 0 of 2 values
- Claims removed by the verifier: 0
- Model replies: 60 from the cache, 0 live calls, 0 missing (a missing reply shows as an error below)
- Median model latency, as recorded: 2288 ms
- Median pipeline latency: 8 ms (replayed replies cost no model time)
- Tokens, from the replies that reported them: 40802 in, 19128 out

## Failures

- Q25 (no_diacritics): missing key facts: ['0,1%']. Q: rut tien ve ngan hang co mat phi khong A: Có phí rút tiền, nhưng 3 lần đầu tiên mỗi tháng miễn phí. [1]
- Q29 (unanswerable): answered but should have abstained. Q: Bị phạt bao nhiêu tiền nếu nhập sai OTP nhiều lần? A: Không có phạt tiền, chỉ cần chờ 24 giờ rồi thử lại. [1]
- Q38 (paraphrase): abstained (model_found_no_answer) but should have answered. Q: Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không? A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
- Q41 (paraphrase): missing key facts: ['15 phút']. Q: Chụp giấy tờ xong thì bao lâu mới biết kết quả? A: Kết quả xác minh tài khoản thường được biết trong vòng 24 giờ. [1]
- Q42 (paraphrase): abstained (model_found_no_answer) but should have answered. Q: Tại sao ảnh căn cước của mình bị trả lại? A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
- Q43 (paraphrase): missing key facts: ['giả mạo']. Q: Có người gọi tự nhận là nhân viên ví và xin mã xác nhận gửi về điện thoại, mình nên làm gì? A: Không nên cung cấp mã OTP, vì nhân viên Ví Mây không bao giờ yêu cầu mã OTP. [1] Đây là dấu hiệu lừa đảo thường gặp. [2]
- Q51 (paraphrase): missing key facts: ['bằng 0']. Q: Mình không dùng ví nữa thì hủy ví bằng cách nào? A: Rút hoặc chuyển hết số dư về ngân hàng đã liên kết. Vào Cài đặt, chọn Đóng tài khoản và xác nhận bằng khuôn mặt. [1]
- Q52 (paraphrase): missing key facts: ['30 ngày']. Q: Mã giảm giá để lâu quá có bị mất không? A: Voucher đã hết hạn không được cấp lại. [1]
- Q53 (paraphrase): missing key facts: ['không cam kết', '24 giờ']. Q: Mình lỡ bấm nhầm số người nhận khi chuyển, có lấy lại được không? A: Có thể lấy lại nếu người nhận đồng ý và trong 3 ngày làm việc. [1] Không lấy lại nếu người nhận không đồng ý. [2] Cần báo trong 24h để Ví Mây tạm giữ. [3]
- Q54 (paraphrase): abstained (model_found_no_answer) but should have answered. Q: Ví có tính tiền hằng tháng để giữ tài khoản không? A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
- Q55 (paraphrase): abstained (model_found_no_answer) but should have answered. Q: Không dùng ví cả năm thì có sao không? A: Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này.
