# design_components.py
import streamlit as st
from datetime import datetime
import base64

# Color scheme
PRIMARY_COLOR = "#1E88E5"  # Deep blue
SECONDARY_COLOR = "#26A69A"  # Teal
ACCENT_COLOR = "#FF5722"  # Orange
TEXT_COLOR = "#212121"  # Almost black
LIGHT_BG = "#F5F7F9"  # Light background
DARK_BG = "#0A192F"  # Dark background

# Configure page styling
def setup_page_config():
    st.set_page_config(
        page_title="MarketMind AI - Market Research Assistant",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown("""
    <style>
        /* Main page styling */
        .main {
            background-color: #F5F7F9;
            padding: 1.5rem;
        }
        
        /* Headers */
        h1 {
            color: #1E88E5;
            font-weight: 700;
            margin-bottom: 1.5rem;
        }
        
        h2 {
            color: #26A69A;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #E0E0E0;
            padding-bottom: 0.5rem;
        }
        
        h3 {
            color: #0A192F;
            font-weight: 600;
        }
        
        /* Form elements */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #E0E0E0;
            padding: 0.5rem;
            font-size: 1rem;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #1E88E5;
            box-shadow: 0 0 0 0.2rem rgba(30, 136, 229, 0.25);
        }
        
        .stButton > button {
            background-color: #1E88E5;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #1565C0;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        /* Results section */
        .results-container {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            margin-top: 2rem;
        }
        
        /* Card styling */
        .card {
            border-radius: 10px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            background-color: white;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
        }
        
        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #26A69A;
        }
        
        /* Download button */
        .download-btn {
            background-color: #FF5722;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin-top: 1rem;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #E0E0E0;
            color: #757575;
            font-size: 0.9rem;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F5F7F9;
            border-radius: 8px 8px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white;
            border-top: 3px solid #1E88E5;
        }
        
        /* Brand title styling */
        .brand-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #1E88E5, #26A69A);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
            margin-bottom: 0;
            display: inline-block;
        }
        
        .brand-title-ai {
            color: #FF5722;
            font-weight: 900;
            -webkit-text-fill-color: #FF5722;
        }
        
        /* Typewriter animation for tagline */
        .typewriter {
            overflow: hidden;
            border-right: .15em solid #26A69A;
            white-space: nowrap;
            margin: 0;
            display: inline-block;
            animation: 
                typing 3.5s steps(40, end),
                blink-caret .75s step-end infinite;
        }
        
        @keyframes typing {
            from { width: 0 }
            to { width: 100% }
        }
        
        @keyframes blink-caret {
            from, to { border-color: transparent }
            50% { border-color: #26A69A }
        }
    </style>
    
    <!-- Add script for typewriter effect -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const text = "Think like a market analyst, act like a machine.";
            const taglineElement = document.getElementById('typewriter-text');
            
            if (taglineElement) {
                let i = 0;
                taglineElement.textContent = '';
                
                function typeWriter() {
                    if (i < text.length) {
                        taglineElement.textContent += text.charAt(i);
                        i++;
                        setTimeout(typeWriter, 50);
                    }
                }
                
                typeWriter();
            }
        });
    </script>
    """, unsafe_allow_html=True)

# Header components
def render_header():
    """Renders the app header with logo and title"""
    col1, col2 = st.columns([1, 5])
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 10px;">
                <span style="font-size: 3rem; color: #1E88E5;">🧠</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="margin-bottom: 15px;">
                <h1 class="brand-title">Market<span style="color: #26A69A; -webkit-text-fill-color: #26A69A;">Mind</span> <span class="brand-title-ai">AI</span></h1>
                <div style="height: 30px; margin-top: 5px;">
                    <p id="typewriter-text" style="color: #757575; font-size: 1.1rem; margin-top: 0; font-style: italic; opacity: 0.9;">
                        "Think like a market analyst, act like a machine."
                    </p>
                </div>
                <script>
                    // Simulating typewriter effect with CSS
                    const textElement = document.getElementById('typewriter-text');
                    if (textElement) {
                        textElement.classList.add('typewriter');
                    }
                </script>
            </div>
        """, unsafe_allow_html=True)

# Input section with examples
def render_input_section():
    """Renders the input section with examples"""
    st.markdown("""
    <div class="card" style="background-color: #E3F2FD; border-left: 5px solid #1E88E5; padding: 1.2rem;">
        <h3 style="color: #1E88E5; margin-top: 0;">How it works</h3>
        <p style="color: #212121; font-size: 1.05rem; font-weight: 400;">Enter your business idea with a specific location to get realistic, location-specific market research.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Example cards in three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card" style="height: 100px; background-color: #FFFFFF; border: 1px solid #E0E0E0;">
            <strong style="color: #212121; display: block; margin-bottom: 8px;">Example:</strong>
            <span style="color: #424242; font-size: 1.05rem;">Gym in Coimbatore</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card" style="height: 100px; background-color: #FFFFFF; border: 1px solid #E0E0E0;">
            <strong style="color: #212121; display: block; margin-bottom: 8px;">Example:</strong>
            <span style="color: #424242; font-size: 1.05rem;">Coffee shop in New York</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card" style="height: 100px; background-color: #FFFFFF; border: 1px solid #E0E0E0;">
            <strong style="color: #212121; display: block; margin-bottom: 8px;">Example:</strong>
            <span style="color: #424242; font-size: 1.05rem;">IT consulting in Bangalore</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Input field
    business_idea = st.text_input("Enter your business idea with location:", 
                                 placeholder="e.g., Gym in Coimbatore", 
                                 key="business_idea_input")
    
    # Feature highlights
    st.markdown("""
    <div style="margin: 1.5rem 0;">
        <h3 style="color: #26A69A; margin-bottom: 1rem;">What you'll get</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
            <div style="flex: 1; min-width: 200px; background-color: white; padding: 1rem; border-radius: 8px; border-left: 3px solid #1E88E5; border: 1px solid #E0E0E0;">
                <strong style="color: #1E88E5; font-size: 1rem; display: block; margin-bottom: 5px;">📍 Local Market Data</strong>
                <span style="color: #424242; font-size: 0.95rem;">Real information about local businesses</span>
            </div>
            <div style="flex: 1; min-width: 200px; background-color: white; padding: 1rem; border-radius: 8px; border-left: 3px solid #26A69A; border: 1px solid #E0E0E0;">
                <strong style="color: #26A69A; font-size: 1rem; display: block; margin-bottom: 5px;">🔎 Competitor Analysis</strong>
                <span style="color: #424242; font-size: 0.95rem;">Analysis of actual competitors in your area</span>
            </div>
            <div style="flex: 1; min-width: 200px; background-color: white; padding: 1rem; border-radius: 8px; border-left: 3px solid #FF5722; border: 1px solid #E0E0E0;">
                <strong style="color: #FF5722; font-size: 1rem; display: block; margin-bottom: 5px;">📈 Location-Specific Trends</strong>
                <span style="color: #424242; font-size: 0.95rem;">Trends relevant to your business and location</span>
            </div>
            <div style="flex: 1; min-width: 200px; background-color: white; padding: 1rem; border-radius: 8px; border-left: 3px solid #9C27B0; border: 1px solid #E0E0E0;">
                <strong style="color: #9C27B0; font-size: 1rem; display: block; margin-bottom: 5px;">📊 Market Assessment</strong>
                <span style="color: #424242; font-size: 0.95rem;">Comprehensive market analysis for your specific area</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    generate_button = st.button("Generate Market Research Report")
    
    return business_idea, generate_button

# Progress indicators
def create_progress_indicators():
    """Creates and returns progress indicators"""
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    return progress_bar, status_container

def update_status(status_container, text, progress_bar=None, progress=None):
    """Updates status text and progress bar if provided"""
    status_container.markdown(f"""
    <div style="text-align: center; padding: 10px; background-color: white; 
    border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <p style="margin: 0; color: #1E88E5;">{text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if progress_bar and progress is not None:
        progress_bar.progress(progress)

# Results display
# In the display_report function, we need to update the background and ensure tab styling is appropriate
def display_report(report, business_idea):
    """Displays the final report with tabs for viewing and downloading"""
    st.markdown("""
    <div style="padding: 20px; border-radius: 10px; margin-top: 20px; 
    box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-top: 5px solid #26A69A;">
        <h2 style="color: #26A69A; margin-top: 0;">Market Research Report</h2>
    </div>
    
    <style>
    /* Custom styling for tabs - dark theme with orange text */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #0A192F;
        padding: 5px 5px 0 5px;
        border-radius: 10px 10px 0 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0A192F;
        border-radius: 8px 8px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #FF5722 !important;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #152238;
        border-top: 3px solid #FF5722;
        color: #FF5722 !important;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        background-color: transparent;
        border-radius: 0 0 10px 10px;
        border: 1px solid #333;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for report viewing options
    tab1, tab2 = st.tabs(["📄 View Report", "💾 Download Report"])
    
    with tab1:
        st.markdown(report)
    
    with tab2:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; background-color: transparent; border-radius: 10px;">
            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMTZMMTYgMTEuNDI4NUgxMy4yVjRIMTAuOFYxMS40Mjg1SDhMMTIgMTZaIiBmaWxsPSIjMUU4OEU1Ii8+PHBhdGggZD0iTTIwIDIwSDRWMTQuNVYxMy41VjEzLjRINi40VjE0LjVWMTcuNkgxNy42VjE0LjVWMTMuNEgyMFYxMy41VjE0LjVWMjBaIiBmaWxsPSIjMUU4OEU1Ii8+PC9zdmc+" alt="Download" style="width: 80px; height: 80px; margin-bottom: 20px;">
            <h3 style="margin-bottom: 20px;">Download Your Report</h3>
            <p style="color: #757575; margin-bottom: 30px;">Choose your preferred format below</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        # Generate safe filename
        safe_filename = f"marketmind_ai_{business_idea.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}"
        
        with col1:
            st.download_button(
                label="Download as Markdown (.md)",
                data=report,
                file_name=f"{safe_filename}.md",
                mime="text/markdown",
                key="download_md"
            )
        
        with col2:
            import markdown
            html_report = markdown.markdown(report)
            st.download_button(
                label="Download as HTML (.html)",
                data=html_report,
                file_name=f"{safe_filename}.html",
                mime="text/html",
                key="download_html"
            )

# Updated header components with improved typewriter animation
# Updated header components with improved looping typewriter animation
def render_header():
    """Renders the app header with logo and title"""
    col1, col2 = st.columns([1, 5])
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 10px;">
                <span style="font-size: 3rem; color: #1E88E5;">🧠</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="margin-bottom: 15px;">
                <h1 class="brand-title">Market<span style="color: #26A69A; -webkit-text-fill-color: #26A69A;">Mind</span> <span class="brand-title-ai">AI</span></h1>
                <div style="height: 30px; margin-top: 5px;">
                    <p class="typewriter-container" style="color: #757575; font-size: 1.1rem; margin-top: 0; font-style: italic; opacity: 0.9;">
                        <span class="typewriter">"Think like a market analyst, act like a machine."</span>
                    </p>
                </div>
            </div>
            
            <style>
            /* Container to restrict width */
            .typewriter-container {
                display: inline-block;
                margin: 0;
            }
            
            /* Improved typewriter animation for tagline */
            .typewriter {
                overflow: hidden;
                border-right: .15em solid #26A69A;
                white-space: nowrap;
                display: inline-block;
                width: 0;
                animation: 
                    typing 3.5s steps(40, end) 1s infinite alternate,
                    blink-caret .75s step-end infinite;
            }
            
            @keyframes typing {
                0% { width: 0 }
                90%, 100% { width: 100% }
            }
            
            @keyframes blink-caret {
                from, to { border-color: transparent }
                50% { border-color: #26A69A }
            }
            </style>
        """, unsafe_allow_html=True)
            
# Footer component
def render_footer():
    """Renders the app footer"""
    st.markdown("""
    <div class="footer">
        <p>MarketMind AI • Built with Streamlit, Groq LLM, and SerpAPI</p>
        <p style="font-size: 0.8rem;">© 2025 • All research data pulled from real-time sources</p>
    </div>
    """, unsafe_allow_html=True)

# Error and warning components
def show_error(message):
    """Displays an error message"""
    st.markdown(f"""
    <div style="background-color: #FFEBEE; border-left: 5px solid #F44336; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h3 style="color: #D32F2F; margin-top: 0; margin-bottom: 10px;">Error</h3>
        <p style="margin-bottom: 0; color: #212121;">{message}</p>
    </div>
    """, unsafe_allow_html=True)

def show_warning(message):
    """Displays a warning message"""
    st.markdown(f"""
    <div style="background-color: #FFF8E1; border-left: 5px solid #FFC107; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h3 style="color: #FF8F00; margin-top: 0; margin-bottom: 10px;">Note</h3>
        <p style="margin-bottom: 0; color: #212121;">{message}</p>
    </div>
    """, unsafe_allow_html=True)

def show_success(message):
    """Displays a success message"""
    st.markdown(f"""
    <div style="background-color: #E8F5E9; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h3 style="color: #2E7D32; margin-top: 0; margin-bottom: 10px;">Success</h3>
        <p style="margin-bottom: 0; color: #212121;">{message}</p>
    </div>
    """, unsafe_allow_html=True)