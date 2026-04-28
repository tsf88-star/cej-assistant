import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import io

# ──────────────────────────────────────────
# [1] 앱 설정 및 스타일링
# ──────────────────────────────────────────
st.set_page_config(page_title="CEJ Submission Assistant", layout="wide", page_icon="🧪")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 32px; font-weight: 700; color: #1E293B; margin-bottom: 5px; }
    .sub-header { font-size: 16px; color: #64748B; margin-bottom: 30px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #F8FAFC; border-radius: 8px 8px 0 0; 
        padding: 0 25px; font-weight: 600; color: #475569;
    }
    .stTabs [aria-selected="true"] { background-color: #0F172A !important; color: white !important; }
    .prompt-box { background-color: #F1F5F9; border-radius: 12px; padding: 20px; border-left: 5px solid #3B82F6; margin: 15px 0; }
    .feature-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🧪 CEJ Submission Assistant (Si/Gr-PSSA)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Chemical Engineering Journal 투고를 위한 논리 검증 및 딥 메커니즘 분석 도구</div>', unsafe_allow_html=True)

tabs = st.tabs(["🧐 Virtual Reviewer", "📊 Mechanism Analysis", "✍️ Technical Polish"])

# ──────────────────────────────────────────
# [Tab 1] CEJ 가상 리뷰어 (프롬프트 제너레이터)
# ──────────────────────────────────────────
with tabs[0]:
    st.header("🧐 CEJ Virtual Reviewer Simulator")
    st.info("현재까지의 가설과 실험 데이터를 기반으로 CEJ 리뷰어의 예상 질문을 생성합니다.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        hypothesis = st.text_area("1. 연구의 핵심 가설 (Hypothesis)", placeholder="예: 0.5wt% PSSA 첨가가 Si/Gr 음극의 SEI 층을 안정화시키고 리튬 이온 flux를 균일하게 만든다.")
        findings = st.text_area("2. 주요 실험 결과 (Key Findings)", placeholder="예: PSSA 첨가 시 사이클 성능 20% 향상, CV 분석 결과 Capacitive 기여도 증가 확인.")
        mechanisms = st.text_area("3. 주장하는 메커니즘 (Proposed Mechanism)", placeholder="예: PSSA의 Sulfonate group이 Li+과 상호작용하여 고체 전해질 계면의 저항을 낮춤.")
    
    with col2:
        st.markdown("### 🤖 Generated Reviewer Prompt")
        if st.button("초정밀 리뷰 프롬프트 생성"):
            full_prompt = f"""
당신은 Chemical Engineering Journal (CEJ)의 시니어 에디터이자 이차전지 분야의 엄격한 리뷰어입니다. 
다음 연구 요약을 읽고, CEJ 게재 수준에 도달하기 위해 보완해야 할 점을 비판적으로 분석하십시오.

[연구 요약]
- 주제: Si/Gr 복합 음극 내 0.5wt% PSSA 슬러리 첨가제 연구
- 핵심 가설: {hypothesis}
- 주요 결과: {findings}
- 메커니즘: {mechanisms}

[리뷰 가이드라인]
1. 논리적 결함: 가설과 결과 사이의 연결 고리가 약한 부분을 지적하십시오.
2. 메커니즘 깊이: 단순 성능 나열을 넘어, 화학 공학적 관점에서의 메커니즘 증명이 충분한지 검토하십시오.
3. 추가 실험 제안: 리뷰어로서 논문을 Reject 시키지 않기 위해 필수로 요구할 만한 추가 분석(예: XPS, TEM, EIS fitting 등)을 제안하십시오.

답변은 한국어로 상세히 작성해 주십시오.
            """
            st.code(full_prompt, language="markdown")
            st.success("위 프롬프트를 복사하여 ChatGPT나 Claude에 붙여넣으세요!")

# ──────────────────────────────────────────
# [Tab 2] 딥 메커니즘 분석기 (b-value & Contribution)
# ──────────────────────────────────────────
with tabs[1]:
    st.header("📊 Deep Kinetics Analysis (CV)")
    st.markdown("CV 데이터를 업로드하여 b-value와 용량 기여도(Capacitive vs. Diffusion)를 분석합니다.")
    
    uploaded_file = st.file_uploader("CV 엑셀/CSV 파일 업로드 (Voltage, Current 쌍)", type=["xlsx", "csv"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            st.write("데이터 프리뷰 (상위 5행):")
            st.dataframe(df.head())
            
            # 분석 파라미터 설정
            st.divider()
            st.subheader("⚙️ Analysis Settings")
            scan_rates_str = st.text_input("Scan Rates (mV/s, 콤마로 구분)", "0.1, 0.2, 0.5, 1.0, 2.0")
            scan_rates = [float(x.strip()) for x in scan_rates_str.split(",")]
            
            if st.button("Kinetics 분석 실행"):
                # b-value 계산 로직 (임시: 2번, 4번, 6번... 열이 전류라고 가정)
                # 실제 데이터 구조에 맞게 슬라이싱 필요 (Unnamed: 2, 4, 6, 8, 10 등)
                current_cols = df.iloc[:, [2, 4, 6, 8, 10]].max() # 피크 전류 추출 (간소화)
                log_v = np.log10(scan_rates)
                log_i = np.log10(current_cols.values)
                
                slope, intercept, r_value, p_value, std_err = stats.linregress(log_v, log_i)
                
                c1, c2 = st.columns(2)
                with c1:
                    fig_b = go.Figure()
                    fig_b.add_trace(go.Scatter(x=log_v, y=log_i, mode='markers', name='Data Points', marker=dict(size=12, color='#0054FF')))
                    fig_b.add_trace(go.Scatter(x=log_v, y=intercept + slope*log_v, mode='lines', name=f'Fitting (b={slope:.2f})', line=dict(color='#EF4444', dash='dash')))
                    fig_b.update_layout(title="b-value Analysis (log i vs log v)", xaxis_title="log(Scan rate, V/s)", yaxis_title="log(Peak current, A)", template="plotly_white")
                    st.plotly_chart(fig_b, use_container_width=True)
                    st.metric("Calculated b-value", f"{slope:.3f}", delta=f"R²={r_value**2:.4f}")

                with c2:
                    # 기여도 분석 (간소화된 예시)
                    # i = k1*v + k2*v^0.5 -> i/v^0.5 = k1*v^0.5 + k2
                    v_half = np.sqrt(scan_rates)
                    i_v_half = current_cols.values / v_half
                    k1, k2, _, _, _ = stats.linregress(v_half, i_v_half)
                    
                    contributions = []
                    for v in scan_rates:
                        cap = k1 * v
                        diff = k2 * np.sqrt(v)
                        total = cap + diff
                        contributions.append([cap/total*100, diff/total*100])
                    
                    labels = [f"{v} mV/s" for v in scan_rates]
                    cap_vals = [c[0] for c in contributions]
                    diff_vals = [c[1] for c in contributions]
                    
                    fig_cont = go.Figure(data=[
                        go.Bar(name='Capacitive', x=labels, y=cap_vals, marker_color='#3B82F6'),
                        go.Bar(name='Diffusion-controlled', x=labels, y=diff_vals, marker_color='#94A3B8')
                    ])
                    fig_cont.update_layout(barmode='stack', title="Pseudocapacitive Contribution", yaxis_title="Contribution (%)", template="plotly_white")
                    st.plotly_chart(fig_cont, use_container_width=True)
                    
                st.success("✅ 메커니즘 분석 완료. 그래프를 우클릭하여 저장하거나 논문에 활용하세요.")
        except Exception as e:
            st.error(f"파일 분석 중 오류 발생: {e}")

# ──────────────────────────────────────────
# [Tab 3] 테크니컬 프루프리더 (영문 교정)
# ──────────────────────────────────────────
with tabs[2]:
    st.header("✍️ Visual & Technical Proofreader")
    st.markdown("논문의 문장 수준을 CEJ급으로 끌어올리고 Figure 통일성을 점검합니다.")
    
    raw_text = st.text_area("교정할 영문 단락 입력", height=200, placeholder="Improve the performance of Si anode by adding PSSA...")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("📏 CEJ Figure Checklist")
        st.checkbox("폰트 크기 통일 (8-10pt 추천)")
        st.checkbox("반복 실험 오차 막대(Error bar) 포함")
        st.checkbox("모든 축에 단위(Unit) 명시")
        st.checkbox("스케일 바(Scale bar) 가독성 확인 (SEM/TEM)")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_p2:
        if st.button("테크니컬 교정 프롬프트 생성"):
            proof_prompt = f"""
당신은 이차전지 분야 세계 최고의 저널(Nature Energy, AM, CEJ) 전문 에디터입니다. 
다음 영문 텍스트를 고수준의 학술적 표현으로 교정하십시오.

[수정 원칙]
1. 단어 선택: 'show' -> 'exhibit/demonstrate', 'improve' -> 'enhance', 'deterioration' -> 'degradation' 등 전문 용어 사용.
2. 문장 구조: 간결하면서도 논리적인 인과 관계가 명확한 수동태/능동태 적절히 혼용.
3. 분야 특화: Si 음극의 부피 팽창, SEI 형성, 이온 전도성 등 전지 분야 관습적 표현 최적화.

[원본 텍스트]
{raw_text}

수정된 버전과 수정 이유(Key Improvements)를 한국어로 설명해 주십시오.
            """
            st.code(proof_prompt, language="markdown")
            st.success("프롬프트를 복사하여 AI 서비스에 입력하세요.")

st.divider()
st.caption("CEJ Submission Assistant v1.0 | Built for Si/Gr-PSSA Project")
