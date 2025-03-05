import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import urllib.parse
from datetime import datetime
import re
from typing import Dict, List, Any
import concurrent.futures
import numpy as np
import plotly.express as px
import base64
from urllib.parse import urlparse

# Define styles in a separate string
CUSTOM_STYLES = """
<style>
.media-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow: hidden;
}
.media-table thead th {
    background-color: #262730;
    padding: 0.75rem 1rem;
    text-align: left;
    color: rgba(250, 250, 250, 0.7);
}
.media-table tbody td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(250, 250, 250, 0.05);
}
.media-table tbody tr:nth-child(odd) {
    background-color: rgba(250, 250, 250, 0.02);
}
.media-table tbody tr:hover {
    background-color: rgba(250, 250, 250, 0.05);
}
.app-header {
    padding: 1rem;
    background-color: #262730;
    border-radius: 10px;
    margin-bottom: 2rem;
}
.app-logo {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.app-title {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
}
.app-subtitle {
    margin: 0;
    font-size: 0.875rem;
    color: rgba(250, 250, 250, 0.7);
}
.grid-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}
.grid-item-3 {
    grid-column: span 1;
}
.grid-item-6 {
    grid-column: span 2;
}
.footer {
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
    border-top: 1px solid rgba(250, 250, 250, 0.1);
}
.status-ok {
    color: #00C49A;
}
.status-warning {
    color: #FFB347;
}
.status-error {
    color: #FF6B6B;
}
.download-button {
    display: inline-block;
    padding: 0.5rem 1rem;
    background-color: #4D77FF;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    margin-top: 1rem;
}
.download-button:hover {
    background-color: #3D67FF;
}
</style>
"""

