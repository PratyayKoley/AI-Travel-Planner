import streamlit as st
from agents import MultiAgentOrchestrator

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="TripMind — AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================
st.markdown("""
<style>
    /* Main Header Styling */
    .main-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.2em;
        opacity: 0.9;
    }
    
    /* Step Headers */
    .step-header {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 30px 0 15px 0;
        border-left: 5px solid #667eea;
    }
    
    .step-header h3 {
        margin: 0;
        color: #2c3e50;
    }
    
    /* Cost Cards */
    .cost-card {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        transition: all 0.3s ease;
    }
    
    .cost-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Success Box */
    .success-box {
        background: #d4edda;
        border: 2px solid #28a745;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    /* Warning Box */
    .warning-box {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    /* Info Box */
    .info-box {
        background: #d1ecf1;
        border: 2px solid #17a2b8;
        border-left: 5px solid #17a2b8;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 1.1em;
    }
    
    .stButton>button:hover {
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }
    
    /* Footer Styling */
    .footer {
        text-align: center;
        padding: 30px;
        background: #f8f9fa;
        border-radius: 10px;
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER SECTION
# ============================================================================
st.markdown("""
<div class="main-header">
    <h1>✈️ TripMind — AI Travel Planner</h1>
    <p>Plan your perfect trip with our intelligent multi-agent system</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - USER SETTINGS & EXAMPLES
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Location Selection
    st.markdown("### 📍 Your Location")
    user_state = st.selectbox(
        "Select your state/region:",
        options=[
            "Maharashtra", "Kerala", "Goa", "Rajasthan", "Karnataka",
            "Tamil Nadu", "Uttar Pradesh", "Delhi", "West Bengal", "Gujarat",
            "Madhya Pradesh", "Himachal Pradesh", "Uttarakhand", "Punjab",
            "Andhra Pradesh", "Telangana", "Haryana", "Jammu and Kashmir",
            "Odisha", "Assam", "Bihar", "Jharkhand", "Chhattisgarh"
        ],
        index=0,
        help="This helps us suggest nearby destinations"
    )
    
    cities = {
        "Maharashtra": ["Mumbai", "Pune", "Lonavala", "Nashik", "Aurangabad", "Nagpur", "Kolhapur", "Mahabaleshwar"],
        "Kerala": ["Kochi", "Munnar", "Alleppey", "Thiruvananthapuram", "Wayanad", "Kovalam", "Thekkady"],
        "Goa": ["Panaji", "Baga", "Calangute", "Anjuna", "Palolem", "Margao", "Candolim"],
        "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur", "Jaisalmer", "Pushkar", "Mount Abu", "Bikaner"],
        "Karnataka": ["Bangalore", "Mysore", "Coorg", "Hampi", "Mangalore", "Udupi", "Chikmagalur"],
        "Tamil Nadu": ["Chennai", "Madurai", "Coimbatore", "Ooty", "Kodaikanal", "Rameswaram", "Kanyakumari"],
        "Uttar Pradesh": ["Agra", "Varanasi", "Lucknow", "Mathura", "Vrindavan", "Allahabad", "Ayodhya"],
        "Delhi": ["New Delhi", "Old Delhi", "Connaught Place", "Dwarka", "Hauz Khas"],
        "West Bengal": ["Kolkata", "Darjeeling", "Siliguri", "Durgapur", "Digha", "Kalimpong"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Dwarka", "Somnath", "Gir", "Kutch"],
        "Madhya Pradesh": ["Bhopal", "Indore", "Ujjain", "Gwalior", "Khajuraho", "Pachmarhi"],
        "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Kullu", "Kasauli", "Dalhousie", "Spiti"],
        "Uttarakhand": ["Dehradun", "Mussoorie", "Nainital", "Rishikesh", "Haridwar", "Auli", "Jim Corbett"],
        "Punjab": ["Amritsar", "Chandigarh", "Ludhiana", "Patiala", "Jalandhar", "Pathankot"],
        "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Tirupati", "Amaravati", "Araku Valley"],
        "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
        "Haryana": ["Gurgaon", "Faridabad", "Ambala", "Karnal", "Panipat", "Kurukshetra"],
        "Jammu and Kashmir": ["Srinagar", "Gulmarg", "Pahalgam", "Jammu", "Leh", "Ladakh", "Sonamarg"],
        "Odisha": ["Bhubaneswar", "Puri", "Konark", "Cuttack", "Chilika", "Gopalpur"],
        "Assam": ["Guwahati", "Kaziranga", "Tezpur", "Jorhat", "Majuli", "Sivasagar"],
        "Bihar": ["Patna", "Bodh Gaya", "Nalanda", "Rajgir", "Gaya", "Vaishali"],
        "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Netarhat", "Deoghar"],
        "Chhattisgarh": ["Raipur", "Bilaspur", "Bhilai", "Durg", "Jagdalpur"]
    }
    
    user_city = st.selectbox(
        "City:",
        options=cities[user_state],
        help="Your current city for better recommendations"
    )
    
    st.markdown("---")
    
    # Quick Start Examples
    st.markdown("### 💡 Quick Start Examples")
    st.markdown("Click any example to try it:")
    
    examples = [
        f"{user_city} 3 days budget 8000",
        "I want multiple trips under 5000 for 3 days",
        f"Plan a 5 day luxury trip to {user_city}",
        f"Weekend getaway near {user_city} under 10000",
        f"7 days {user_state} tour budget 20000",
        "Suggest me 4 days trip under 15000"
    ]
    
    selected_example = st.radio(
        "Choose an example:",
        ["✍️ Write Custom Query"] + examples,
        index=0
    )
    
    st.markdown("---")
    
    # Tips Section
    st.markdown("### 💡 Pro Tips")
    st.info("""
    **For best results, include:**
    - 📍 Destination (or ask for suggestions)
    - 📅 Number of days
    - 💰 Budget amount
    - 🎯 Travel style (budget/luxury)
    """)
    
    st.markdown("---")
    st.caption("🔒 Fully AI-powered • API-based system")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# Query Input Section
