import streamlit as st
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta
import re
from typing import Dict, List, Any, Union
import concurrent.futures
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64
from urllib.parse import urlparse
import json
from pathlib import Path
import time
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import hashlib
from functools import lru_cache

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
        # Initialize state in session_state instead of instance variable
        if 'validator_state' not in st.session_state:
            st.session_state.validator_state = {
                "urls": [],
                "concurrent_requests": 5,
                "timeout": 10,
                "user_agent": "Mozilla/5.0 (Streamlit Sitemap Validator)",
                "status_counts": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0},
                "history": []
            }
        self.state = st.session_state.validator_state

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_sitemap(_self, url: str) -> str:
        """Load and parse sitemap XML with Streamlit caching"""
        try:
            response = requests.get(url, headers={"User-Agent": _self.state["user_agent"]})
            return response.text
        except Exception as e:
            return f"Error loading sitemap: {str(e)}"

    @st.cache_data(ttl=3600)
    def extract_urls_from_sitemap(_self, xml_content: str) -> List[Dict]:
        """Extract URLs and metadata from sitemap XML with support for sitemap index"""
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            urls = []
            
            # Check if this is a sitemap index
            sitemapindex = soup.find('sitemapindex')
            if sitemapindex:
                for sitemap in sitemapindex.find_all('sitemap'):
                    loc = sitemap.find('loc').text
                    sub_content = _self.load_sitemap(loc)
                    urls.extend(_self.extract_urls_from_sitemap(sub_content))
                return urls
            
            # Process regular sitemap
            for url in soup.find_all('url'):
                url_data = {
                    "url": url.find('loc').text if url.find('loc') else None,
                    "lastmod": url.find('lastmod').text if url.find('lastmod') else None,
                    "priority": url.find('priority').text if url.find('priority') else None,
                    "changefreq": url.find('changefreq').text if url.find('changefreq') else None,
                    "images": [img.find('loc').text for img in url.find_all('image:image')],
                    "videos": [vid.find('video:content_loc').text for vid in url.find_all('video:video')],
                    "alternates": [
                        {"href": link.get('href'), "hreflang": link.get('hreflang')}
                        for link in url.find_all('xhtml:link')
                    ]
                }
                if url_data["url"]:
                    urls.append(url_data)
            
            return urls
        except Exception as e:
            st.error(f"Error parsing sitemap: {str(e)}")
            return []

    def generate_html_sitemap(self, urls: List[Dict]) -> str:
        """Generate an HTML sitemap from URL data"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>HTML Sitemap</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 2rem; }
                .sitemap { max-width: 1200px; margin: 0 auto; }
                .url-group { margin-bottom: 2rem; }
                .url-item { margin: 0.5rem 0; padding: 0.5rem; border-bottom: 1px solid #eee; }
                .url-item:hover { background-color: #f5f5f5; }
                .meta { color: #666; font-size: 0.9em; }
                .alternates { margin-left: 1rem; font-size: 0.9em; color: #0066cc; }
            </style>
        </head>
        <body>
            <div class="sitemap">
                <h1>HTML Sitemap</h1>
        """
        
        # Group URLs by domain
        domains = {}
        for url_data in urls:
            domain = urlparse(url_data["url"]).netloc
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(url_data)
        
        # Generate HTML for each domain
        for domain, domain_urls in domains.items():
            html += f'<div class="url-group"><h2>{domain}</h2>'
            for url_data in domain_urls:
                html += f"""
                <div class="url-item">
                    <a href="{url_data['url']}">{url_data['url']}</a>
                    <div class="meta">
                        Last Modified: {url_data.get('lastmod', 'N/A')} | 
                        Priority: {url_data.get('priority', 'N/A')} | 
                        Change Frequency: {url_data.get('changefreq', 'N/A')}
                    </div>
                """
                if url_data.get('alternates'):
                    html += '<div class="alternates">Alternate versions:<br>'
                    for alt in url_data['alternates']:
                        html += f'<a href="{alt["href"]}">{alt["hreflang"]}</a><br>'
                    html += '</div>'
                html += '</div>'
            html += '</div>'
        
        html += """
            </div>
        </body>
        </html>
        """
        return html

    def analyze_sitemap_health(self, urls: List[Dict], results: List[Dict]) -> Dict:
        """Analyze sitemap health and generate recommendations"""
        analysis = {
            "health_score": 0,
            "issues": [],
            "recommendations": [],
            "metrics": {}
        }
        
        # Calculate metrics
        total_urls = len(urls)
        if total_urls == 0:
            return analysis
        
        success_count = sum(1 for r in results if r["status_group"] == "2xx")
        redirect_count = sum(1 for r in results if r["status_group"] == "3xx")
        error_count = sum(1 for r in results if r["status_group"] in ["4xx", "5xx", "error"])
        
        # Calculate health score (0-100)
        health_score = (success_count / total_urls) * 100
        analysis["health_score"] = round(health_score, 2)
        
        # Analyze issues
        if redirect_count > 0:
            analysis["issues"].append({
                "type": "warning",
                "message": f"{redirect_count} URLs are redirecting"
            })
        
        if error_count > 0:
            analysis["issues"].append({
                "type": "error",
                "message": f"{error_count} URLs are returning errors"
            })
        
        # Generate recommendations
        if redirect_count > 0:
            analysis["recommendations"].append(
                "Update sitemap with final URLs to eliminate redirects"
            )
        
        if error_count > 0:
            analysis["recommendations"].append(
                "Fix or remove broken URLs from the sitemap"
            )
        
        # Check lastmod dates
        old_urls = sum(1 for url in urls if url.get("lastmod") and 
                      datetime.fromisoformat(url["lastmod"].replace('Z', '+00:00')) < 
                      datetime.now() - timedelta(days=180))
        if old_urls > 0:
            analysis["recommendations"].append(
                f"Update lastmod dates for {old_urls} URLs that haven't been modified in 6 months"
            )
        
        # Store metrics
        analysis["metrics"] = {
            "total_urls": total_urls,
            "success_count": success_count,
            "redirect_count": redirect_count,
            "error_count": error_count,
            "old_urls": old_urls
        }
        
        return analysis

    def generate_visualizations(self, results: List[Dict]) -> Dict:
        """Generate visualization data for the sitemap analysis"""
        # Status distribution pie chart
        status_counts = {
            "Success (2xx)": sum(1 for r in results if r["status_group"] == "2xx"),
            "Redirects (3xx)": sum(1 for r in results if r["status_group"] == "3xx"),
            "Client Errors (4xx)": sum(1 for r in results if r["status_group"] == "4xx"),
            "Server Errors (5xx)": sum(1 for r in results if r["status_group"] == "5xx"),
            "Other Errors": sum(1 for r in results if r["status_group"] == "error")
        }
        
        status_fig = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="URL Status Distribution",
            color_discrete_map={
                "Success (2xx)": "#00C49A",
                "Redirects (3xx)": "#FFB347",
                "Client Errors (4xx)": "#FF6B6B",
                "Server Errors (5xx)": "#B00020",
                "Other Errors": "#718096"
            }
        )
        
        # Response time histogram
        response_times = [r["response_time"] for r in results if isinstance(r["response_time"], (int, float))]
        time_fig = px.histogram(
            x=response_times,
            nbins=30,
            title="Response Time Distribution",
            labels={"x": "Response Time (ms)", "y": "Count"},
            color_discrete_sequence=["#4D77FF"]
        )
        
        return {
            "status_distribution": status_fig,
            "response_times": time_fig
        }

    def save_history(self, analysis_data: Dict):
        """Save analysis history in session state"""
        if 'analysis_history' not in st.session_state:
            st.session_state.analysis_history = []
            
        timestamp = datetime.now().isoformat()
        st.session_state.analysis_history.append({
            "timestamp": timestamp,
            "metrics": analysis_data["metrics"],
            "health_score": analysis_data["health_score"]
        })
        
        # Keep only last 30 days of history
        st.session_state.analysis_history = [
            h for h in st.session_state.analysis_history
            if datetime.fromisoformat(h["timestamp"]) > datetime.now() - timedelta(days=30)
        ]

    def generate_trend_chart(self) -> go.Figure:
        """Generate trend chart from historical data in session state"""
        if not st.session_state.get('analysis_history'):
            return None
        
        df = pd.DataFrame(st.session_state.analysis_history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["health_score"],
            mode="lines+markers",
            name="Health Score",
            line=dict(color="#4D77FF")
        ))
        
        fig.update_layout(
            title="Sitemap Health Score Trend",
            xaxis_title="Date",
            yaxis_title="Health Score",
            hovermode="x unified"
        )
        
        return fig

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
            "robots_txt_data": None,
            "analysis": None,
            "visualizations": None
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
                            "robots_txt_data": robots_txt_data,
                            "validation_results": None,
                            "analysis": None,
                            "visualizations": None
                        }
                        
                        st.success(f"Loaded {len(urls)} URLs from sitemap")
                    else:
                        st.error("Failed to load sitemap")

    # Show analysis if data is available
    if st.session_state.sitemap_data.get("urls"):
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Dashboard",
            "URL Testing",
            "Visualizations",
            "Robots.txt",
            "HTML Sitemap"
        ])
        
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
            
            # Show health analysis if available
            if st.session_state.sitemap_data.get("analysis"):
                analysis = st.session_state.sitemap_data["analysis"]
                st.metric("Health Score", f"{analysis['health_score']}%")
                
                if analysis["issues"]:
                    st.subheader("Issues")
                    for issue in analysis["issues"]:
                        if issue["type"] == "error":
                            st.error(issue["message"])
                        else:
                            st.warning(issue["message"])
                
                if analysis["recommendations"]:
                    st.subheader("Recommendations")
                    for rec in analysis["recommendations"]:
                        st.info(rec)
            
            # Show URL table with filtering
            st.subheader("URLs")
            df = pd.DataFrame(urls)
            
            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input("🔍 Filter URLs", "")
            with col2:
                has_media = st.checkbox("Show only URLs with media")
            
            if search:
                df = df[df["url"].str.contains(search, case=False)]
            if has_media:
                df = df[df.apply(lambda x: len(x["images"]) + len(x["videos"]) > 0, axis=1)]
            
            st.dataframe(df)
            
        with tab2:
            st.subheader("URL Testing")
            
            # Test settings
            with st.expander("⚙️ Test Settings"):
                col1, col2 = st.columns(2)
                with col1:
                    validator.state["concurrent_requests"] = st.slider(
                        "Concurrent Requests",
                        min_value=1,
                        max_value=20,
                        value=5
                    )
                with col2:
                    validator.state["timeout"] = st.slider(
                        "Timeout (seconds)",
                        min_value=1,
                        max_value=30,
                        value=10
                    )
            
            if st.button("Test URLs"):
                with st.spinner("Testing URLs..."):
                    results = []
                    urls = st.session_state.sitemap_data["urls"]
                    
                    progress = st.progress(0)
                    for i, url in enumerate(urls):
                        result = validator.test_url(url)
                        results.append(result)
                        progress.progress((i + 1) / len(urls))
                    
                    # Generate analysis and visualizations
                    analysis = validator.analyze_sitemap_health(urls, results)
                    visualizations = validator.generate_visualizations(results)
                    
                    # Save to session state
                    st.session_state.sitemap_data.update({
                        "validation_results": results,
                        "analysis": analysis,
                        "visualizations": visualizations
                    })
                    
                    # Save to history
                    validator.save_history(analysis)
                    
                    st.success("Testing complete!")
            
            # Show results if available
            if st.session_state.sitemap_data.get("validation_results"):
                results = st.session_state.sitemap_data["validation_results"]
                
                # Status summary
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
                
                # Results table with filtering
                st.subheader("Detailed Results")
                results_df = pd.DataFrame(results)
                
                # Add filters
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect(
                        "Filter by Status",
                        options=["2xx", "3xx", "4xx", "5xx", "error"],
                        default=[]
                    )
                with col2:
                    min_time = st.number_input("Min Response Time (ms)", value=0)
                
                if status_filter:
                    results_df = results_df[results_df["status_group"].isin(status_filter)]
                results_df = results_df[results_df["response_time"] >= min_time]
                
                st.dataframe(results_df)
                
                # Export options
                if st.button("📥 Export Results"):
                    csv = results_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="sitemap_results.csv" class="download-button">Download CSV</a>'
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
                
                # Show trend chart
                trend_chart = validator.generate_trend_chart()
                if trend_chart:
                    st.plotly_chart(trend_chart, use_container_width=True)
            else:
                st.info("Run URL testing to see visualizations")
        
        with tab4:
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
                    
                    if robots_data["content"]:
                        st.subheader("robots.txt Content")
                        st.code(robots_data["content"], language="text")
                else:
                    st.error("❌ robots.txt not found")
        
        with tab5:
            st.subheader("HTML Sitemap")
            
            if st.button("Generate HTML Sitemap"):
                with st.spinner("Generating HTML sitemap..."):
                    html_sitemap = validator.generate_html_sitemap(
                        st.session_state.sitemap_data["urls"]
                    )
                    
                    # Show preview
                    st.subheader("Preview")
                    st.components.v1.html(html_sitemap, height=400, scrolling=True)
                    
                    # Download option
                    b64 = base64.b64encode(html_sitemap.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="sitemap.html" class="download-button">Download HTML Sitemap</a>'
                    st.markdown(href, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        <div>Sitemap Validator & Analyzer | Built with Streamlit</div>
        <div style="font-size: 0.75rem; color: rgba(250, 250, 250, 0.5);">© 2024 | Modern design</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