class SitemapValidator:
    def __init__(self):
        self.state = {
            "urls": [],
            "concurrent_requests": 5,
            "timeout": 10,
            "user_agent": "Mozilla/5.0 (Streamlit Sitemap Validator)",
            "status_counts": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0}
        }

    def load_sitemap(self, url: str) -> str:
        """Load and parse sitemap XML"""
        try:
            response = requests.get(url, headers={"User-Agent": self.state["user_agent"]})
            return response.text
        except Exception as e:
            return f"Error loading sitemap: {str(e)}"

    def extract_urls_from_sitemap(self, xml_content: str) -> List[Dict]:
        """Extract URLs and metadata from sitemap XML"""
        try:
            root = ET.fromstring(xml_content)
            urls = []
            
            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                url_data = {
                    "url": url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text,
                    "lastmod": url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod').text if url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod') is not None else None,
                    "priority": url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority').text if url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority') is not None else None,
                    "changefreq": url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq').text if url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq') is not None else None,
                    "images": [img.find('{http://www.google.com/schemas/sitemap-image/1.1}loc').text for img in url.findall('.//{http://www.google.com/schemas/sitemap-image/1.1}image')],
                    "videos": [vid.find('{http://www.google.com/schemas/sitemap-video/1.1}content_loc').text for vid in url.findall('.//{http://www.google.com/schemas/sitemap-video/1.1}video')]
                }
                urls.append(url_data)
            
            return urls
        except Exception as e:
            return []

    def test_url(self, url_data: Dict) -> Dict:
        """Test a single URL and return results"""
        url = url_data["url"]
        try:
            response = requests.get(
                url,
                headers={"User-Agent": self.state["user_agent"]},
                timeout=self.state["timeout"],
                allow_redirects=True
            )
            
            status_code = response.status_code
            response_time = response.elapsed.total_seconds() * 1000
            
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
            
            return {
                "url": url,
                "status_code": status_code,
                "response_time": response_time,
                "redirected": len(response.history) > 0,
                "final_url": response.url if len(response.history) > 0 else None,
                "status_group": status_group
            }
            
        except requests.Timeout:
            return {
                "url": url,
                "status_code": "Timeout",
                "response_time": self.state["timeout"] * 1000,
                "redirected": False,
                "final_url": None,
                "status_group": "error"
            }
        except Exception as e:
            return {
                "url": url,
                "status_code": "Error",
                "response_time": 0,
                "redirected": False,
                "final_url": None,
                "status_group": "error",
                "error": str(e)
            }

    def check_robots_txt(self, sitemap_url: str) -> Dict:
        """Check robots.txt for sitemap declaration"""
        try:
            parsed_url = urlparse(sitemap_url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = f"{domain}/robots.txt"
            
            response = requests.get(robots_url, headers={"User-Agent": self.state["user_agent"]})
            
            if response.status_code == 200:
                content = response.text
                sitemap_declared = bool(re.search(r'Sitemap:', content, re.IGNORECASE))
                sitemaps = re.findall(r'Sitemap:\s*(.*)', content)
                
                return {
                    "found": True,
                    "content": content,
                    "sitemap_declared": sitemap_declared,
                    "sitemaps": sitemaps
                }
            
            return {
                "found": False,
                "content": None,
                "sitemap_declared": False,
                "sitemaps": []
            }
            
        except Exception as e:
            return {
                "found": False,
                "content": f"Error: {str(e)}",
                "sitemap_declared": False,
                "sitemaps": []
            }

    def detect_sitemaps(self, url: str) -> List[str]:
        """Detect sitemaps for a given URL"""
        sitemaps = []
        try:
            # Check common sitemap locations
            common_paths = [
                "/sitemap.xml",
                "/sitemap_index.xml",
                "/sitemap-index.xml",
                "/sitemap.php",
                "/sitemap.txt"
            ]
            
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Check robots.txt first
            robots_data = self.check_robots_txt(url)
            if robots_data["sitemap_declared"]:
                sitemaps.extend(robots_data["sitemaps"])
            
            # Check common paths
            for path in common_paths:
                try:
                    sitemap_url = domain + path
                    response = requests.head(
                        sitemap_url,
                        headers={"User-Agent": self.state["user_agent"]},
                        timeout=5
                    )
                    if response.status_code == 200:
                        sitemaps.append(sitemap_url)
                except:
                    continue
            
            return list(set(sitemaps))  # Remove duplicates
            
        except Exception as e:
            return []

def main():
    st.set_page_config(
        page_title="Sitemap Validator & Analyzer",
        page_icon="🌐",
        layout="wide"
    )

    # Apply custom styles
    st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)

    # Initialize session state
    if 'sitemap_data' not in st.session_state:
        st.session_state.sitemap_data = {
            "sitemap_url": "",
            "sitemap_content": None,
            "urls": [],
            "validation_results": None,
            "robots_txt_data": None
        }

    # App Header
    st.markdown("""
    <div class="app-header">
        <div class="app-logo">
            <div style="font-size: 2.5rem;">🌐</div>
            <div>
                <h1 class="app-title">Sitemap Validator & Analyzer</h1>
                <p class="app-subtitle">Validate, test, and analyze XML sitemaps to improve SEO and website health</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main functionality
    validator = SitemapValidator()
    
    # Input form
    with st.form("sitemap_form"):
        sitemap_url = st.text_input(
            "Enter Sitemap URL",
            placeholder="https://example.com/sitemap.xml",
            value=st.session_state.sitemap_data.get("sitemap_url", "")
        )
        
        col1, col2 = st.columns(2)
        with col1:
            detect_button = st.form_submit_button("🔍 Detect Sitemaps", use_container_width=True)
        with col2:
            load_button = st.form_submit_button("📥 Load Sitemap", use_container_width=True)
        
        if detect_button:
            if not sitemap_url:
                st.warning("Please enter a website URL")
            else:
                with st.spinner("Detecting sitemaps..."):
                    detected_sitemaps = validator.detect_sitemaps(sitemap_url)
                    if detected_sitemaps:
                        st.success(f"Found {len(detected_sitemaps)} sitemaps!")
                        sitemap_url = st.selectbox(
                            "Select a sitemap",
                            options=detected_sitemaps
                        )
                    else:
                        st.warning("No sitemaps found. Try entering URL manually.")
        
        if load_button:
            if not sitemap_url:
                st.warning("Please enter a sitemap URL")
            else:
                with st.spinner("Loading sitemap..."):
                    sitemap_content = validator.load_sitemap(sitemap_url)
                    if sitemap_content:
                        urls = validator.extract_urls_from_sitemap(sitemap_content)
                        robots_txt_data = validator.check_robots_txt(sitemap_url)
                        
                        st.session_state.sitemap_data = {
                            "sitemap_url": sitemap_url,
                            "sitemap_content": sitemap_content,
                            "urls": urls,
                            "robots_txt_data": robots_txt_data
                        }
                        
                        st.success(f"Loaded {len(urls)} URLs from sitemap")
                    else:
                        st.error("Failed to load sitemap")

    # Show analysis if data is available
    if st.session_state.sitemap_data.get("urls"):
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["Dashboard", "URL Testing", "Robots.txt"])
        
        with tab1:
            st.subheader("Dashboard Overview")
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            
            urls = st.session_state.sitemap_data["urls"]
            total_images = sum(len(url["images"]) for url in urls)
            total_videos = sum(len(url["videos"]) for url in urls)
            
            with col1:
                st.metric("Total URLs", len(urls))
            with col2:
                st.metric("Total Images", total_images)
            with col3:
                st.metric("Total Videos", total_videos)
            
            # Show URL table
            st.dataframe(pd.DataFrame(urls))
            
        with tab2:
            st.subheader("URL Testing")
            if st.button("Test URLs"):
                with st.spinner("Testing URLs..."):
                    results = []
                    urls = st.session_state.sitemap_data["urls"]
                    
                    progress = st.progress(0)
                    for i, url in enumerate(urls):
                        result = validator.test_url(url)
                        results.append(result)
                        progress.progress((i + 1) / len(urls))
                    
                    st.session_state.sitemap_data["validation_results"] = results
                    st.success("Testing complete!")
                    
                    # Show results summary
                    status_counts = {
                        "2xx": sum(1 for r in results if r["status_group"] == "2xx"),
                        "3xx": sum(1 for r in results if r["status_group"] == "3xx"),
                        "4xx": sum(1 for r in results if r["status_group"] == "4xx"),
                        "5xx": sum(1 for r in results if r["status_group"] == "5xx"),
                        "error": sum(1 for r in results if r["status_group"] == "error")
                    }
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Success (2xx)", status_counts["2xx"])
                    with col2:
                        st.metric("Redirects (3xx)", status_counts["3xx"])
                    with col3:
                        st.metric("Client Errors (4xx)", status_counts["4xx"])
                    with col4:
                        st.metric("Server Errors (5xx)", status_counts["5xx"])
                    with col5:
                        st.metric("Other Errors", status_counts["error"])
            
            # Show results if available
            if st.session_state.sitemap_data.get("validation_results"):
                results_df = pd.DataFrame(st.session_state.sitemap_data["validation_results"])
                st.dataframe(results_df)
        
        with tab3:
            st.subheader("Robots.txt Analysis")
            robots_data = st.session_state.sitemap_data.get("robots_txt_data")
            
            if robots_data:
                if robots_data["found"]:
                    st.success("✅ robots.txt found")
                    if robots_data["sitemap_declared"]:
                        st.success("✅ Sitemap declared in robots.txt")
                    else:
                        st.warning("⚠️ Sitemap not declared in robots.txt")
                    
                    if robots_data["sitemaps"]:
                        st.subheader("Sitemaps in robots.txt")
                        for sitemap in robots_data["sitemaps"]:
                            st.write(f"- {sitemap}")
                else:
                    st.error("❌ robots.txt not found")

    # Footer
    st.markdown("""
    <div class="footer">
        <div>Sitemap Validator & Analyzer | Built with Streamlit</div>
        <div style="font-size: 0.75rem; color: rgba(250, 250, 250, 0.5);">© 2024 | Modern design</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