st.markdown("### 🔍 Describe Your Dream Trip")

col1, col2 = st.columns([3, 1])

with col1:
    if selected_example == "✍️ Write Custom Query":
        query = st.text_area(
            "Enter your travel query:",
            value=f"{user_city} 3 days budget 10000",
            height=120,
            placeholder="E.g., Plan a 4 day budget trip to Goa under 15000",
            help="Describe your trip in natural language",
            label_visibility="collapsed"
        )
    else:
        query = st.text_area(
            "Enter your travel query:",
            value=selected_example,
            height=120,
            label_visibility="collapsed"
        )

with col2:
    st.markdown("#### 📊 Quick Info")
    st.metric("📍 Your Location", user_state, delta=user_city)
    st.metric("📝 Query Length", f"{len(query)} chars")

# Action Buttons
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    run_btn = st.button(
        "🚀 Generate My Travel Plans", 
        type="primary", 
        use_container_width=True
    )

# ============================================================================
# MAIN PIPELINE EXECUTION
# ============================================================================
if run_btn and query:
    
    try:
        orchestrator = MultiAgentOrchestrator()
        
        q_lower = query.lower()
        if user_state.lower() not in q_lower and user_city.lower() not in q_lower:
            enhanced = f"state {user_state} city {user_city} {query}"
        else:
            enhanced = query
        
        result = orchestrator.process_query(enhanced)
        
        st.markdown('<div class="step-header"><h3>✨ Your Personalized Travel Plan</h3></div>', unsafe_allow_html=True)
        
        # Final summary display
        st.markdown(result)
        
        st.markdown("---")
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.download_button(
                label="📥 Download Full Itinerary",
                data=result,
                file_name=f"TripMind_{user_city}_{query.split()[0]}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Modify Query", use_container_width=True):
                st.rerun()
        
        with col3:
            st.button("📤 Share Plan", use_container_width=True, disabled=True, help="Coming soon!")
        
        st.success("🎉 Your travel plan is ready!")
        
        # Success message
        st.markdown("""
        <div class="footer">
            <h3>🎉 Your Perfect Trip Awaits!</h3>
            <p style="font-size: 1.1em; margin: 15px 0;">
                <b>Powered by Multi-Agent AI System</b><br>
                Query Resolver → Planner → Cost Analyzer → Summarizer
            </p>
            <p style="color: #666; margin-top: 20px;">
                <small>✨ All plans are AI-generated and can be customized further based on your preferences</small>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        
    except Exception as e:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.error(f"❌ **An error occurred while generating your travel plan**")
        st.write(f"**Error Details:** {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("🔧 View Technical Details"):
            st.exception(e)
        
        st.info("💡 **Tip:** Try simplifying your query or use one of the example queries from the sidebar.")

elif run_btn:
    st.warning("⚠️ Please enter a travel query to get started!")
    st.info("💡 Try using one of the example queries from the sidebar, or write your own!")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 30px;">
    <p style="margin: 5px 0; color: #666;">
        <b>TripMind v2.0</b> — Intelligent Travel Planning System
    </p>
    <p style="margin: 5px 0; color: #888; font-size: 0.9em;">
        Made with ❤️ using Streamlit & Python by
    </p>
    <p style="margin: 15px 0; color: #999; font-size: 0.85em;">
        🚀 API-powered • 💯 Free to use • 🌍 Location-aware
    </p>
</div>
""", unsafe_allow_html=True)