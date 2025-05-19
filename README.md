# 💻 Project: Object Image Editor

## 👨‍🎓 Thông tin sinh viên thực hiện
| STT | Họ và Tên               | MSSV        |
|-----|--------------------------|-------------|
| 1   | Trần Huỳnh Trung Hiếu    | N21DCCN122  |
| 2   | Nguyễn Thị Thanh Huyến   | N21DCCN130  |
| 3   | Nguyễn Thị Huyền My      | N21DCCN147  |
| 4   | Tô Phan Kiều Thương      | N21DCCN184  |


## 📘 Thông tin đề bài
As a project, develop a software package that implements the transform-ation-based approach to retrieval by similarity. In particular, your package must contain the following capabilities that can be encoded as functions:

(a) Develop a syntax in which transformation operators can be represented. Then develop a program, called TransformationLibraryManager, that takes as input, perhaps through a user interface or from a file, a transformation operator specified in your syntax, and appends it to the library through a TLMinsert routine. Similarly, write a TLMsearch routine that, given the name of an instantiated operator, will return an appropriately instantiated version of the operator.

(b) Develop a syntax in which cost functions can be represented. Then write a program, called CostFunctionServer, that has a Costinsert routine that takes as input, perhaps through a user interface or from a file, a cost function specified in your syntax, and appends it to a library of cost functions. CostFunctionServer must also have a function, called EvaluateCall, that takes an instantiated transformation operator as input and returns the cost of this operator as output, using the cost functions represented using your syntax.

(c) Develop a program, called ObjectConvertor, that takes two objects o1 and o2 as input and that uses TransformationLibraryManager and CostFunctionServer to construct a least-cost transformation sequence between o1 and o2.

(d) Demonstrate your system's operation using the simple example of transformation sequences in Figure below. In particular, specify all the operations for this example in your syntax, as well as all the cost functions.

## 📝 Mô tả chi tiết bài đã làm
Chương trình được xây dựng bằng ngôn ngữ **Python**, bao gồm các phần chính:
- `main.py` - File chính để chạy chương trình.
- `modules/` - Thư mục chứa các module xử lý riêng như [mô tả ngắn từng module nếu có].
- Giao diện sử dụng [Console/GUI/Web...], cho phép người dùng tương tác dễ dàng.

Các chức năng cụ thể:
- ✅ Cho phép người dùng nhập ...
- ✅ Tính toán và hiển thị ...
- ✅ Ghi kết quả ra file/hiển thị trực tiếp...

## ⚙️ Hướng dẫn cài đặt
Yêu cầu:
- Python >= 3.8
- Cài đặt thư viện phụ thuộc:

```bash
pip install -r requirements.txt
