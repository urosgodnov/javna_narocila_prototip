"""
Ultra-modern, minimal design system - 2024 style
No icons, no BS, just clean professional UI
"""

def get_unified_css():
    """Modern minimal CSS - inspired by Linear, Vercel, Stripe"""
    return """
    <style>
    /* Import Inter font for that modern look */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Reset and base */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Extended color palette with semantic colors */
    :root {
        /* Grayscale palette */
        --text-primary: #000000;
        --text-secondary: #666666;
        --text-tertiary: #999999;
        --bg-primary: #FFFFFF;
        --bg-secondary: #FAFAFA;
        --bg-tertiary: #F5F5F5;
        --border: #E5E5E5;
        --border-hover: #CCCCCC;
        
        /* Extended grayscale */
        --primary-50: #f8fafc;
        --primary-100: #f1f5f9;
        --primary-200: #e2e8f0;
        --primary-600: #475569;
        --primary-900: #0f172a;
        
        /* Semantic colors */
        --accent: #3b82f6;
        --accent-hover: #2563eb;
        --accent-blue: #3b82f6;
        --success-green: #10b981;
        --warning-amber: #f59e0b;
        --error-red: #ef4444;
        
        /* Success and error (legacy support) */
        --success: #10b981;
        --error: #ef4444;
        
        /* Border radius */
        --radius-sm: 4px;
        --radius-md: 6px;
        --radius-lg: 8px;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
        --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
        
        /* Transitions */
        --transition-fast: 150ms ease;
        --transition-normal: 250ms ease;
    }
    
    /* Typography - clean and minimal */
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px;
        line-height: 1.5;
        color: var(--text-primary);
        background: var(--bg-primary);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        letter-spacing: -0.02em;
        margin: 0;
        padding: 0;
    }
    
    h1 { font-size: 28px; line-height: 1.2; }
    h2 { font-size: 20px; line-height: 1.3; }
    h3 { font-size: 16px; line-height: 1.4; }
    
    /* Remove ALL Streamlit default styling */
    .stApp {
        background: var(--bg-primary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {display: none;}
    footer {display: none;}
    header {visibility: hidden;}
    
    /* Page header - ultra minimal */
    .page-header {
        padding: 32px 0 24px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 32px;
        background: var(--bg-primary);
    }
    
    .page-header h1 {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.03em;
    }
    
    .page-header p {
        color: var(--text-secondary);
        font-size: 14px;
        margin-top: 4px;
    }
    
    /* Buttons - minimal, no borders */
    .stButton > button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md);
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        transition: background 0.2s ease;
        box-shadow: none !important;
        letter-spacing: -0.01em;
    }
    
    .stButton > button:hover {
        background: var(--accent-hover) !important;
        color: white !important;
        transform: none;
        box-shadow: none !important;
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }
    
    /* Inputs - minimal borders */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        padding: 8px 12px;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        background: var(--bg-primary);
        color: var(--text-primary);
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent);
    }
    
    /* Labels - minimal */
    .stTextInput > label,
    .stTextArea > label,
    .stNumberInput > label,
    .stSelectbox > label {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 4px;
        letter-spacing: -0.01em;
    }
    
    /* Tabs - Linear style */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid var(--border);
        gap: 24px;
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        padding: 12px 0;
        margin-right: 24px;
        font-weight: 500;
        font-size: 14px;
        color: var(--text-secondary);
        transition: all 0.2s ease;
        letter-spacing: -0.01em;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary);
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--text-primary);
        border-bottom-color: var(--accent);
        background: transparent;
    }
    
    /* Tables - minimal */
    .dataframe {
        border: none;
        font-size: 13px;
    }
    
    .dataframe thead tr {
        border-bottom: 1px solid var(--border);
    }
    
    .dataframe thead th {
        background: transparent;
        font-weight: 500;
        color: var(--text-secondary);
        padding: 8px 12px;
        text-align: left;
        border: none;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid var(--border);
    }
    
    .dataframe tbody tr:hover {
        background: var(--bg-secondary);
    }
    
    .dataframe tbody td {
        padding: 12px;
        color: var(--text-primary);
        border: none;
    }
    
    /* Metrics - minimal */
    [data-testid="metric-container"] {
        background: transparent;
        padding: 16px 0;
        border: none;
        border-radius: 0;
        box-shadow: none;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.03em;
    }
    
    [data-testid="metric-container"] label {
        font-size: 12px;
        color: var(--text-secondary);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    /* Alerts - minimal */
    .stAlert {
        border-radius: var(--radius-md);
        padding: 12px 16px;
        border: 1px solid var(--border);
        background: var(--bg-secondary);
        font-size: 14px;
    }
    
    /* Sidebar - minimal */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
        padding-top: 32px;
    }
    
    /* Expanders - minimal */
    .streamlit-expanderHeader {
        background: transparent;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        font-weight: 500;
        font-size: 14px;
        padding: 12px 16px;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-secondary);
    }
    
    /* File uploader - minimal */
    .stFileUploader > div > div {
        border: 1px dashed var(--border);
        border-radius: var(--radius-md);
        padding: 24px;
        background: var(--bg-secondary);
        text-align: center;
    }
    
    .stFileUploader > div > div:hover {
        border-color: var(--accent);
        background: var(--bg-tertiary);
    }
    
    /* Progress bar - minimal */
    .stProgress > div > div > div {
        background: var(--accent);
    }
    
    .stProgress > div > div {
        background: var(--bg-tertiary);
        height: 2px;
    }
    
    /* Remove all decorative elements */
    .css-1v0mbdj > img {
        display: none;
    }
    
    .row-widget.stRadio > div {
        flex-direction: row;
        gap: 16px;
    }
    
    /* Login specific */
    .login-container {
        max-width: 360px;
        margin: 80px auto;
        padding: 0;
    }
    
    .login-header {
        margin-bottom: 32px;
    }
    
    .login-header h3 {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .login-header p {
        color: var(--text-secondary);
        font-size: 14px;
    }
    
    /* Remove emoji from everywhere */
    [data-testid="stMarkdownContainer"] p:first-child {
        font-size: 16px;
        font-weight: 500;
        color: var(--text-primary);
    }
    
    /* Clean spacing */
    .block-container {
        padding: 0 48px;
        max-width: 1200px;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px;
    }
    
    /* Modern Card Component */
    .modern-card {
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 24px;
        margin-bottom: 16px;
        transition: all var(--transition-fast);
    }
    
    .modern-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .card-header {
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border);
    }
    
    .card-header h3 {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }
    
    .card-content {
        color: var(--text-secondary);
        font-size: 14px;
        line-height: 1.6;
    }
    
    .card-actions {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border);
        display: flex;
        gap: 8px;
    }
    
    /* Modern Table Component */
    .modern-table {
        width: 100%;
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        overflow: hidden;
    }
    
    .modern-table thead {
        background: var(--bg-secondary);
    }
    
    .modern-table th {
        padding: 12px 16px;
        text-align: left;
        font-weight: 500;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border);
    }
    
    .modern-table tbody tr {
        border-bottom: 1px solid var(--primary-100);
        transition: background var(--transition-fast);
    }
    
    .modern-table tbody tr:hover {
        background: var(--bg-secondary);
    }
    
    .modern-table td {
        padding: 16px;
        font-size: 14px;
        color: var(--text-primary);
    }
    
    /* Status Badge Component */
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    .status-success {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success-green);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        color: var(--warning-amber);
    }
    
    .status-error {
        background: rgba(239, 68, 68, 0.1);
        color: var(--error-red);
    }
    
    .status-info {
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-blue);
    }
    
    /* Skeleton Loader Component */
    .skeleton-loader {
        padding: 16px;
    }
    
    .skeleton-line {
        height: 16px;
        background: linear-gradient(90deg, 
            var(--primary-100) 25%, 
            var(--primary-200) 50%, 
            var(--primary-100) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: var(--radius-sm);
        margin-bottom: 8px;
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    /* Progress Bar Component */
    .progress-container {
        width: 100%;
        height: 8px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        background: var(--accent-blue);
        transition: width var(--transition-normal);
    }
    
    .progress-label {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
    }
    
    /* Toast Notification Component */
    .toast-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 300px;
        max-width: 500px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .toast-success {
        background: var(--success-green);
        color: white;
    }
    
    .toast-error {
        background: var(--error-red);
        color: white;
    }
    
    .toast-warning {
        background: var(--warning-amber);
        color: white;
    }
    
    .toast-info {
        background: var(--accent-blue);
        color: white;
    }
    
    .toast-close {
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        padding: 0;
        margin-left: auto;
    }
    
    /* Search Input Component */
    .search-input {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        font-size: 14px;
        font-family: 'Inter', sans-serif;
        transition: all var(--transition-fast);
    }
    
    .search-input:focus {
        outline: none;
        border-color: var(--accent-blue);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Modern Button Variants */
    .modern-button {
        padding: 8px 16px;
        border-radius: var(--radius-md);
        font-size: 14px;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        transition: all var(--transition-fast);
        border: none;
    }
    
    .modern-button-primary {
        background: var(--accent);
        color: white;
    }
    
    .modern-button-primary:hover {
        background: var(--accent-hover);
    }
    
    .modern-button-secondary {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--border);
    }
    
    .modern-button-secondary:hover {
        background: var(--bg-secondary);
        border-color: var(--border-hover);
    }
    </style>
    """

def get_button_script():
    """Minimal JavaScript - no fancy effects"""
    return r"""
    <script>
    // Remove any emoji or icons from text
    document.addEventListener('DOMContentLoaded', function() {
        // Clean up any remaining emoji
        const elements = document.querySelectorAll('*');
        elements.forEach(el => {
            if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
                el.textContent = el.textContent.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]/gu, '');
            }
        });
    });
    </script>
    """

def apply_design_system():
    """Apply the ultra-modern minimal design system with accessibility"""
    import streamlit as st
    from ui.components.accessibility import initialize_accessibility
    
    # Apply core design system
    st.markdown(get_unified_css(), unsafe_allow_html=True)
    st.markdown(get_button_script(), unsafe_allow_html=True)
    
    # Initialize accessibility features
    initialize_accessibility()