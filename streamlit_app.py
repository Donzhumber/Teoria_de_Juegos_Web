import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
from simulation_engine import SimulationEngine

# Page Config
st.set_page_config(
    page_title="Bayesian Kidnapping Simulator | Premium AI Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper for layout
def glass_container(title=None):
    container = st.container()
    if title:
        container.markdown(f"### {title}")
    return container

# ============================================================
# SIDEBAR: PARAMETERS
# ============================================================

st.sidebar.markdown("# 🛡️ Simulation Control")
st.sidebar.markdown("---")

with st.sidebar.expander("🌍 Environment Settings", expanded=True):
    region = st.selectbox("Operating Region", ["Andina", "Metro", "OriSel", "PacRoj", "Carib"])
    n_max = st.slider("Max Duration (Days)", 30, 360, 120)

with st.sidebar.expander("⚖️ Policy Weights (Government)", expanded=False):
    w_pay = st.slider("Ransom Penalty (W_pay)", 100, 1500, 650)
    w_death = st.slider("Death Penalty (W_death)", 500, 3000, 1800)
    g_rescue = st.slider("Rescue Gain (G_rescue)", 0, 1000, 350)

# Initialize Engine
engine = SimulationEngine(region=region)

# ============================================================
# MAIN INTERFACE
# ============================================================

st.markdown("# Bayesian Kidnapping Simulation")
st.markdown("### Interactive Econometric Intelligence Dashboard")

tabs = st.tabs(["🚀 Live Simulator", "📊 Monte Carlo Stress Test", "📖 Methodology"])

# ------------------------------------------------------------
# TAB 1: LIVE SIMULATOR
# ------------------------------------------------------------
with tabs[0]:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### Scenario Configuration")
        # Let user choose a "secret" true type for simulation or randomize
        true_type_name = st.selectbox("True Captor Type (Hidden from Agent)", 
                                     [t['name'] for t in engine.Theta])
        true_type_idx = next(i for i, t in enumerate(engine.Theta) if t['name'] == true_type_name)
        
        run_sim = st.button("🚀 Run Live Simulation")
        st.markdown("</div>", unsafe_allow_html=True)

    if run_sim:
        history = []
        mu_t = engine.priors.copy()
        
        status_area = st.empty()
        chart_area = st.empty()
        metric_area = st.empty()
        
        for t in range(n_max):
            step = engine.run_simulation_step(mu_t, t, true_type_idx)
            history.append(step)
            mu_t = step['new_mu']
            
            # Update Metrics
            m_col1, m_col2, m_col3 = metric_area.columns(3)
            m_col1.metric("Day", t)
            m_col2.metric("Agent Action (α)", f"{step['alpha']:.2f}")
            m_col3.metric("Deterrence (γ)", f"{step['gamma']:.2f}")
            
            # Update Chart
            beliefs = engine.aggregate_beliefs(mu_t)
            df_beliefs = pd.DataFrame(list(beliefs.items()), columns=['Group', 'Probability'])
            fig = px.bar(df_beliefs, x='Group', y='Probability', 
                         title=f"Agent Beliefs Evolution - Day {t}",
                         color='Probability', color_continuous_scale='Viridis',
                         range_y=[0, 1])
            fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            chart_area.plotly_chart(fig, use_container_width=True)
            
            status_area.info(f"Day {t}: Event observed -> **{step['event'].upper()}**")
            
            if step['event'] != 'cont':
                status_area.success(f"Simulation Terminated on Day {t} due to **{step['event'].upper()}**")
                break
            
            time.sleep(0.05) if t < 20 else time.sleep(0.01)

# ------------------------------------------------------------
# TAB 2: MONTE CARLO STRESS TEST
# ------------------------------------------------------------
with tabs[1]:
    st.markdown("#### Aggregate Analytics")
    n_sims = st.select_slider("Select Number of Simulations", options=[50, 100, 250, 500], value=100)
    
    if st.button("🧪 Run Batch Analysis"):
        results_list = []
        progress_bar = st.progress(0)
        
        for i in range(n_sims):
            # Randomize true type for batch
            batch_mu = engine.priors.copy()
            batch_true_idx = np.random.choice(len(engine.Theta), p=engine.priors)
            
            for t in range(n_max):
                step = engine.run_simulation_step(batch_mu, t, batch_true_idx)
                batch_mu = step['new_mu']
                if step['event'] != 'cont':
                    results_list.append({'sim_id': i, 'tau': t, 'event': step['event'], 'true_k': engine.Theta[batch_true_idx]['k']})
                    break
            else:
                results_list.append({'sim_id': i, 'tau': n_max, 'event': 'censored', 'true_k': engine.Theta[batch_true_idx]['k']})
            
            progress_bar.progress((i + 1) / n_sims)
        
        df_res = pd.DataFrame(results_list)
        
        # Summary Visuals
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df_res, names='event', title="Outcome Composition")
            fig_pie.update_layout(template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            fig_hist = px.histogram(df_res, x='tau', color='event', title="Duration Distribution (Days)")
            fig_hist.update_layout(template="plotly_dark")
            st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------------------------
# TAB 3: METHODOLOGY
# ------------------------------------------------------------
with tabs[2]:
    st.markdown("""
    ### Econometric Framework
    
    This simulation implements a **Dynamic Bayesian Learning Mechanism** where the State and the Victim's Family face uncertainty about the kidnapper's identity and motivations.
    
    #### Core Components:
    1.  **Type Space ($\Theta$):** Combinations of Organization (DC, PAR, ELN, FARC), Financial Policy (Pay/NoPay), and Visibility (Public/NonPublic).
    2.  **Bayesian Update:** The State updates its beliefs ($\mu_t$) based on survival events and family interactions using multi-level Hazard functions estimated via Cox Proportional Hazard models.
    3.  **Optimal Control:** The State optimizes intensities ($\alpha, \gamma$) by balancing social costs of death and ransom payments against the likelihood of rescue.
    4.  **Softmax Selection:** Decisions are not purely deterministic; they follow a stochastic optimization rule ($\xi$) to reflect real-world variability and prevent agent-bias.
    
    *Developed as a digital twin of the theoretical MATLAB framework.*
    """)

# Footer
st.markdown("---")
st.caption("AI-Powered Bayesian Simulation Agency | Antigravity Design System")
