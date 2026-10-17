from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(
    page_title="World Bank Global Map",
    page_icon="🌍",
    layout="wide",
)


INDICATORS = {
    "人口總數（人）": "SP.POP.TOTL",
    "GDP per capita（現價美元）": "NY.GDP.PCAP.CD",
    "預期壽命（歲）": "SP.DYN.LE00.IN",
    "網路使用率（%）": "IT.NET.USER.ZS",
    "人均二氧化碳排放量（公噸）": "EN.ATM.CO2E.PC",
}

INDICATOR_LAST_YEARS = {
    "EN.ATM.CO2E.PC": 2020,
}

COLOR_SCALES = {
    "黃－紅": "YlOrRd",
    "藍－綠": "GnBu",
    "紫－黃": "Purples",
    "藍－紅": "RdBu",
}

COLOR_MODES = {
    "線性分布（原始數值）": "linear",
    "對數分布（適合人口與 GDP）": "log",
    "五級分組（適合地圖判讀）": "quantile",
}


@st.cache_data(ttl=3600)
def fetch_world_bank_data(indicator_code: str, year: int) -> pd.DataFrame:
    """取得指定 World Bank 指標與年份的國家資料。"""
    url = (
        "https://api.worldbank.org/v2/country/all/"
        f"indicator/{indicator_code}"
        f"?date={year}&format=json&per_page=400&source=2"
    )

    last_error = None
    for attempt in range(2):
        try:
            response = requests.get(
                url,
                timeout=(15, 90),
                headers={"User-Agent": "WorldBank-Map-Workshop/1.0"},
            )
            response.raise_for_status()
            break
        except requests.RequestException as error:
            last_error = error
            if attempt == 1:
                raise last_error
    payload = response.json()

    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(
            f"World Bank API 沒有回傳可用資料（指標：{indicator_code}，年份：{year}）。"
        )

    df = pd.DataFrame(payload[1])
    if df.empty:
        raise ValueError(
            f"這個指標在所選年份沒有資料（指標：{indicator_code}，年份：{year}）。"
        )

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value", "countryiso3code"])

    # World Bank API 的 region 欄位在不同回應版本中可能是字典或文字。
    # 只排除區域加總資料，避免因欄位格式不同而誤刪除所有國家。
    if "region" in df.columns:
        region_values = df["region"].apply(
            lambda item: item.get("value")
            if isinstance(item, dict)
            else str(item)
        )
        df = df[region_values != "Aggregates"]

    if df.empty:
        raise ValueError(
            f"這個指標在所選年份沒有可繪製的國家資料（指標：{indicator_code}，年份：{year}）。"
        )

    # World Bank API 的 country 欄位通常是字典，先轉成可顯示的國家名稱文字。
    df["country"] = df["country"].apply(
        lambda item: item.get("value")
        if isinstance(item, dict)
        else str(item)
    )

    return df[["country", "countryiso3code", "date", "value"]].rename(
        columns={
            "country": "國家",
            "countryiso3code": "ISO3",
            "date": "年份",
            "value": "數值",
        }
    )


def format_value(value: float) -> str:
    if pd.isna(value):
        return "無資料"
    if abs(value) >= 1_000_000:
        return f"{value:,.0f}"
    if abs(value) >= 100:
        return f"{value:,.1f}"
    return f"{value:,.2f}"


st.title("🌍 World Bank 全球面量圖探索器")
st.caption("利用 World Bank Indicators API，自動取得資料並繪製互動式世界地圖。")

with st.sidebar:
    st.header("地圖設定")

    indicator_name = st.selectbox("選擇指標", list(INDICATORS.keys()))
    indicator_code = INDICATORS[indicator_name]

    latest_year = INDICATOR_LAST_YEARS.get(indicator_code, datetime.now().year)
    default_year = min(2022, latest_year)

    year = st.slider(
        "選擇年份",
        min_value=1960,
        max_value=latest_year,
        value=default_year,
    )

    color_name = st.selectbox("選擇色階", list(COLOR_SCALES.keys()))
    color_scale = COLOR_SCALES[color_name]

    color_mode_name = st.selectbox(
        "選擇數值呈現方式",
        list(COLOR_MODES.keys()),
        index=1,
        help="人口與 GDP 的國家差距很大，使用對數分布通常比較容易看出空間差異。",
    )
    color_mode = COLOR_MODES[color_mode_name]

    st.divider()
    st.markdown("**目前使用的指標代碼**")
    st.code(indicator_code)
    st.markdown(
        "[查看 World Bank 指標資料庫](https://data.worldbank.org/indicator)"
    )

