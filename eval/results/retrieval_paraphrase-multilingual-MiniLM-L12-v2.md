# Retrieval evaluation - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Chunks: 49. Scored questions: 49 (expect == answer).

| Mode | any@1 | any@3 | any@5 | all@3 | all@5 |
|---|---|---|---|---|---|
| dense | 30/49 | 39/49 | 41/49 | 38/49 | 41/49 |
| bm25 | 32/49 | 45/49 | 45/49 | 45/49 | 45/49 |
| hybrid | 33/49 | 43/49 | 47/49 | 43/49 | 47/49 |

## any@3 by question kind

| Kind | dense | bm25 | hybrid |
|---|---|---|---|
| ambiguous | 1/1 | 1/1 | 1/1 |
| injection | 1/1 | 1/1 | 1/1 |
| multi_doc | 2/3 | 3/3 | 3/3 |
| no_diacritics | 1/2 | 2/2 | 2/2 |
| paraphrase | 14/20 | 16/20 | 14/20 |
| pii | 1/2 | 2/2 | 2/2 |
| plain | 19/20 | 20/20 | 20/20 |

## Misses at k=3

**dense**
- Q16 expected ['08'], got ['03', '04', '09']: Điểm hoàn có hiệu lực trong bao lâu?
- Q22 expected ['06'], got ['02', '01', '03']: Nếu tôi bị lừa chuyển tiền thì Ví Mây có chắc chắn lấy lại được không, và việc đầu tiên tôi nên làm là gì?
- Q24 expected ['01'], got ['02', '07', '11']: han muc giao dich moi ngay cua tai khoan cap 2 la bao nhieu
- Q34 expected ['04'], got ['12', '07', '09']: CCCD của tôi là 079012345678, tôi cần làm gì để xác thực danh tính?
- Q36 expected ['05'], got ['07', '06', '03']: Em gõ sai mật mã giao dịch liên tục thì ví có tự đóng băng không, bao giờ dùng lại được?
- Q42 expected ['04'], got ['01', '11', '11']: Tại sao ảnh căn cước của mình bị trả lại?
- Q49 expected ['09'], got ['06', '12', '01']: Ví có bán thông tin của mình cho bên thứ ba không?
- Q51 expected ['10'], got ['03', '02', '11']: Mình không dùng ví nữa thì hủy ví bằng cách nào?
- Q52 expected ['11'], got ['03', '09', '08']: Mã giảm giá để lâu quá có bị mất không?
- Q55 expected ['05'], got ['03', '02', '11']: Không dùng ví cả năm thì có sao không?

**bm25**
- Q38 expected ['02'], got ['08', '06', '05']: Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không?
- Q47 expected ['08'], got ['07', '01', '04']: Quét mã trả tiền ở quán cà phê thì tối đa bao nhiêu một lần với tài khoản đã xác thực căn cước?
- Q51 expected ['10'], got ['05', '05', '09']: Mình không dùng ví nữa thì hủy ví bằng cách nào?
- Q52 expected ['11'], got ['06', '05', '05']: Mã giảm giá để lâu quá có bị mất không?

**hybrid**
- Q36 expected ['05'], got ['06', '10', '07']: Em gõ sai mật mã giao dịch liên tục thì ví có tự đóng băng không, bao giờ dùng lại được?
- Q38 expected ['02'], got ['06', '05', '12']: Có bị trừ thêm tiền khi mình chuyển cho người dùng khác cùng ứng dụng không?
- Q49 expected ['09'], got ['06', '01', '04']: Ví có bán thông tin của mình cho bên thứ ba không?
- Q51 expected ['10'], got ['03', '07', '11']: Mình không dùng ví nữa thì hủy ví bằng cách nào?
- Q52 expected ['11'], got ['03', '12', '08']: Mã giảm giá để lâu quá có bị mất không?
- Q55 expected ['05'], got ['03', '02', '10']: Không dùng ví cả năm thì có sao không?
