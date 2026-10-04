# Verifier on versus off - L0b - openai-compat:openai/gpt-oss-20b

Both runs judge the same recorded model replies, so the model is not called again.

| | Passed |
|---|---|
| verifier on | 45/60 |
| verifier off | 48/60 |

Question by question: 45 pass either way, 12 fail either way, **0 pass only with the verifier**, **3 pass only without it**.

Claims: the model produced 56, the verifier kept 48 and removed 8. Removal reasons: quote_not_in_source 4, claim_not_supported_by_quote 3, number_not_in_quote 1.

What the user got:

| Outcome | on | off | Meaning |
|---|---|---|---|
| answered_correctly | 36 | 39 | answered, every key fact present |
| answered_incorrectly | 5 | 6 | answered, but a key fact is missing or a forbidden claim appears |
| abstained_wrongly | 8 | 4 | declined a question the documents can answer |
| abstained_correctly | 9 | 9 | declined a question the documents cannot answer |
| answered_should_abstain | 1 | 1 | answered a question the documents cannot answer |
| error | 1 | 1 | the call failed |

| Kind | on | off |
|---|---|---|
| ambiguous | 1/1 | 1/1 |
| injection | 1/2 | 1/2 |
| multi_doc | 2/3 | 3/3 |
| near_miss | 1/1 | 1/1 |
| no_diacritics | 1/2 | 1/2 |
| out_of_scope | 2/2 | 2/2 |
| paraphrase | 9/20 | 11/20 |
| pii | 2/2 | 2/2 |
| plain | 20/20 | 20/20 |
| unanswerable | 6/7 | 6/7 |

## Passed only with the verifier (it caught something)

- none

## Passed only without the verifier (it removed something it should have kept)

- Q22 (multi_doc): Nếu tôi bị lừa chuyển tiền thì Ví Mây có chắc chắn lấy lại được không, và việc đầu tiên tôi nên làm là gì?
  - removed [quote_not_in_source]: "Khóa ví ngay trong mục Bảo mật của ứng dụng. Báo cáo qua mục Hỗ trợ, chọn 'Báo cáo lừa đảo'."
- Q46 (paraphrase): Mình ghi sai tên chủ tài khoản thì liên kết ngân hàng có được không?
  - removed [claim_not_supported_by_quote]: "Không được liên kết nếu tên không trùng khớp."
  - removed [claim_not_supported_by_quote]: "Tên không trùng khớp sẽ gây lỗi liên kết."
- Q50 (paraphrase): Mình muốn xóa hết dữ liệu cá nhân, mất bao lâu và có xóa được tất cả không?
  - removed [number_not_in_quote]: "Dữ liệu giao dịch không thể xóa trước hết thời hạn lưu, vì phải lưu trữ tối thiểu 10 năm."

## Every claim the verifier removed

Listed so a person can judge each removal; the pass/fail numbers cannot.

- Q22 (failed) [quote_not_in_source] claim "Khóa ví ngay trong mục Bảo mật của ứng dụng. Báo cáo qua mục Hỗ trợ, chọn 'Báo cáo lừa đảo'." | quote "Khóa ví ngay trong mục Bảo mật của ứng dụng. Báo cáo qua mục Hỗ trợ, chọn "Báo cáo lừa đảo"."
- Q25 (failed) [quote_not_in_source] claim "Có phí rút tiền, nhưng 3 lần đầu tiên mỗi tháng miễn phí." | quote "Phí 0,1% giá trị giao dịch, tối thiểu 1.000 đồng và tối đa 10.000 đồng. Mỗi tháng được miễn phí 3 lần rút đầu tiên. Từ …"
- Q41 (failed) [claim_not_supported_by_quote] claim "Kết quả xác minh tài khoản thường được biết trong vòng 24 giờ." | quote "Mỗi tài khoản được thử lại tối đa 5 lần trong 24 giờ. Quá số lần này, tài khoản phải chờ 24 giờ mới được thử tiếp."
- Q43 (failed) [quote_not_in_source] claim "Đây là dấu hiệu lừa đảo thường gặp." | quote "Cuộc gọi tự xưng nhân viên Ví Mây báo 'tài khoản bị khóa' và yêu cầu đọc mã OTP."
- Q46 (failed) [claim_not_supported_by_quote] claim "Không được liên kết nếu tên không trùng khớp." | quote "Tên chủ tài khoản ngân hàng phải trùng tên đã xác thực trên Ví Mây."
- Q46 (failed) [claim_not_supported_by_quote] claim "Tên không trùng khớp sẽ gây lỗi liên kết." | quote "Tên không trùng khớp: kiểm tra lại họ tên trên cả hai nơi."
- Q50 (failed) [number_not_in_quote] claim "Dữ liệu giao dịch không thể xóa trước hết thời hạn lưu, vì phải lưu trữ tối thiểu 10 năm." | quote "Người dùng có thể yêu cầu xem, sửa hoặc xóa dữ liệu. Yêu cầu được xử lý trong 30 ngày. Dữ liệu giao dịch thuộc diện bắt…"
- Q51 (failed) [quote_not_in_source] claim "Rút hoặc chuyển hết số dư về ngân hàng đã liên kết. Vào Cài đặt, chọn Đóng tài khoản và xác nhận bằng khuôn mặt." | quote "Rút hoặc chuyển hết số dư về ngân hàng đã liên kết. Vào Cài đặt, chọn Đóng tài khoản và xác nhận bằng khuôn mặt."
