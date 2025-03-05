import streamlit as st
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta, timezone
import re
from typing import Dict, List, Any, Union, Optional, Tuple
import concurrent.futures
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from urllib.parse import urlparse
import json
from pathlib import Path
import time
import hashlib
from functools import lru_cache
import asyncio
import aiohttp
from dataclasses import dataclass, field, asdict
import io
from PIL import Image
import networkx as nx
import nltk
from nltk.corpus import stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from stqdm import stqdm
from dataclasses import dataclass, field

# Download NLTK resources
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
	
# Modern UI Theme Configuration
THEME = {
    "colors": {
        "primary": "#7676FA",
        "secondary": "#6C63FF",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "background": "#111827",
        "card": "#1F2937",
        "text": "#F9FAFB",
        "text_secondary": "#9CA3AF"
    },
    "fonts": {
        "heading": "Inter, sans-serif",
        "body": "Inter, sans-serif",
        "code": "JetBrains Mono, monospace"
    },
    "shadows": {
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    },
    "animations": {
        "default": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "fast": "all 0.15s cubic-bezier(0.4, 0, 0.2, 1)"
    }
}

# Advanced custom styles with dark theme and glassmorphism
CUSTOM_STYLES = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
    --primary: {THEME["colors"]["primary"]};
    --secondary: {THEME["colors"]["secondary"]};
    --success: {THEME["colors"]["success"]};
    --warning: {THEME["colors"]["warning"]};
    --error: {THEME["colors"]["error"]};
    --background: {THEME["colors"]["background"]};
    --card: {THEME["colors"]["card"]};
    --text: {THEME["colors"]["text"]};
    --text-secondary: {THEME["colors"]["text_secondary"]};
    --shadow-sm: {THEME["shadows"]["sm"]};
    --shadow-md: {THEME["shadows"]["md"]};
    --shadow-lg: {THEME["shadows"]["lg"]};
    --animation-default: {THEME["animations"]["default"]};
    --animation-fast: {THEME["animations"]["fast"]};
}}

/* Base overrides */
.stApp {{
    background-color: var(--background);
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: {THEME["fonts"]["heading"]};
    color: var(--text);
    font-weight: 600;
}}

p, li, span, div {{
    font-family: {THEME["fonts"]["body"]};
    color: var(--text);
}}

code {{
    font-family: {THEME["fonts"]["code"]};
}}

