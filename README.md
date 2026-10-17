# World Bank 全球面量圖探索器

這是一個給教材教法工作坊使用的 Streamlit 範例。使用者可以選擇 World Bank 指標與年份，程式會自動向 World Bank Indicators API 取得資料，並繪製互動式全球面量圖。

## 功能

- 選擇人口、GDP、預期壽命、網路使用率或二氧化碳排放指標
- 選擇年份與色階
- 自動取得 World Bank API 資料
- 繪製 Plotly 互動式世界面量圖
- 查看原始資料與基本統計量
- 下載目前資料為 CSV

## 本機執行

先安裝套件：

```bash
pip install -r requirements.txt
```

再啟動 Streamlit：

```bash
streamlit run app.py
```

瀏覽器通常會自動開啟：

```text
http://localhost:8501
```

## GitHub＋Streamlit Community Cloud 部署

1. 在 GitHub 建立新的 repository。
2. 上傳 `app.py`、`requirements.txt` 與 `README.md`。
3. 開啟 Streamlit Community Cloud。
4. 選擇 GitHub repository、branch 與 `app.py`。
5. 按下 Deploy。

本範例不需要 API key。World Bank API 的請求網址與資料欄位可參考：

<https://datahelpdesk.worldbank.org/knowledgebase/articles/889392>

## 給學生的 AI 任務

請不要只要求 AI「幫我寫一個地圖程式」。可以依照以下順序逐步修改：

1. 請說明這個 Streamlit 程式的資料流程。
2. 請新增「能源使用」或其他 World Bank 指標。
3. 請讓使用者可以輸入 World Bank indicator code。
4. 請新增年份動畫或年份比較功能。
5. 請加入資料缺漏值提醒。
6. 請檢查國家代碼與面量圖的對應是否正確。
7. 請說明這張圖可以支持哪些地理解釋，不能支持哪些結論。

## 重要地理與資料素養提醒

- 面量圖的顏色不是地理解釋本身。
- 平均值可能掩蓋國家內部差異。
- 不同分類方法可能產生不同的視覺效果。
- World Bank API 的資料可能有缺漏值。
- 相關關係不能直接解釋為因果關係。
- 請在成果中標示資料來源、指標代碼與年份。