try:
    with st.spinner("正在向 World Bank 取得資料……"):
        data = fetch_world_bank_data(indicator_code, year)

    map_data = data.copy()

    if color_mode == "log":
        # 對數轉換可以避免少數極大值壓縮其他國家的顏色差異。
        map_data["繪圖值"] = np.log10(map_data["數值"].clip(lower=1))
        color_label = f"log10（{indicator_name}）"
        fig = px.choropleth(
            map_data,
            locations="ISO3",
            color="繪圖值",
            hover_name="國家",
            hover_data={"ISO3": True, "數值": ":,.2f", "繪圖值": False},
            color_continuous_scale=color_scale,
            projection="natural earth",
            labels={"繪圖值": color_label},
            title=f"{year} 年各國{indicator_name}（對數分布）",
        )
    elif color_mode == "quantile":
        map_data["分組"] = pd.qcut(
            map_data["數值"].rank(method="first"),
            q=5,
            labels=["第 1 級（低）", "第 2 級", "第 3 級", "第 4 級", "第 5 級（高）"],
        )
        fig = px.choropleth(
            map_data,
            locations="ISO3",
            color="分組",
            hover_name="國家",
            hover_data={"ISO3": True, "數值": ":,.2f", "分組": True},
            color_discrete_sequence=px.colors.sequential.YlOrRd,
            category_orders={"分組": ["第 1 級（低）", "第 2 級", "第 3 級", "第 4 級", "第 5 級（高）"]},
            projection="natural earth",
            labels={"分組": "五級分組"},
            title=f"{year} 年各國{indicator_name}（五級分組）",
        )
    else:
        fig = px.choropleth(
            map_data,
            locations="ISO3",
            color="數值",
            hover_name="國家",
            hover_data={"ISO3": True, "數值": ":,.2f"},
            color_continuous_scale=color_scale,
            projection="natural earth",
            labels={"數值": indicator_name},
            title=f"{year} 年各國{indicator_name}（線性分布）",
        )
    fig.update_layout(
        margin={"r": 0, "t": 70, "l": 0, "b": 0},
        coloraxis_colorbar={"title": indicator_name},
    )

    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("有資料的國家／地區", f"{len(data)}")
    c2.metric("最高值", data.loc[data["數值"].idxmax(), "國家"])
    c3.metric("最低值", data.loc[data["數值"].idxmin(), "國家"])

    with st.expander("查看原始資料與統計摘要"):
        st.dataframe(
            data.sort_values("數值", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.write(
            {
                "平均值": format_value(data["數值"].mean()),
                "中位數": format_value(data["數值"].median()),
                "標準差": format_value(data["數值"].std()),
            }
        )

    csv_data = data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="下載目前資料 CSV",
        data=csv_data,
        file_name=f"world_bank_{indicator_code}_{year}.csv",
        mime="text/csv",
    )

    st.info(
        "地理探究提示：請不要只描述顏色。請檢查資料來源、年份、缺漏值、"
        "分類方式，以及這張圖能支持或不能支持哪些地理解釋。"
    )

except requests.RequestException as error:
    st.error(
        "無法在限定時間內連線 World Bank API。這通常是遠端 API 暫時忙碌或 "
        "Streamlit Cloud 網路逾時，請稍候重新整理頁面。"
    )
    with st.expander("技術資訊"):
        st.code(str(error))
except (ValueError, KeyError) as error:
    st.error(f"資料處理錯誤：{error}")

st.caption(
    "資料來源：World Bank Indicators API。最後更新時間以 World Bank API 為準。"
)