/* Card design */
.card {{
    background: rgba(31, 41, 55, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: var(--shadow-md);
    transition: var(--animation-default);
}}

.card:hover {{
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}}

.card-header {{
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding-bottom: 0.75rem;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.card-title {{
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
}}

/* App header */
.app-header {{
    padding: 2rem;
    background: linear-gradient(135deg, rgba(108, 99, 255, 0.2), rgba(126, 87, 194, 0.1));
    backdrop-filter: blur(10px);
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid rgba(108, 99, 255, 0.1);
    box-shadow: var(--shadow-lg);
}}

.app-logo {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
}}

.logo-icon {{
    font-size: 3rem;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
}}

.app-title {{
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #fff, #ccc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.app-subtitle {{
    margin: 0.5rem 0 0;
    font-size: 1rem;
    color: var(--text-secondary);
    max-width: 650px;
}}

/* Hero section */
.hero-section {{
    margin-bottom: 3rem;
    text-align: center;
}}

.hero-subtitle {{
    color: var(--primary);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.875rem;
    margin-bottom: 1rem;
}}

.hero-title {{
    font-size: 2.75rem;
    font-weight: 800;
    margin-bottom: 1rem;
    background: linear-gradient(
        90deg,
        #ffffff 0%,
        #e0f2fe 33%,
        #bfdbfe 66%,
        #93c5fd 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-size: 200% auto;
    animation: gradient-animation 4s linear infinite;
}}

.hero-description {{
    font-size: 1.1rem;
    color: var(--text-secondary);
    max-width: 700px;
    margin: 0 auto 2rem;
}}

@keyframes gradient-animation {{
    0% {{ background-position: 0% center; }}
    100% {{ background-position: 200% center; }}
}}

/* Footer */
.footer {{
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
}}

/* Streamlit component overrides */
div.stButton > button {{
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    padding: 0.5rem 1.5rem;
    transition: var(--animation-fast);
}}

div.stButton > button:hover {{
    opacity: 0.9;
    transform: translateY(-1px);
}}

.stTextInput > div > div > input {{
    background-color: rgba(31, 41, 55, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: var(--text);
}}

.stSelectbox > div > div > div {{
    background-color: rgba(31, 41, 55, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: var(--text);
}}

/* Tab styles */
div.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    background-color: transparent;
}}

div.stTabs [data-baseweb="tab"] {{
    height: 40px;
    border-radius: 8px;
    background-color: rgba(31, 41, 55, 0.5);
    margin-bottom: 10px;
}}

div.stTabs [aria-selected="true"] {{
    background-color: var(--primary) !important;
    color: white !important;
}}

/* Custom alert styles */
.alert {{
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}}

.alert-icon {{
    font-size: 1.25rem;
}}

.alert-content {{
    flex: 1;
}}

.alert-title {{
    font-weight: 600;
    margin-bottom: 0.25rem;
}}

.alert-message {{
    margin: 0;
    line-height: 1.5;
}}

.alert-info {{
    background-color: rgba(59, 130, 246, 0.1);
    border-left: 4px solid #3B82F6;
}}

.alert-success {{
    background-color: rgba(16, 185, 129, 0.1);
    border-left: 4px solid var(--success);
}}

.alert-warning {{
    background-color: rgba(245, 158, 11, 0.1);
    border-left: 4px solid var(--warning);
}}

.alert-error {{
    background-color: rgba(239, 68, 68, 0.1);
    border-left: 4px solid var(--error);
}}

/* Download button */
.download-button {{
    display: inline-block;
    padding: 0.5rem 1.5rem;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 500;
    margin-top: 1rem;
    transition: var(--animation-fast);
}}

.download-button:hover {{
    opacity: 0.9;
    transform: translateY(-1px);
}}

/* Stat card styles */
.stat-card {{
    background: rgba(31, 41, 55, 0.5);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1.25rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

.stat-card-value {{
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, #fff, #ccc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.stat-card-label {{
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin: 0;
}}

/* Grid system */
.grid-container {{
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 1.5rem;
    margin-bottom: 2rem;
}}

.grid-item-3 {{
    grid-column: span 3;
}}

.grid-item-4 {{
    grid-column: span 4;
}}

.grid-item-6 {{
    grid-column: span 6;
}}

.grid-item-8 {{
    grid-column: span 8;
}}

.grid-item-9 {{
    grid-column: span 9;
}}

.grid-item-12 {{
    grid-column: span 12;
}}

/* Status styles */
.status-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
}}

.status-ok {{
    color: var(--success);
}}

.status-warning {{
    color: var(--warning);
}}

.status-error {{
    color: var(--error);
}}
</style>
"""
# Icon SVG definitions for use throughout the app
ICONS = {
    "globe": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>""",
    "search": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>""",
    "check": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>""",
    "alert": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>""",
    "error": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>""",
    "info": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>""",
    "download": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>""",
    "upload": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>""",
    "settings": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>""",
    "chart": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>""",
    "image": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>""",
    "video": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>""",
    "refresh": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>"""
}
@dataclass
class URLData:
    url: str
    lastmod: Optional[str] = None
    priority: Optional[str] = None
    changefreq: Optional[str] = None
    images: List[str] = field(default_factory=list)
    videos: List[str] = field(default_factory=list)
    alternates: List[Dict] = field(default_factory=list)
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    redirected: bool = False
    final_url: Optional[str] = None
    status_group: Optional[str] = None
    error: Optional[str] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    indexability: Optional[bool] = None
    canonical_url: Optional[str] = None
    h1_count: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class SitemapInfo:
    url: str
    type: str  # "index" or "sitemap"
    last_modified: Optional[str] = None
    size: Optional[int] = None
    urls_count: Optional[int] = None
    compression: Optional[str] = None  # "gzip", "none", etc.
    xml_format: Optional[bool] = True
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class AnalysisResult:
    health_score: float = 0.0
    issues: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    keywords: Dict = field(default_factory=dict)
    performance: Dict = field(default_factory=dict)
    structure: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
		
class SitemapValidator:
    """Advanced Sitemap Validator with enhanced features and analytics"""
    
    def __init__(self):
        # Initialize state in session_state instead of instance variable
        if 'validator_state' not in st.session_state:
            st.session_state.validator_state = {
                "urls": [],
                "concurrent_requests": 10,
                "timeout": 15,
                "user_agent": "Mozilla/5.0 (Streamlit Advanced Sitemap Validator)",
                "status_counts": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0},
                "history": [],
                "advanced_mode": False,
                "content_analysis": False,
                "check_structured_data": False,
                "rate_limit": 100,  # ms between requests
                "follow_redirects": True,
                "crawl_depth": 1,
                "max_urls_to_check": 1000,
                "check_mobile_friendly": False,
                "check_performance": False,
                "check_ssl": True,
                "check_hreflang": True,
                "check_canonical": True,
                "extract_keywords": True,
                "analyze_competitors": False,
                "competitor_sitemaps": [],
                "dark_mode": True,
                "visualization_type": "plotly",  # or "matplotlib"
                "last_analysis_date": None,
                "export_format": "csv",  # or "json", "excel"
                "prioritize_critical_issues": True,
                "ignore_query_strings": False,
            }
        self.state = st.session_state.validator_state
        
    def icon(self, name: str, color: str = "currentColor") -> str:
        """Return an icon SVG with specified color"""
        if name not in ICONS:
            return ""
        return ICONS[name].replace('stroke="currentColor"', f'stroke="{color}"')
        
    def load_css_and_javascript(self):
        """Load custom CSS and JavaScript for enhanced UI interactions"""
        st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)
        
        # Add custom JavaScript for interactive features
        st.markdown("""
        <script type="text/javascript">
        function toggleDetails(id) {
            const detailsElement = document.getElementById(id);
            if (detailsElement) {
                detailsElement.style.display = detailsElement.style.display === 'none' ? 'block' : 'none';
            }
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                // Show a toast notification
                const toast = document.createElement('div');
                toast.textContent = 'Copied to clipboard!';
                toast.style.position = 'fixed';
                toast.style.bottom = '20px';
                toast.style.right = '20px';
                toast.style.padding = '10px 20px';
                toast.style.backgroundColor = '#10B981';
                toast.style.color = 'white';
                toast.style.borderRadius = '8px';
                toast.style.zIndex = '9999';
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s ease-in-out';
                
                document.body.appendChild(toast);
                
                // Fade in
                setTimeout(() => {
                    toast.style.opacity = '1';
                }, 10);
                
                // Fade out and remove
                setTimeout(() => {
                    toast.style.opacity = '0';
                    setTimeout(() => {
                        document.body.removeChild(toast);
                    }, 300);
                }, 2000);
            });
        }
        
        // Add smooth scrolling to anchor links
        document.addEventListener('DOMContentLoaded', function() {
            const links = document.querySelectorAll('a[href^="#"]');
            for (const link of links) {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const targetId = this.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth'
                        });
                    }
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)
		
@st.cache_data(ttl=3600)
def load_sitemap(_self, url: str) -> Tuple[str, Dict]:
    """Load and parse sitemap XML with Streamlit caching"""
    info = {
        "status": "error",
        "message": "",
        "content_type": None,
        "size": 0,
        "is_gzipped": False
    }
    
    try:
        headers = {"User-Agent": _self.state["user_agent"]}
        response = requests.get(url, headers=headers, timeout=_self.state["timeout"])
        
        info["status"] = "success" if response.status_code == 200 else "error"
        info["message"] = f"HTTP Status: {response.status_code}"
        info["content_type"] = response.headers.get("Content-Type", "")
        info["size"] = len(response.content)
        info["is_gzipped"] = response.headers.get("Content-Encoding", "") == "gzip"
        
        if response.status_code != 200:
            return "", info
            
        return response.text, info
    except Exception as e:
        info["message"] = f"Error loading sitemap: {str(e)}"
        return "", info

    @st.cache_data(ttl=3600)
    def extract_urls_from_sitemap(_self, xml_content: str) -> Tuple[List[URLData], SitemapInfo]:
        """Extract URLs and metadata from sitemap XML with support for sitemap index"""
        sitemap_info = SitemapInfo(
            url="",
            type="unknown",
            urls_count=0
        )
        
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            urls = []
            
            # Check if this is a sitemap index
            sitemapindex = soup.find('sitemapindex')
            if sitemapindex:
                sitemap_info.type = "index"
                for sitemap in sitemapindex.find_all('sitemap'):
                    loc = sitemap.find('loc').text if sitemap.find('loc') else None
                    if loc:
                        sub_content, _ = _self.load_sitemap(loc)
                        sub_urls, _ = _self.extract_urls_from_sitemap(sub_content)
                        urls.extend(sub_urls)
                
                sitemap_info.urls_count = len(urls)
                return urls, sitemap_info
            
            # Process regular sitemap
            sitemap_info.type = "sitemap"
            sitemap_tag = soup.find('urlset')
            
            if not sitemap_tag:
                return [], sitemap_info
                
            for url in soup.find_all('url'):
                url_data = URLData(
                    url=url.find('loc').text if url.find('loc') else "",
                    lastmod=url.find('lastmod').text if url.find('lastmod') else None,
                    priority=url.find('priority').text if url.find('priority') else None,
                    changefreq=url.find('changefreq').text if url.find('changefreq') else None,
                    images=[img.find('image:loc').text for img in url.find_all('image:image') if img.find('image:loc')],
                    videos=[vid.find('video:content_loc').text for vid in url.find_all('video:video') if vid.find('video:content_loc')],
                    alternates=[
                        {"href": link.get('href'), "hreflang": link.get('hreflang')}
                        for link in url.find_all('xhtml:link')
                    ]
                )
                
                if url_data.url:
                    urls.append(url_data)
            
            sitemap_info.urls_count = len(urls)
            return urls, sitemap_info
            
        except Exception as e:
            st.error(f"Error parsing sitemap: {str(e)}")
            return [], sitemap_info
	async def test_url_async(self, url_data: URLData, session: aiohttp.ClientSession) -> URLData:
        """Test a single URL asynchronously and return results"""
        url = url_data.url
        headers = {"User-Agent": self.state["user_agent"]}
        
        try:
            start_time = time.time()
            async with session.get(
                url, 
                headers=headers, 
                timeout=self.state["timeout"],
                allow_redirects=self.state["follow_redirects"]
            ) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                status_code = response.status
                
                # Determine status group
                if status_code >= 200 and status_code < 300:
                    status_group = "2xx"
                elif status_code >= 300 and status_code < 400:
                    status_group = "3xx"
                elif status_code >= 400 and status_code < 500:
                    status_group = "4xx"
                elif status_code >= 500:
                    status_group = "5xx"
                else:
                    status_group = "error"
                
                # Get content type and length
                content_type = response.headers.get("Content-Type", "")
                content_length = int(response.headers.get("Content-Length", "0")) if "Content-Length" in response.headers else 0
                
                # Check for HTML content and extract more info if enabled
                if (self.state["content_analysis"] and 
                    content_type and 
                    "text/html" in content_type.lower()):
                    try:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract page title
                        title_tag = soup.find('title')
                        page_title = title_tag.text if title_tag else None
                        
                        # Extract meta description
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        meta_description = meta_desc.get('content') if meta_desc else None
                        
                        # Check indexability
                        robots_meta = soup.find('meta', attrs={'name': 'robots'})
                        indexability = True
                        if robots_meta and robots_meta.get('content'):
                            indexability = 'noindex' not in robots_meta.get('content').lower()
                        
                        # Extract canonical URL
                        canonical = soup.find('link', attrs={'rel': 'canonical'})
                        canonical_url = canonical.get('href') if canonical else None
                        
                        # Count H1 tags
                        h1_count = len(soup.find_all('h1'))
                        
                        # Update URL data with content info
                        url_data.page_title = page_title
                        url_data.meta_description = meta_description
                        url_data.indexability = indexability
                        url_data.canonical_url = canonical_url
                        url_data.h1_count = h1_count
                    except Exception as e:
                        pass
                
                # Update URL data
                url_data.status_code = status_code
                url_data.response_time = response_time
                url_data.redirected = len(response.history) > 0 if hasattr(response, 'history') else False
                url_data.final_url = str(response.url) if response.url != url else None
                url_data.status_group = status_group
                url_data.content_type = content_type
                url_data.content_length = content_length
                
            return url_data
            
        except asyncio.TimeoutError:
            url_data.status_code = "Timeout"
            url_data.response_time = self.state["timeout"] * 1000
            url_data.status_group = "error"
            return url_data
            
        except Exception as e:
            url_data.status_code = "Error"
            url_data.response_time = 0
            url_data.status_group = "error"
            url_data.error = str(e)
            return url_data

    async def test_urls_batch(self, urls: List[URLData]) -> List[URLData]:
        """Test multiple URLs in parallel using asyncio"""
        connector = aiohttp.TCPConnector(limit=self.state["concurrent_requests"])
        timeout = aiohttp.ClientTimeout(total=self.state["timeout"])
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for url_data in urls:
                # Add rate limiting if needed
                if self.state["rate_limit"] > 0:
                    await asyncio.sleep(self.state["rate_limit"] / 1000.0)
                
                task = asyncio.ensure_future(self.test_url_async(url_data, session))
                tasks.append(task)
            
            results = []
            for future in stqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Testing URLs"):
                result = await future
                results.append(result)
            
            return results

    def test_urls(self, urls: List[URLData]) -> List[URLData]:
        """Run asynchronous URL testing with progress tracking"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self.test_urls_batch(urls))
            return results
        finally:
            loop.close()
	def generate_html_sitemap(self, urls: List[URLData]) -> str:
        """Generate an interactive HTML sitemap from URL data"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Advanced HTML Sitemap</title>
            <style>
                :root {
                    --primary: #7676FA;
                    --secondary: #6C63FF;
                    --dark: #111827;
                    --card: #1F2937;
                    --text: #F9FAFB;
                    --text-secondary: #9CA3AF;
                    --success: #10B981;
                    --warning: #F59E0B;
                    --error: #EF4444;
                }
                
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    background-color: var(--dark);
                    color: var(--text);
                    line-height: 1.6;
                    padding: 2rem;
                }
                
                .sitemap-container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .sitemap-header {
                    text-align: center;
                    margin-bottom: 3rem;
                    padding-bottom: 1.5rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .sitemap-title {
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                    background: linear-gradient(90deg, #ffffff, #e0f2fe);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                
                .sitemap-subtitle {
                    color: var(--text-secondary);
                }
                
                .sitemap-stats {
                    display: flex;
                    justify-content: center;
                    gap: 2rem;
                    margin: 2rem 0;
                }
                
                .stat-item {
                    text-align: center;
                    background: rgba(31, 41, 55, 0.5);
                    backdrop-filter: blur(10px);
                    border-radius: 12px;
                    padding: 1.25rem;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    min-width: 150px;
                }
                
                .stat-value {
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 0.25rem;
                }
                
                .stat-label {
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                }
                
                .search-container {
                    margin-bottom: 2rem;
                }
                
                .search-input {
                    width: 100%;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    background: rgba(31, 41, 55, 0.5);
                    color: var(--text);
                    font-size: 1rem;
                }
                
                .filters {
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                    margin-bottom: 1.5rem;
                }
                
                .filter-chip {
                    display: inline-flex;
                    align-items: center;
                    padding: 0.4rem 0.75rem;
                    border-radius: 20px;
                    background: rgba(31, 41, 55, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    color: var(--text);
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-size: 0.875rem;
                }
                
                .filter-chip:hover, .filter-chip.active {
                    background-color: rgba(118, 118, 250, 0.2);
                    border-color: var(--primary);
                }
                
                .domain-section {
                    margin-bottom: 3rem;
                }
                
                .domain-title {
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                    padding-bottom: 0.5rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .url-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 1rem;
                    margin-bottom: 2rem;
                }
                
                .url-card {
                    background: rgba(31, 41, 55, 0.5);
                    backdrop-filter: blur(10px);
                    border-radius: 12px;
                    padding: 1.25rem;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    transition: all 0.3s ease;
                    cursor: pointer;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                }
                
                .url-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
                    border-color: rgba(118, 118, 250, 0.3);
                }
                
                .url-title {
                    font-weight: 600;
                    margin-bottom: 0.75rem;
                    word-break: break-word;
                }
                
                .url-meta {
                    color: var(--text-secondary);
                    font-size: 0.8125rem;
                    margin-top: auto;
                }
                
                .meta-item {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin-bottom: 0.25rem;
                }
                
                .media-badge {
                    display: inline-block;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    margin-right: 0.5rem;
                    margin-bottom: 0.5rem;
                }
                
                .media-badge.images {
                    background-color: rgba(16, 185, 129, 0.2);
                    color: var(--success);
                }
                
                .media-badge.videos {
                    background-color: rgba(245, 158, 11, 0.2);
                    color: var(--warning);
                }
                
                .footer {
                    text-align: center;
                    margin-top: 4rem;
                    padding-top: 2rem;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    color: var(--text-secondary);
                }
                
                .url-detail-modal {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.7);
                    z-index: 1000;
                    overflow-y: auto;
                }
                
                .modal-content {
                    position: relative;
                    background: var(--card);
                    margin: 5% auto;
                    padding: 2rem;
                    width: 80%;
                    max-width: 900px;
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                }
                
                .close-modal {
                    position: absolute;
                    top: 1rem;
                    right: 1rem;
                    font-size: 1.5rem;
                    cursor: pointer;
                }
                
                .modal-title {
                    margin-bottom: 1.5rem;
                    word-break: break-word;
                }
                
                .detail-section {
                    margin-bottom: 2rem;
                }
                
                .detail-title {
                    font-size: 1.25rem;
                    margin-bottom: 1rem;
                    font-weight: 600;
                }
                
                .detail-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 1rem;
                }
                
                .detail-item {
                    background-color: rgba(31, 41, 55, 0.3);
                    padding: 1rem;
                    border-radius: 8px;
                }
                
                .detail-label {
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                    margin-bottom: 0.25rem;
                }
                
                .detail-value {
                    font-weight: 600;
                }
                
                .media-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 1rem;
                }
                
                .media-item {
                    background-color: rgba(31, 41, 55, 0.3);
                    padding: 1rem;
                    border-radius: 8px;
                    word-break: break-word;
                }
                
                .language-links {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.75rem;
                }
                
                .language-link {
                    background-color: rgba(31, 41, 55, 0.3);
                    padding: 0.5rem 0.75rem;
                    border-radius: 8px;
                    font-size: 0.875rem;
                }
                
                .view-url-btn {
                    display: inline-block;
                    margin-top: 1rem;
                    padding: 0.5rem 1.5rem;
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    border: none;
                    cursor: pointer;
                }
                
                .view-url-btn:hover {
                    opacity: 0.9;
                    transform: translateY(-2px);
                }
                
                @media (max-width: 768px) {
                    body {
                        padding: 1rem;
                    }
                    
                    .sitemap-stats {
                        flex-direction: column;
                        gap: 1rem;
                    }
                    
                    .url-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .modal-content {
                        width: 95%;
                        margin: 5% auto;
                        padding: 1.5rem;
                    }
                    
                    .detail-grid {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="sitemap-container">
                <div class="sitemap-header">
                    <h1 class="sitemap-title">Interactive HTML Sitemap</h1>
                    <p class="sitemap-subtitle">Generated by Advanced Sitemap Validator</p>
                    
                    <div class="sitemap-stats">
                        <div class="stat-item">
                            <div class="stat-value" id="total-urls">0</div>
                            <div class="stat-label">Total URLs</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="total-images">0</div>
                            <div class="stat-label">Images</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="total-videos">0</div>
                            <div class="stat-label">Videos</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="total-domains">0</div>
                            <div class="stat-label">Domains</div>
                        </div>
                    </div>
                </div>
                
                <div class="search-container">
                    <input type="text" class="search-input" id="search-input" placeholder="Search URLs...">
                </div>
                
                <div class="filters">
                    <div class="filter-chip" data-filter="all">All</div>
                    <div class="filter-chip" data-filter="images">With Images</div>
                    <div class="filter-chip" data-filter="videos">With Videos</div>
                    <div class="filter-chip" data-filter="alternates">With Alternates</div>
                </div>
                
                <div id="domains-container">
                    <!-- Domain sections will be generated here -->
                </div>
                
                <div class="footer">
                    <p>Generated on <span id="generation-date"></span></p>
                    <p>Advanced Sitemap Validator Tool</p>
                </div>
            </div>
            
            <div class="url-detail-modal" id="url-modal">
                <div class="modal-content">
                    <span class="close-modal" id="close-modal">&times;</span>
                    <h2 class="modal-title" id="modal-url-title"></h2>
                    
                    <div class="detail-section">
                        <h3 class="detail-title">URL Information</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <div class="detail-label">Last Modified</div>
                                <div class="detail-value" id="detail-lastmod">N/A</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Priority</div>
                                <div class="detail-value" id="detail-priority">N/A</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Change Frequency</div>
                                <div class="detail-value" id="detail-changefreq">N/A</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section" id="images-section">
                        <h3 class="detail-title">Images</h3>
                        <div class="media-list" id="images-list"></div>
                    </div>
                    
                    <div class="detail-section" id="videos-section">
                        <h3 class="detail-title">Videos</h3>
                        <div class="media-list" id="videos-list"></div>
                    </div>
                    
                    <div class="detail-section" id="alternates-section">
                        <h3 class="detail-title">Alternate Language Versions</h3>
                        <div class="language-links" id="alternates-list"></div>
                    </div>
                    
                    <a href="#" class="view-url-btn" id="view-url-btn" target="_blank">Visit URL</a>
                </div>
            </div>
            
            <script>
                // Store all URL data as a JavaScript object
                const urlData = PLACEHOLDER_URL_DATA;
                
                // Group URLs by domain
                function groupByDomain(urls) {
                    const domains = {};
                    urls.forEach(url => {
                        try {
                            const domain = new URL(url.url).hostname;
                            if (!domains[domain]) {
                                domains[domain] = [];
                            }
                            domains[domain].push(url);
                        } catch (e) {
                            console.error('Invalid URL:', url.url);
                        }
                    });
                    return domains;
                }
                
                // Count stats
                function countStats(urls) {
                    let totalImages = 0;
                    let totalVideos = 0;
                    const domains = new Set();
                    
                    urls.forEach(url => {
                        try {
                            domains.add(new URL(url.url).hostname);
                            totalImages += url.images.length;
                            totalVideos += url.videos.length;
                        } catch (e) {
                            console.error('Invalid URL:', url.url);
                        }
                    });
                    
                    document.getElementById('total-urls').textContent = urls.length;
                    document.getElementById('total-images').textContent = totalImages;
                    document.getElementById('total-videos').textContent = totalVideos;
                    document.getElementById('total-domains').textContent = domains.size;
                }
                
                // Initialize
                document.addEventListener('DOMContentLoaded', () => {
                    // Set generation date
                    document.getElementById('generation-date').textContent = new Date().toLocaleString();
                    
                    // Initialize with all data
                    countStats(urlData);
                    renderDomains(groupByDomain(urlData));
                    
                    // Search input handler
                    document.getElementById('search-input').addEventListener('input', filterUrls);
                    
                    // Filter chip handlers
                    document.querySelectorAll('.filter-chip').forEach(chip => {
                        chip.addEventListener('click', () => {
                            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
                            chip.classList.add('active');
                            filterUrls();
                        });
                    });
                    
                    // Activate the "All" filter by default
                    document.querySelector('.filter-chip[data-filter="all"]').classList.add('active');
                });
            </script>
        </body>
        </html>
        """
        
        # Convert the URLData objects to simple dictionaries
        url_dicts = [url.to_dict() for url in urls]
        
        # Convert to JSON for embedding in JavaScript
        url_json = json.dumps(url_dicts)
        
        # Replace the placeholder with actual data
        html = html.replace("PLACEHOLDER_URL_DATA", url_json)
        
        return html
	def analyze_sitemap_health(self, urls: List[URLData], results: List[URLData]) -> AnalysisResult:
        """Analyze sitemap health and generate recommendations"""
        analysis = AnalysisResult()
        
        # Calculate metrics
        total_urls = len(urls)
        if total_urls == 0:
            return analysis
        
        success_count = sum(1 for r in results if r.status_group == "2xx")
        redirect_count = sum(1 for r in results if r.status_group == "3xx")
        error_count = sum(1 for r in results if r.status_group in ["4xx", "5xx", "error"])
        
        # Calculate health score (0-100)
        health_score = (success_count / total_urls) * 100
        analysis.health_score = round(health_score, 2)
        
        # Analyze issues
        if redirect_count > 0:
            analysis.issues.append({
                "type": "warning",
                "message": f"{redirect_count} URLs are redirecting"
            })
        
        if error_count > 0:
            analysis.issues.append({
                "type": "error",
                "message": f"{error_count} URLs are returning errors"
            })
        
        # Generate recommendations
        if redirect_count > 0:
            analysis.recommendations.append(
                "Update sitemap with final URLs to eliminate redirects"
            )
        
        if error_count > 0:
            analysis.recommendations.append(
                "Fix or remove broken URLs from the sitemap"
            )
        
        # Check lastmod dates
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        old_urls = 0
        for url in urls:
            if url.lastmod:
                parsed_date = self.parse_date(url.lastmod)
                if parsed_date and parsed_date < six_months_ago:
                    old_urls += 1
        
        if old_urls > 0:
            analysis.recommendations.append(
                f"Update lastmod dates for {old_urls} URLs that haven't been modified in 6 months"
            )
        
        # Store metrics
        analysis.metrics = {
            "total_urls": total_urls,
            "success_count": success_count,
            "redirect_count": redirect_count,
            "error_count": error_count,
            "old_urls": old_urls,
            "avg_response_time": round(sum(r.response_time for r in results if isinstance(r.response_time, (int, float))) / len(results) if results else 0, 2),
            "median_response_time": np.median([r.response_time for r in results if isinstance(r.response_time, (int, float))]) if results else 0,
            "images_count": sum(len(url.images) for url in urls),
            "videos_count": sum(len(url.videos) for url in urls),
            "alternates_count": sum(len(url.alternates) for url in urls)
        }
        
        return analysis

    def generate_visualizations(self, results: List[URLData]) -> Dict:
        """Generate visualization data for the sitemap analysis"""
        # Status distribution pie chart
        status_counts = {
            "Success (2xx)": sum(1 for r in results if r.status_group == "2xx"),
            "Redirects (3xx)": sum(1 for r in results if r.status_group == "3xx"),
            "Client Errors (4xx)": sum(1 for r in results if r.status_group == "4xx"),
            "Server Errors (5xx)": sum(1 for r in results if r.status_group == "5xx"),
            "Other Errors": sum(1 for r in results if r.status_group == "error")
        }
        
        status_fig = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="URL Status Distribution",
            color_discrete_map={
                "Success (2xx)": "#10B981",
                "Redirects (3xx)": "#F59E0B",
                "Client Errors (4xx)": "#EF4444",
                "Server Errors (5xx)": "#B00020",
                "Other Errors": "#718096"
            },
            template="plotly_dark"
        )
        
        status_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family="Inter, sans-serif",
                color="rgba(255,255,255,0.85)"
            ),
            margin=dict(t=40, b=0, l=0, r=0)
        )
        
        # Response time histogram
        response_times = [r.response_time for r in results if isinstance(r.response_time, (int, float))]
        
        time_fig = px.histogram(
            x=response_times,
            nbins=30,
            title="Response Time Distribution",
            labels={"x": "Response Time (ms)", "y": "Count"},
            color_discrete_sequence=["#7676FA"],
            template="plotly_dark"
        )
        
        time_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family="Inter, sans-serif",
                color="rgba(255,255,255,0.85)"
            ),
            margin=dict(t=40, b=40, l=40, r=20)
        )
        
        # Content type distribution
        content_types = {}
        for r in results:
            if not r.content_type:
                continue
            
            # Extract main content type
            main_type = r.content_type.split(';')[0].strip().split('/')
            if len(main_type) > 1:
                main_type = f"{main_type[0]}/{main_type[1]}"
            else:
                main_type = main_type[0]
                
            if main_type in content_types:
                content_types[main_type] += 1
            else:
                content_types[main_type] = 1
        
        # Sort by count
        content_types = dict(sorted(content_types.items(), key=lambda x: x[1], reverse=True)[:8])
        
        content_fig = px.bar(
            x=list(content_types.keys()),
            y=list(content_types.values()),
            title="Content Type Distribution",
            labels={"x": "Content Type", "y": "Count"},
            color_discrete_sequence=["#6C63FF"],
            template="plotly_dark"
        )
        
        content_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family="Inter, sans-serif",
                color="rgba(255,255,255,0.85)"
            ),
            margin=dict(t=40, b=80, l=40, r=20),
            xaxis_tickangle=-45
        )
        
        return {
            "status_distribution": status_fig,
            "response_times": time_fig,
            "content_types": content_fig
        }
	def main():
    st.set_page_config(
        page_title="Advanced Sitemap Validator & Analyzer",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Create and load validator instance
    validator = SitemapValidator()
    validator.load_css_and_javascript()

    # App Header with modern design
    st.markdown("""
    <div class="app-header">
        <div class="app-logo">
            <div class="logo-icon">🔍</div>
            <div>
                <h1 class="app-title">Advanced Sitemap Validator & Analyzer</h1>
                <p class="app-subtitle">Comprehensive tool for validating, testing, and optimizing XML sitemaps for better SEO</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero section for first-time users
    if not st.session_state.get('sitemap_data', {}).get('urls'):
        st.markdown("""
        <div class="hero-section">
            <div class="hero-subtitle">SEO OPTIMIZATION TOOL</div>
            <h2 class="hero-title">Improve Your Site's Visibility</h2>
            <p class="hero-description">
                Validate your XML sitemaps, identify issues, and get actionable recommendations to enhance your website's SEO performance.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Create columns for the main input form
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sitemap_url = st.text_input(
            "Enter Sitemap URL or Website URL",
            placeholder="https://example.com/sitemap.xml",
            value=st.session_state.get('sitemap_data', {}).get('sitemap_url', "")
        )
    
    with col2:
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            detect_button = st.button("🔍 Detect", use_container_width=True)
        with col2_2:
            load_button = st.button("📥 Load", use_container_width=True)
    
    # Advanced options in an expander
    with st.expander("⚙️ Advanced Options", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            validator.state["concurrent_requests"] = st.slider(
                "Concurrent Requests",
                min_value=1,
                max_value=20,
                value=validator.state["concurrent_requests"]
            )
            
            validator.state["content_analysis"] = st.checkbox(
                "Analyze Page Content",
                value=validator.state["content_analysis"],
                help="Extract and analyze HTML content from URLs"
            )
        
        with col2:
            validator.state["timeout"] = st.slider(
                "Timeout (seconds)",
                min_value=1,
                max_value=30,
                value=validator.state["timeout"]
            )
            
            validator.state["follow_redirects"] = st.checkbox(
                "Follow Redirects",
                value=validator.state["follow_redirects"],
                help="Follow URL redirects to final destination"
            )
        
        with col3:
            validator.state["max_urls_to_check"] = st.number_input(
                "Max URLs to Check",
                min_value=10,
                max_value=10000,
                value=validator.state["max_urls_to_check"],
                help="Limit the number of URLs to test"
            )
            
            validator.state["check_ssl"] = st.checkbox(
                "Verify SSL Certificates",
                value=validator.state["check_ssl"],
                help="Check for SSL certificate issues"
            )
    
    # Detect sitemaps
    if detect_button:
        if not sitemap_url:
            st.warning("Please enter a website URL")
        else:
            with st.spinner("Detecting sitemaps..."):
                detected_sitemaps = validator.detect_sitemaps(sitemap_url)
                if detected_sitemaps:
                    st.success(f"Found {len(detected_sitemaps)} sitemaps!")
                    selected_sitemap = st.selectbox(
                        "Select a sitemap",
                        options=detected_sitemaps
                    )
                    sitemap_url = selected_sitemap
                else:
                    st.warning("No sitemaps found. Try entering a sitemap URL manually.")
    
    # Load sitemap
    if load_button:
        if not sitemap_url:
            st.warning("Please enter a sitemap URL")
        else:
            with st.spinner("Loading and parsing sitemap..."):
                sitemap_content, info = validator.load_sitemap(sitemap_url)
                
                if info["status"] == "success" and sitemap_content:
                    urls, sitemap_info = validator.extract_urls_from_sitemap(sitemap_content)
                    robots_txt_data = validator.check_robots_txt(sitemap_url)
                    
                    # Save to session state
                    if 'sitemap_data' not in st.session_state:
                        st.session_state.sitemap_data = {}
                        
                    st.session_state.sitemap_data.update({
                        "sitemap_url": sitemap_url,
                        "sitemap_content": sitemap_content,
                        "urls": urls,
                        "sitemap_info": sitemap_info,
                        "robots_txt_data": robots_txt_data
                    })
                    
                    st.success(f"✅ Successfully loaded {len(urls)} URLs from sitemap")
                else:
                    st.error(f"❌ Failed to load sitemap: {info['message']}")
    
    # Show tabs with analysis if data is loaded
    if st.session_state.get('sitemap_data', {}).get('urls'):
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard",
            "🔍 URL Validation",
            "📈 Visualizations",
            "🤖 Robots.txt",
            "🗺️ HTML Sitemap"
        ])
        
        urls = st.session_state.sitemap_data["urls"]
        
        with tab1:
            st.subheader("Dashboard")
            
            # Create a modern stat card layout
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div style="color: {THEME['colors']['primary']}">
                        {validator.icon('globe', THEME['colors']['primary'])}
                    </div>
                    <div class="stat-card-value">{len(urls)}</div>
                    <div class="stat-card-label">Total URLs</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                total_images = sum(len(url.images) for url in urls)
                st.markdown(f"""
                <div class="stat-card">
                    <div style="color: {THEME['colors']['success']}">
                        {validator.icon('image', THEME['colors']['success'])}
                    </div>
                    <div class="stat-card-value">{total_images}</div>
                    <div class="stat-card-label">Total Images</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                total_videos = sum(len(url.videos) for url in urls)
                st.markdown(f"""
                <div class="stat-card">
                    <div style="color: {THEME['colors']['warning']}">
                        {validator.icon('video', THEME['colors']['warning'])}
                    </div>
                    <div class="stat-card-value">{total_videos}</div>
                    <div class="stat-card-label">Total Videos</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                total_alternates = sum(len(url.alternates) for url in urls)
                st.markdown(f"""
                <div class="stat-card">
                    <div style="color: {THEME['colors']['secondary']}">
                        {validator.icon('globe', THEME['colors']['secondary'])}
                    </div>
                    <div class="stat-card-value">{total_alternates}</div>
                    <div class="stat-card-label">Alternate URLs</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Show health analysis if available
            if st.session_state.sitemap_data.get("analysis"):
                analysis = st.session_state.sitemap_data["analysis"]
                
                st.markdown("<h3 style='margin-top: 2rem;'>Health Score</h3>", unsafe_allow_html=True)
                
                # Health score gauge
                score = analysis.health_score
                color = "#10B981" if score >= 90 else "#F59E0B" if score >= 70 else "#EF4444"
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"""
                    <div class="radial-progress">
                        <svg width="120" height="120">
                            <circle class="bg" cx="60" cy="60" r="54" stroke="rgba(255, 255, 255, 0.1)"></circle>
                            <circle class="progress" cx="60" cy="60" r="54" 
                                stroke="{color}" 
                                stroke-dasharray="{score * 3.39} 339" 
                                transform="rotate(-90 60 60)">
                            </circle>
                        </svg>
                        <div class="radial-progress-text">{score}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Show issues
                    if analysis.issues:
                        for issue in analysis.issues:
                            if issue["type"] == "error":
                                st.markdown(f"""
                                <div class="alert alert-error">
                                    <div class="alert-icon">{validator.icon('error', THEME['colors']['error'])}</div>
                                    <div class="alert-content">
                                        <div class="alert-title">Error</div>
                                        <p class="alert-message">{issue["message"]}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="alert alert-warning">
                                    <div class="alert-icon">{validator.icon('alert', THEME['colors']['warning'])}</div>
                                    <div class="alert-content">
                                        <div class="alert-title">Warning</div>
                                        <p class="alert-message">{issue["message"]}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                
                # Show recommendations
                if analysis.recommendations:
                    st.markdown("<h3>Recommendations</h3>", unsafe_allow_html=True)
                    for rec in analysis.recommendations:
                        st.markdown(f"""
                        <div class="alert alert-info">
                            <div class="alert-icon">{validator.icon('info', "#3B82F6")}</div>
                            <div class="alert-content">
                                <p class="alert-message">{rec}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # URL Preview
            st.markdown("<h3 style='margin-top: 2rem;'>URL Preview</h3>", unsafe_allow_html=True)
            
            # Filter options
            search = st.text_input("🔍 Filter URLs", placeholder="Type to search...")
            
            # Create DataFrame for display
            df = pd.DataFrame([url.to_dict() for url in urls])
            
            # Apply filters
            if search:
                df = df[df["url"].str.contains(search, case=False, na=False)]
            
            st.dataframe(df)
            
        with tab2:
            st.subheader("URL Validation")
            
            if st.button("🚀 Test URLs"):
                with st.spinner("Testing URLs..."):
                    # Limit the number of URLs to test if needed
                    urls_to_test = urls[:validator.state["max_urls_to_check"]]
                    
                    # Test URLs
                    results = validator.test_urls(urls_to_test)
                    
                    # Generate analysis
                    analysis = validator.analyze_sitemap_health(urls_to_test, results)
                    visualizations = validator.generate_visualizations(results)
                    
                    # Save to session state
                    st.session_state.sitemap_data.update({
                        "validation_results": results,
                        "analysis": analysis,
                        "visualizations": visualizations
                    })
                    
                    st.success(f"✅ Tested {len(results)} URLs successfully!")
            
            # Show results if available
            if st.session_state.sitemap_data.get("validation_results"):
                results = st.session_state.sitemap_data["validation_results"]
                
                # Status summary
                col1, col2, col3, col4, col5 = st.columns(5)
                
                status_counts = {
                    "2xx": sum(1 for r in results if r.status_group == "2xx"),
                    "3xx": sum(1 for r in results if r.status_group == "3xx"),
                    "4xx": sum(1 for r in results if r.status_group == "4xx"),
                    "5xx": sum(1 for r in results if r.status_group == "5xx"),
                    "error": sum(1 for r in results if r.status_group == "error")
                }
                
                with col1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div style="color: {THEME['colors']['success']}">✓</div>
                        <div class="stat-card-value">{status_counts['2xx']}</div>
                        <div class="stat-card-label">Success (2xx)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div style="color: {THEME['colors']['warning']}">↪</div>
                        <div class="stat-card-value">{status_counts['3xx']}</div>
                        <div class="stat-card-label">Redirects (3xx)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div style="color: {THEME['colors']['error']}">✗</div>
                        <div class="stat-card-value">{status_counts['4xx']}</div>
                        <div class="stat-card-label">Client Errors (4xx)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div style="color: {THEME['colors']['error']}">⚠</div>
                        <div class="stat-card-value">{status_counts['5xx']}</div>
                        <div class="stat-card-label">Server Errors (5xx)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div style="color: {THEME['colors']['text_secondary']}">?</div>
                        <div class="stat-card-value">{status_counts['error']}</div>
                        <div class="stat-card-label">Other Errors</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Results table with filtering
                st.subheader("Detailed Results")
                
                # Create DataFrame
                results_df = pd.DataFrame([r.to_dict() for r in results])
                
                # Add filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_filter = st.multiselect(
                        "Filter by Status",
                        options=["2xx", "3xx", "4xx", "5xx", "error"],
                        default=[]
                    )
                with col2:
                    min_time = st.number_input("Min Response Time (ms)", value=0)
                with col3:
                    content_filter = st.text_input("Filter by Content Type")
                
                # Apply filters
                filtered_df = results_df.copy()
                if status_filter:
                    filtered_df = filtered_df[filtered_df["status_group"].isin(status_filter)]
                filtered_df = filtered_df[filtered_df["response_time"] >= min_time]
                if content_filter:
                    filtered_df = filtered_df[filtered_df["content_type"].str.contains(content_filter, case=False, na=False)]
                
                st.dataframe(filtered_df)
                
                # Export options
                if st.button("📥 Export Results"):
                    if validator.state["export_format"] == "csv":
                        csv = filtered_df.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="sitemap_results.csv" class="download-button">Download CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    elif validator.state["export_format"] == "json":
                        json_str = filtered_df.to_json(orient="records")
                        b64 = base64.b64encode(json_str.encode()).decode()
                        href = f'<a href="data:application/json;base64,{b64}" download="sitemap_results.json" class="download-button">Download JSON</a>'
                        st.markdown(href, unsafe_allow_html=True)
        
        with tab3:
            st.subheader("Visualizations")
            
            if st.session_state.sitemap_data.get("visualizations"):
                visualizations = st.session_state.sitemap_data["visualizations"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(visualizations["status_distribution"], use_container_width=True)
                with col2:
                    st.plotly_chart(visualizations["response_times"], use_container_width=True)
                
                st.plotly_chart(visualizations["content_types"], use_container_width=True)
            else:
                st.info("Run URL testing to see visualizations")
        
        with tab4:
            st.subheader("Robots.txt Analysis")
            
            robots_data = st.session_state.sitemap_data.get("robots_txt_data")
            if robots_data:
                if robots_data["found"]:
                    st.markdown(f"""
                    <div class="alert alert-success">
                        <div class="alert-icon">{validator.icon('check', THEME['colors']['success'])}</div>
                        <div class="alert-content">
                            <div class="alert-title">robots.txt found</div>
                            <p class="alert-message">The website has a robots.txt file.</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if robots_data["sitemap_declared"]:
                        st.markdown(f"""
                        <div class="alert alert-success">
                            <div class="alert-icon">{validator.icon('check', THEME['colors']['success'])}</div>
                            <div class="alert-content">
                                <div class="alert-title">Sitemap declared</div>
                                <p class="alert-message">The sitemap is properly declared in robots.txt.</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="alert alert-warning">
                            <div class="alert-icon">{validator.icon('alert', THEME['colors']['warning'])}</div>
                            <div class="alert-content">
                                <div class="alert-title">Sitemap not declared</div>
                                <p class="alert-message">The sitemap is not declared in robots.txt. Consider adding it for better SEO.</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if robots_data["sitemaps"]:
                        st.subheader("Sitemaps in robots.txt")
                        for sitemap in robots_data["sitemaps"]:
                            st.markdown(f"- `{sitemap}`")
                    
                    if robots_data["content"]:
                        st.subheader("robots.txt Content")
                        st.code(robots_data["content"], language="text")
                else:
                    st.markdown(f"""
                    <div class="alert alert-error">
                        <div class="alert-icon">{validator.icon('error', THEME['colors']['error'])}</div>
                        <div class="alert-content">
                            <div class="alert-title">robots.txt not found</div>
                            <p class="alert-message">The website does not have a robots.txt file. Consider adding one for better search engine crawling.</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab5:
            st.subheader("HTML Sitemap Generator")
            
            if st.button("Generate HTML Sitemap"):
                with st.spinner("Generating HTML sitemap..."):
                    html_sitemap = validator.generate_html_sitemap(urls)
                    
                    # Show preview
                    st.subheader("Preview")
                    st.components.v1.html(html_sitemap, height=600, scrolling=True)
                    
                    # Download option
                    b64 = base64.b64encode(html_sitemap.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="sitemap.html" class="download-button">Download HTML Sitemap</a>'
                    st.markdown(href, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div>Advanced Sitemap Validator & Analyzer | A modern SEO tool</div>
        <div style="font-size: 0.75rem; margin-top: 0.5rem;">© 2024 | Built with Streamlit</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
