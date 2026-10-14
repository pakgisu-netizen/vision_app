import pandas as pd
import plotly.express as px
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="제조 품질 현황 대시보드", page_icon="📊", layout="wide"
)

# 2. 화면 제목 및 부제
st.setTitle = st.title("제조 품질 현황 대시보드")
st.title("🏭 제조 품질 현황 대시보드")
st.markdown("AI 비전검사 PoC 준비를 위한 품질 데이터 모니터링")
st.markdown("---")


# 3. 기본 샘플 데이터 생성 함수 (CSV가 없을 때 사용)
@st.cache_data
def load_sample_data():
  data = {
      "inspection_date": [
          "2026-10-01",
          "2026-10-01",
          "2026-10-02",
          "2026-10-02",
          "2026-10-03",
          "2026-10-03",
          "2026-10-04",
          "2026-10-04",
          "2026-10-05",
          "2026-10-05",
          "2026-10-06",
          "2026-10-06",
      ],
      "product_id": [
          "P001",
          "P002",
          "P003",
          "P004",
          "P005",
          "P006",
          "P007",
          "P008",
          "P009",
          "P010",
          "P011",
          "P012",
      ],
      "result": [
          "OK",
          "NG",
          "OK",
          "NG",
          "OK",
          "OK",
          "NG",
          "OK",
          "NG",
          "OK",
          "OK",
          "NG",
      ],
      "defect_type": [
          "None",
          "Scratch",
          "None",
          "Crack",
          "None",
          "None",
          "Dent",
          "None",
          "Scratch",
          "None",
          "None",
          "Crack",
      ],
      "confidence": [
          0.98,
          0.91,
          0.96,
          0.88,
          0.99,
          0.97,
          0.85,
          0.95,
          0.89,
          0.99,
          0.96,
          0.87,
      ],
  }
  return pd.DataFrame(data)


# 4. 사이드바 - 파일 업로드 및 필터
st.sidebar.header("⚙️ 제어 및 필터")
uploaded_file = st.sidebar.file_uploader(
    "CSV 파일 업로드", type=["csv"]
)

if uploaded_file is not None:
  df = pd.read_csv(uploaded_file)
  st.sidebar.success("사용자 정의 CSV 파일이 로드되었습니다!")
else:
  df = load_sample_data()
  st.sidebar.info("기본 샘플 데이터를 사용 중입니다.")

# 날짜 형식 변환
df["inspection_date"] = pd.to_datetime(df["inspection_date"]).dt.date

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 데이터 필터")

# 날짜 필터
min_date = df["inspection_date"].min()
max_date = df["inspection_date"].max()
date_range = st.sidebar.date_input(
    "조회 기간 선택", [min_date, max_date], min_value=min_date, max_value=max_date
)

# 제품 필터
product_list = sorted(df["product_id"].unique().tolist())
selected_products = st.sidebar.multiselect(
    "제품 선택", product_list, default=product_list
)

# 검사 결과 필터
result_list = sorted(df["result"].unique().tolist())
selected_results = st.sidebar.multiselect(
    "검사 결과 선택", result_list, default=result_list
)

# 필터 적용
if len(date_range) == 2:
  start_date, end_date = date_range
  filtered_df = df[
      (df["inspection_date"] >= start_date)
      & (df["inspection_date"] <= end_date)
      & (df["product_id"].isin(selected_products))
      & (df["result"].isin(selected_results))
  ]
else:
  filtered_df = df[
      (df["product_id"].isin(selected_products))
      & (df["result"].isin(selected_results))
  ]

# 5. 상단 KPI 카드 영역
total_count = len(filtered_df)
ok_count = len(filtered_df[filtered_df["result"] == "OK"])
ng_count = len(filtered_df[filtered_df["result"] == "NG"])
defect_rate = (ng_count / total_count * 100) if total_count > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="전체 검사", value=f"{total_count} 건")
col2.metric(label="정상 (OK)", value=f"{ok_count} 건")
col3.metric(label="불량 (NG)", value=f"{ng_count} 건")
col4.metric(label="불량률", value=f"{defect_rate:.1f}%")

st.markdown("---")

# 6. 중단 - 그래프 영역 (2열 레이아웃)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
  st.subheader("📈 날짜별 검사 현황")
  if not filtered_df.empty:
    daily_df = (
        filtered_df.groupby(["inspection_date", "result"])
        .size()
        .reset_index(name="count")
    )
    fig_line = px.line(
        daily_df,
        x="inspection_date",
        y="count",
        color="result",
        markers=True,
        labels={
            "inspection_date": "검사 일자",
            "count": "건수",
            "result": "결과",
        },
    )
    st.plotly_chart(fig_line, use_container_width=True)
  else:
    st.warning("표시할 데이터가 없습니다.")

with chart_col2:
  st.subheader("📊 불량 유형별 건수")
  ng_df = filtered_df[
      (filtered_df["result"] == "NG")
      & (filtered_df["defect_type"] != "None")
  ]
  if not ng_df.empty:
    defect_counts = (
        ng_df["defect_type"].value_counts().reset_index()
    )
    defect_counts.columns = ["defect_type", "count"]
    fig_bar = px.bar(
        defect_counts,
        x="defect_type",
        y="count",
        color="defect_type",
        labels={"defect_type": "불량 유형", "count": "건수"},
    )
    st.plotly_chart(fig_bar, use_container_width=True)
  else:
    st.info("선택된 조건 내 불량 데이터가 없습니다.")

st.markdown("---")

# 7. 하단 - 최근 검사 결과 테이블
st.subheader("📋 최근 검사 결과 (최대 10건)")
if not filtered_df.empty:
  sorted_df = filtered_df.sort_values(by="inspection_date", ascending=False)
  st.dataframe(sorted_df.head(10), use_container_width=True)
else:
  st.warning("표시할 데이터가 없습니다.")