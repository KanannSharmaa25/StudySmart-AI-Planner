# ================= IMPORTS =================
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="StudySmart AI Planner",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= DARK THEME =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    background-color: #0f172a;
    font-family: 'Inter', sans-serif;
    color: #e5e7eb;
}
[data-testid="stSidebar"] {
    background-color: #020617;
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
input, textarea {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    border: 1px solid #334155 !important;
}
.stDataFrame {
    background-color: #020617;
    border-radius: 12px;
    border: 1px solid #1e293b;
}
.stButton > button {
    background-color: #3b82f6;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.6rem 1.3rem;
}
.stButton > button:hover {
    background-color: #2563eb;
}
hr { border-color: #1e293b; }
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
DATA_PATH = "data/study_data.csv"
HISTORY_PATH = "data/confidence_history.csv"

try:
    plan = pd.read_csv(DATA_PATH)
    plan["Exam_Date"] = pd.to_datetime(plan["Exam_Date"])
except:
    plan = pd.DataFrame(columns=[
        "Subject", "Exam_Date", "Daily_Hours", "Confidence", "Added_On"
    ])

try:
    history = pd.read_csv(HISTORY_PATH)
    history["Date"] = pd.to_datetime(history["Date"])
except:
    history = pd.DataFrame(columns=["Date", "Subject", "Confidence"])

# ================= SIDEBAR =================
with st.sidebar:
    st.header("📘 StudySmart")
    st.caption("Smarter planning. Less burnout.")
    st.divider()

    mode = st.radio("Mode", ["➕ Add Subject", "✏️ Edit / Delete Subject"])

    if mode == "➕ Add Subject":
        subject = st.text_input("Subject name")
        exam_date = st.date_input("Exam date")
        daily_hours = st.slider("Daily study hours", 1, 10, 2)
        confidence = st.slider("Confidence level", 1, 5, 3)

        if st.button("Add Subject"):
            if subject.strip():
                plan = pd.concat([plan, pd.DataFrame([{
                    "Subject": subject,
                    "Exam_Date": exam_date,
                    "Daily_Hours": daily_hours,
                    "Confidence": confidence,
                    "Added_On": datetime.now()
                }])], ignore_index=True)

                history = pd.concat([history, pd.DataFrame([{
                    "Date": datetime.now(),
                    "Subject": subject,
                    "Confidence": confidence
                }])], ignore_index=True)

                plan.to_csv(DATA_PATH, index=False)
                history.to_csv(HISTORY_PATH, index=False)
                st.success("Subject added")
                st.rerun()

    else:
        if not plan.empty:
            selected = st.selectbox("Select subject", plan["Subject"])
            row = plan[plan["Subject"] == selected].iloc[0]

            exam_date = st.date_input("Exam date", row["Exam_Date"])
            daily_hours = st.slider("Daily study hours", 1, 10, int(row["Daily_Hours"]))
            confidence = st.slider("Confidence level", 1, 5, int(row["Confidence"]))

            if st.button("Update"):
                plan.loc[plan["Subject"] == selected,
                         ["Exam_Date", "Daily_Hours", "Confidence"]] = \
                    [exam_date, daily_hours, confidence]

                history = pd.concat([history, pd.DataFrame([{
                    "Date": datetime.now(),
                    "Subject": selected,
                    "Confidence": confidence
                }])], ignore_index=True)

                plan.to_csv(DATA_PATH, index=False)
                history.to_csv(HISTORY_PATH, index=False)
                st.success("Updated")
                st.rerun()

            if st.button("Delete"):
                plan = plan[plan["Subject"] != selected]
                plan.to_csv(DATA_PATH, index=False)
                st.warning("Deleted")
                st.rerun()

# ================= MAIN =================
st.title("📘 StudySmart AI Planner")
st.caption("Adaptive study intelligence")
st.divider()

if plan.empty:
    st.info("Add subjects to begin.")
    st.stop()

# ================= CORE CALCULATIONS =================
today = pd.to_datetime("today")
plan["Days_Left"] = (plan["Exam_Date"] - today).dt.days.clip(lower=1)

plan["Risk_Score"] = (
    (1 / plan["Days_Left"]) * 0.5 +
    ((6 - plan["Confidence"]) / 5) * 0.3 +
    (plan["Daily_Hours"] / plan["Daily_Hours"].max()) * 0.2
)

plan["Risk_Level"] = pd.cut(
    plan["Risk_Score"],
    bins=[-1, 0.35, 0.6, 2],
    labels=["🟢 Low Risk", "🟡 Medium Risk", "🔴 High Risk"]
)

# ================= BURNOUT RISK =================
burnout_scores = []
for _, r in plan.iterrows():
    overload = min(r["Daily_Hours"] / 8, 1)
    burnout_scores.append(
        overload * 0.5 + r["Risk_Score"] * 0.5
    )

plan["Burnout_Score"] = burnout_scores
plan["Burnout_Risk"] = pd.cut(
    plan["Burnout_Score"],
    bins=[-1, 0.4, 0.65, 2],
    labels=["🟢 Low", "🟡 Medium", "🔴 High"]
)

# ================= TODAY PLAN =================
st.header("📅 Today’s Study Plan")
total_hours = st.slider("Available study hours today", 1, 12, 4)

plan["Priority"] = plan["Risk_Score"] / plan["Risk_Score"].sum()
plan["Study_Hours_Today"] = (plan["Priority"] * total_hours).round(2)

st.dataframe(
    plan[["Subject", "Study_Hours_Today", "Risk_Level", "Burnout_Risk"]],
    use_container_width=True
)

# ================= 5A CONFIDENCE TREND =================
st.divider()
st.header("📈 Confidence Trend Analysis")

choice = st.selectbox("Select subject", plan["Subject"].unique())
sub_hist = history[history["Subject"] == choice].sort_values("Date")

if len(sub_hist) < 2:
    st.info("Not enough confidence data yet.")
else:
    st.line_chart(sub_hist.set_index("Date")["Confidence"])

# ================= 5B EXAM READINESS =================
st.divider()
st.header("🎯 Exam Readiness Score")

max_days = plan["Days_Left"].max()
max_hours = plan["Daily_Hours"].max()

plan["Readiness_Score"] = (
    (plan["Confidence"] / 5) * 0.35 +
    (1 - plan["Days_Left"] / max_days) * 0.3 +
    (plan["Daily_Hours"] / max_hours) * 0.2 +
    (1 - plan["Risk_Score"]) * 0.15
).round(2) * 100

plan["Readiness_Level"] = pd.cut(
    plan["Readiness_Score"],
    bins=[0, 40, 65, 85, 100],
    labels=["🔴 Not Ready", "🟠 Needs Work", "🟡 Almost Ready", "🟢 Exam Ready"]
)

st.dataframe(
    plan[["Subject", "Readiness_Score", "Readiness_Level"]],
    use_container_width=True
)

# ================= 5C SMART WEEKLY GOALS =================
st.divider()
st.header("📆 Smart Weekly Goals (AI Generated)")

weekly_hours = total_hours * 7

burnout_penalty = plan["Burnout_Risk"].map({
    "🔴 High": 0.7,
    "🟡 Medium": 0.85,
    "🟢 Low": 1.0
}).astype(float)

plan["Weekly_Priority"] = plan["Risk_Score"] * burnout_penalty
plan["Weekly_Priority"] /= plan["Weekly_Priority"].sum()

plan["Weekly_Target_Hours"] = (
    plan["Weekly_Priority"] * weekly_hours
).round(1)

st.dataframe(
    plan[["Subject", "Weekly_Target_Hours", "Risk_Level", "Burnout_Risk"]],
    use_container_width=True
)

st.caption("Weekly goals adapt automatically to risk and burnout.")

# ================= STEP 5D: WHAT-IF STUDY SIMULATOR =================
st.divider()
st.header("🔮 What-If Study Simulator")

st.caption(
    "Simulate how changing your daily study hours affects risk and readiness "
    "(this does NOT change your real data)."
)

# Select subject
sim_subject = st.selectbox(
    "Choose subject to simulate",
    plan["Subject"].unique(),
    key="whatif_subject"
)

row = plan[plan["Subject"] == sim_subject].iloc[0]

# Slider for hypothetical hours
sim_hours = st.slider(
    "What if you study this many hours per day?",
    1, 10,
    int(row["Daily_Hours"]),
    key="whatif_hours"
)

# ----- Recalculate simulated risk -----
sim_risk = (
    (1 / row["Days_Left"]) * 0.5 +
    ((6 - row["Confidence"]) / 5) * 0.3 +
    (sim_hours / plan["Daily_Hours"].max()) * 0.2
)

risk_change = sim_risk - row["Risk_Score"]

# ----- Display results -----
st.subheader("📊 Simulation Result")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Current Risk",
        round(row["Risk_Score"], 2)
    )

with col2:
    st.metric(
        "Simulated Risk",
        round(sim_risk, 2),
        delta=round(-risk_change, 2)
    )

with col3:
    percent = (risk_change / row["Risk_Score"]) * 100
    st.metric(
        "Risk Change %",
        f"{round(abs(percent), 1)}%",
        delta="↓" if risk_change < 0 else "↑"
    )

# ----- Interpretation -----
st.subheader("🧠 AI Interpretation")

if sim_risk < row["Risk_Score"] - 0.05:
    st.success(
        "Increasing your study hours meaningfully reduces risk. "
        "This is a good short-term strategy."
    )
elif sim_risk > row["Risk_Score"] + 0.05:
    st.warning(
        "Reducing study hours increases risk. "
        "Only do this if burnout is high."
    )
else:
    st.info(
        "This change has minimal impact. Focus on quality (active recall, tests)."
    )

# ================= STEP 5E: SMART ALERTS & ADAPTIVE RECOMMENDATIONS =================
st.divider()
st.header("🚨 Smart Alerts & Recommendations")

alerts = []
actions = []

# ---------- Alert 1: Urgent exams ----------
urgent = plan[plan["Days_Left"] <= 5]
if not urgent.empty:
    alerts.append(
        f"⏰ **Urgent Exams Coming Up:** {', '.join(urgent.Subject)}"
    )
    actions.append(
        "Prioritize these subjects daily using revision + mock tests."
    )

# ---------- Alert 2: High risk subjects ----------
high_risk = plan[plan["Risk_Level"] == "🔴 High Risk"]
if not high_risk.empty:
    alerts.append(
        f"🔴 **High Risk Subjects Detected:** {', '.join(high_risk.Subject)}"
    )
    actions.append(
        "Increase frequency and use active recall instead of passive reading."
    )

# ---------- Alert 3: Low confidence ----------
low_conf = plan[plan["Confidence"] <= 2]
if not low_conf.empty:
    alerts.append(
        f"📉 **Low Confidence Subjects:** {', '.join(low_conf.Subject)}"
    )
    actions.append(
        "Break topics into smaller chunks and track small wins."
    )

# ---------- Alert 4: Burnout risk ----------
if "Burnout_Risk" in plan.columns:
    burnout_high = plan[plan["Burnout_Risk"] == "🔴 High"]
    if not burnout_high.empty:
        alerts.append(
            f"🔥 **Burnout Risk Detected:** {', '.join(burnout_high.Subject)}"
        )
        actions.append(
            "Reduce hours slightly and switch to lighter revision sessions."
        )

# ---------- Alert 5: Imbalanced workload ----------
if plan["Study_Hours_Today"].max() >= total_hours * 0.6:
    alerts.append("⚖️ **Imbalanced Schedule Detected**")
    actions.append(
        "Redistribute time to avoid overloading a single subject."
    )

# ---------- Display Alerts ----------
if not alerts:
    st.success("✅ No critical alerts. Your study plan looks balanced.")
else:
    for a in alerts:
        st.warning(a)

    st.subheader("🧠 Recommended Actions")
    for act in set(actions):
        st.markdown(f"- {act}")
# ================= STEP 5F: VISUAL DASHBOARD =================
st.divider()
st.header("📊 Progress Dashboard")

# ---------- Risk Level Distribution ----------
st.subheader("⚠️ Risk Distribution")

risk_counts = plan["Risk_Level"].value_counts()
st.bar_chart(risk_counts)

# ---------- Readiness Score Chart ----------
st.subheader("🎯 Exam Readiness by Subject")

readiness_df = plan[["Subject", "Readiness_Score"]].set_index("Subject")
st.bar_chart(readiness_df)

# ---------- Days Left Visual ----------
st.subheader("⏳ Days Left Until Exams")

days_left_df = plan[["Subject", "Days_Left"]].set_index("Subject")
st.bar_chart(days_left_df)

# ---------- Quick Interpretation ----------
st.subheader("🧠 How to read this dashboard")

st.markdown(
    """
- **Risk Distribution:** Fewer red bars = healthier plan  
- **Readiness Chart:** Aim to push subjects into 70–90 range  
- **Days Left:** Subjects with low days + low readiness need urgency  
"""
)
# ================= STEP 5G: AI-POWERED PERSONALIZED STUDY ADVICE =================
st.divider()
st.header("🧠 Personalized AI Study Advisor")

st.caption(
    "This advice is generated dynamically using your risk, readiness, "
    "confidence trends, and burnout signals."
)

# Select subject
advisor_subject = st.selectbox(
    "Choose a subject for personalized advice",
    plan["Subject"].unique(),
    key="advisor_subject"
)

row = plan[plan["Subject"] == advisor_subject].iloc[0]

advice = []

# ---------- Risk-based advice ----------
if row["Risk_Level"] == "🔴 High Risk":
    advice.append(
        "This subject is high risk. Prioritize it daily and focus on exam-oriented practice."
    )
elif row["Risk_Level"] == "🟡 Medium Risk":
    advice.append(
        "You are moderately prepared. Increase revision frequency and solve mixed questions."
    )
else:
    advice.append(
        "You are low risk. Maintain consistency and do light revision."
    )

# ---------- Readiness-based advice ----------
if row["Readiness_Score"] < 50:
    advice.append(
        "Your readiness score is low. Start with fundamentals and avoid time pressure."
    )
elif row["Readiness_Score"] < 75:
    advice.append(
        "You are almost ready. Focus on weak areas and past-year questions."
    )
else:
    advice.append(
        "You are exam ready. Focus on speed, accuracy, and mock tests."
    )

# ---------- Burnout-based advice ----------
if "Burnout_Risk" in plan.columns:
    if row["Burnout_Risk"] == "🔴 High":
        advice.append(
            "Burnout risk is high. Reduce study hours slightly and use shorter focused sessions."
        )
    elif row["Burnout_Risk"] == "🟡 Medium":
        advice.append(
            "Watch for fatigue. Take regular breaks and avoid overloading."
        )

# ---------- Time-based advice ----------
if row["Days_Left"] <= 7:
    advice.append(
        "Exam is very close. Shift from learning new topics to revision and mock tests."
    )

# ---------- Display advice ----------
for tip in advice:
    st.markdown(f"- {tip}")

st.info(
    "💡 Tip: This AI advisor adapts automatically as your confidence, hours, and risk change."
)
