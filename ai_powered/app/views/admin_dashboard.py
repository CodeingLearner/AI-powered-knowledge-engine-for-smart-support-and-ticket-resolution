import streamlit as st
import pandas as pd
import ticket_service
from .user_dashboard import handle_document_upload
import os
import rag_engine
import config
import auth_service
import altair as alt

def render_overview():
    st.header("📈 Dashboard Overview")
    kpis = ticket_service.get_admin_kpis()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="glass-card" style="padding: 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.metric("Total Tickets", kpis['total_tickets'])
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-card" style="padding: 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.metric("Resolved", kpis['resolved_tickets'])
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="glass-card" style="padding: 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.metric("Open / Tentative", kpis['tentative_tickets'] + kpis['unresolved_tickets'])
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="glass-card" style="padding: 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
        st.metric("Avg Confidence", f"{kpis['avg_confidence']:.1%}")
        st.markdown('</div>', unsafe_allow_html=True)


def render_all_tickets():
    st.header("📋 All Tickets")
    tickets_df = ticket_service.get_all_tickets()
    st.dataframe(tickets_df, use_container_width=True)

def render_analytics():
    st.header("📊 Analytics")
    tickets_df = ticket_service.get_all_tickets()
    
    if not tickets_df.empty:
        st.markdown('<div style="margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)
        st.subheader("Category Distribution")
        cat_counts = tickets_df['category'].value_counts().reset_index()
        cat_counts.columns = ['category', 'count']
        
        cat_chart = alt.Chart(cat_counts).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('category:N', title='', sort='-y', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('count:Q', title='Ticket Count', axis=alt.Axis(tickMinStep=1, format='d')),
            color=alt.Color('category:N', legend=None, scale=alt.Scale(scheme='purples')),
            tooltip=['category', 'count']
        ).properties(height=300).configure_view(strokeWidth=0)
        st.altair_chart(cat_chart, use_container_width=True)
    
        st.markdown('<div style="margin-top: 2rem; margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)
        st.subheader("Priority Levels")
        pri_counts = tickets_df['priority'].value_counts().reset_index()
        pri_counts.columns = ['priority', 'count']
        
        pri_chart = alt.Chart(pri_counts).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="count", type="quantitative"),
            color=alt.Color(field="priority", type="nominal", scale=alt.Scale(scheme='blues'), title='Priority'),
            tooltip=['priority', 'count']
        ).properties(height=300).configure_view(strokeWidth=0)
        st.altair_chart(pri_chart, use_container_width=True)

        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        st.subheader("Tickets over Time")
        tickets_df['date'] = pd.to_datetime(tickets_df['created_at']).dt.date
        date_counts = tickets_df['date'].value_counts().sort_index().reset_index()
        date_counts.columns = ['date', 'count']
        
        line_chart = alt.Chart(date_counts).mark_line(point=True, color='#00b4d8', strokeWidth=3).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('count:Q', title='Ticket Count', axis=alt.Axis(tickMinStep=1, format='d')),
            tooltip=['date', 'count']
        ).properties(height=300).configure_view(strokeWidth=0)
        st.altair_chart(line_chart, use_container_width=True)

        import plotly.express as px
        
        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        st.subheader("Category vs Priority Heatmap")
        heatmap_df = tickets_df.groupby(['category', 'priority']).size().reset_index(name='count')
        
        if not heatmap_df.empty:
            # Add Context Data (KPIs) above heatmap
            h_col1, h_col2, h_col3 = st.columns(3)
            total = int(heatmap_df['count'].sum())
            high_pri = int(heatmap_df[heatmap_df['priority'].isin(['High', 'Critical'])]['count'].sum())
            low_pri = int(heatmap_df[heatmap_df['priority'] == 'Low']['count'].sum())
            
            h_col1.metric("Total Tickets", total)
            h_col2.metric("High Priority", high_pri)
            h_col3.metric("Low Priority", low_pri)
            
            st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
            
            # Pivot data for heatmap
            pivot_df = heatmap_df.pivot(index='category', columns='priority', values='count').fillna(0)
            
            # Reorder columns to logical priority if they exist
            cols_order = [c for c in ['Low', 'Medium', 'High', 'Critical'] if c in pivot_df.columns]
            if cols_order:
                pivot_df = pivot_df[cols_order]
                
            fig = px.imshow(
                pivot_df,
                text_auto=True,
                color_continuous_scale="RdYlGn_r"  # Reversed so high numbers are Red
            )
            
            fig.update_traces(
                xgap=10, 
                ygap=10, 
                textfont=dict(size=18, color="white")
            )
            
            fig.update_layout(
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                plot_bgcolor="#0E1117",
                paper_bgcolor="#0E1117",
                font=dict(color="white")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for heatmap.")
    else:
        st.info("No data available for analytics.")

def render_knowledge_base_admin():
    st.header("📚 Knowledge Base Management")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("Upload entirely new sets of documents to the global RAG database.")
    handle_document_upload()
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Indexed Documents")
        if os.path.exists(rag_engine.DATA_PROCESSED_DIR):
            processed_files = os.listdir(rag_engine.DATA_PROCESSED_DIR)
            for f in processed_files:
                st.write(f"- 📄 {f}")
        else:
            st.write("None")
            
    with col2:
        st.subheader("Pending Documents")
        if os.path.exists(rag_engine.DATA_RAW_DIR):
            raw_files = os.listdir(rag_engine.DATA_RAW_DIR)
            for f in raw_files:
                st.write(f"- ⏳ {f}")
        else:
            st.write("None")

def render_ai_insights():
    st.header("🧠 AI Insights")
    st.markdown('<div style="margin-top: 1.5rem; margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)
    st.subheader("Top Repeated Issues")
    top_qs = ticket_service.get_top_questions()
    st.dataframe(top_qs, use_container_width=True)

    st.markdown('<div style="margin-top: 2rem; margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)
    st.subheader("Knowledge Gaps")
    gaps = ticket_service.get_knowledge_gap_groups()
    st.dataframe(gaps, use_container_width=True)

def render_all_users():
    st.header("👥 User Management")
    st.markdown('<div style="margin-bottom: 1rem;">', unsafe_allow_html=True)
    st.write("List of all registered users in the system.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    try:
        users = auth_service.get_all_users()
        if users:
            users_df = pd.DataFrame(users)
            st.dataframe(users_df, use_container_width=True)
        else:
            st.info("No users found.")
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        
    st.markdown('</div>', unsafe_allow_html=True)
def render_admin_dashboard():
    menu_selection = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "User Management"]
    )

    if menu_selection == "Dashboard":
        render_overview()
        
        st.markdown('<div style="margin-top: 3rem;"></div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Tickets", "📊 Analytics", "🧠 AI Insights", "📚 Knowledge Base"])
        
        with tab1:
            st.markdown('<div class="glass-card" style="padding: 1.5rem; margin-top: 1rem; margin-bottom: 2rem;">', unsafe_allow_html=True)
            render_all_tickets()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab2:
            st.markdown('<div class="glass-card" style="padding: 1.5rem; margin-top: 1rem; margin-bottom: 2rem;">', unsafe_allow_html=True)
            render_analytics()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab3:
            st.markdown('<div class="glass-card" style="padding: 1.5rem; margin-top: 1rem; margin-bottom: 2rem;">', unsafe_allow_html=True)
            render_ai_insights()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab4:
            st.markdown('<div class="glass-card" style="padding: 1.5rem; margin-top: 1rem; margin-bottom: 2rem;">', unsafe_allow_html=True)
            render_knowledge_base_admin()
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu_selection == "User Management":
        render_all_users()
