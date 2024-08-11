1. 程式環境及框架：
    (1) python 版本：python 3.10
    (2) Vue.js 為 Vue 3 的 Options API 方式進行撰寫，主要是先前都以 Vue 2 的框架進行開發。 

2. 所需套件：
    sqlalchemy
    fastapi
    datetime
    pydantic

3. 資料庫連線及表格：
    (1) 需更改 /backend/database.py 的第5行 URL_DATABASE = 'postgresql://postgres:PASSWORD@localhost:5432/USERNAME'
    (2) 會自動在資料庫生成兩個 Table。第一個Table為 "Users"，儲存ID、姓名、E-mail及註冊日期。第二個Table為 "ConfirmUsers"，儲存ID、E-mail及密碼（經過Hash加密）

4. JWT 時效過期：
    時效設定在 /backend/main.py 的第35行 ACCESS_TOKEN_EXPIRE_MINUTES = 1，設定時間為1分鐘。

5. 登入及註冊：
    (1) 在註冊時，會先將用戶的密碼經過加密後，儲存至 "ConfirmUsers" 的Table裡面。
    (2) 登入後網頁自動跳轉至 "127.0.0.1:8000/docs"，並將後端認證後的資料儲存至LocalStorage。

6. API 測試
    (1) 測試網址為 "127.0.0.1:8000/docs"
    (2) 須先登入....才可使用查詢、刪除、更改等API功能，否則會回傳。
    (3) 更改API目前只設定修改用戶姓名，其餘資料無法修改。 
    
