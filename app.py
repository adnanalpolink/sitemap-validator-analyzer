import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import urllib.parse
import concurrent.futures
import time
import re
import matplotlib.pyplot as plt
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from urllib.parse import urlparse
import base64

# Page configuration
st.set_page_config(
    page_title="Sitemap Validator & Analyzer",
    layout="wide",
    page_icon="🌐",
    initial_sidebar_state="collapsed"
)

# Modern UI enhancements with CSS
st.markdown("""
<style>
    /* Global styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 1rem;
        max-width: 95%;
    }
    
    /* Typography */
    h1 {
        font-weight: 700;
        font-size: 2.25rem;
        margin-bottom: 0.75rem;
        color: #000000;
    }
    
    h2 {
        font-weight: 600;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        color: #000000;
    }
    
    h3 {
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
        color: #000000;
    }
    
    p {
        color: #000000;
    }
    
    /* Cards and containers */
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
        border: 1px solid #F1F5F9;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 0px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px 8px 0 0;
        gap: 8px;
        padding: 12px 16px;
        font-weight: 500;
        color: #64748B;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: #3B82F6;
        border-bottom: 2px solid #3B82F6;
        font-weight: 600;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 600;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #64748B;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 14px;
    }
    
    /* Status indicators */
    .status-ok {
        background-color: #ECFDF5;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-weight: 500;
        color: #10B981;
    }
    
    .status-warning {
        background-color: #FFFBEB;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-weight: 500;
        color: #F59E0B;
    }
    
    .status-error {
        background-color: #FEF2F2;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-weight: 500;
        color: #EF4444;
    }
    
    /* Form elements */
    div[data-baseweb="input"] {
        border-radius: 8px;
    }
    
    button[kind="primary"] {
        border-radius: 8px;
        background-color: #3B82F6;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    button[kind="primary"]:hover {
        background-color: #2563EB;
    }
    
    button[kind="secondary"] {
        border-radius: 8px;
        background-color: white;
        border: 1px solid #E2E8F0;
        color: #475569;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    button[kind="secondary"]:hover {
        background-color: #F8FAFC;
    }
    
    .stSlider > div > div > div {
        background-color: #F1F5F9;
    }
    
    .stSlider > div > div > div > div {
        background-color: #3B82F6;
    }
    
    .stProgress > div > div > div > div {
        background-color: #3B82F6;
    }
    
    /* Tables and dataframes */
    .dataframe {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
    
    .dataframe th {
        background-color: #F8FAFC;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        color: #475569;
        border-bottom: 1px solid #E2E8F0;
        white-space: nowrap;
    }
    
    .dataframe td {
        padding: 12px 16px;
        border-bottom: 1px solid #E2E8F0;
        color: #334155;
    }
    
    .dataframe tr:last-child td {
        border-bottom: none;
    }
    
    .dataframe tr:hover td {
        background-color: #F8FAFC;
    }
    
    /* Expandable sections */
    details {
        margin-bottom: 1rem;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        overflow: hidden;
    }
    
    summary {
        padding: 1rem;
        background-color: #F8FAFC;
        font-weight: 500;
        cursor: pointer;
    }
    
    details[open] summary {
        border-bottom: 1px solid #E2E8F0;
    }
    
    details > div {
        padding: 1rem;
    }

    /* Other elements */
    .small-info {
        font-size: 0.875rem;
        color: #64748B;
    }
    
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #94A3B8;
        font-size: 0.875rem;
        padding: 1.5rem 0;
        border-top: 1px solid #F1F5F9;
    }
    
    /* Download buttons */
    .download-button {
        display: inline-block;
        background-color: #3B82F6;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 500;
        margin-top: 0.5rem;
        transition: background-color 0.2s;
        text-align: center;
    }
    
    .download-button:hover {
        background-color: #2563EB;
    }
    
    /* Notification boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
    
    .stAlert > div {
        padding: 0.75rem 1rem;
        border-radius: 8px;
    }
    
    /* Charts */
    div.js-plotly-plot {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Control panel layout */
    .control-panel {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .control-panel > div {
        flex: 1;
    }
    
    /* Widget labels */
    .stTextInput > label,
    .stSlider > label,
    .stSelectbox > label {
        color: #000000;
        font-weight: 500;
        font-size: 0.875rem;
    }
    
    /* Ensure all text is visible across themes */
    .st-emotion-cache-ue6h4q, .st-emotion-cache-10trblm, .st-emotion-cache-q8sbsg p {
        color: #000000 !important;
    }
    
    .st-emotion-cache-1gulkj5 {
        color: #000000;
    }
    
    /* Fix for Streamlit default text colors */
    div.stMarkdown p, div.stMarkdown span, div.stMarkdown li {
        color: #000000 !important;
    }
    
    /* Make metric labels visible */
    div[data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, p {
            color: #FFFFFF !important;
        }
        
        .small-info {
            color: #E2E8F0 !important;
        }
        
        div.stMarkdown p, div.stMarkdown span, div.stMarkdown li {
            color: #FFFFFF !important;
        }
        
        div[data-testid="stMetricLabel"] {
            color: #FFFFFF !important;
        }
        
        .card {
            background-color: #1E293B;
            border-color: #334155;
        }
        
        .dataframe {
            border-color: #334155;
        }
        
        .dataframe th {
            background-color: #0F172A;
            color: #FFFFFF;
            border-bottom-color: #334155;
        }
        
        .dataframe td {
            border-bottom-color: #334155;
            color: #FFFFFF;
        }
        
        .dataframe tr:hover td {
            background-color: #1E293B;
        }
    }
</style>
""", unsafe_allow_html=True)

class SitemapValidator:
    def __init__(self):
        self.state = {
            "sitemap_url": "",
            "sitemap_content": None,
            "urls": [],
            "validation_results": None,
            "status_counts": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0},
            "is_processing": False,
            "concurrent_requests": 5,
            "timeout": 10,
            "user_agent": "Mozilla/5.0 (Streamlit Sitemap Validator)"
        }
        
    def detect_sitemaps(self, url):
        """Detect sitemap from a given URL by checking robots.txt and common patterns"""
        try:
            # Parse the base URL
            parsed_url = urlparse(url)
            origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Initialize sitemap URLs list
            sitemap_urls = []
            
            # Check robots.txt first
            try:
                robots_url = f"{origin}/robots.txt"
                response = requests.get(robots_url, timeout=5)
                if response.status_code == 200:
                    robots_text = response.text
                    # Extract sitemap URLs using regex
                    sitemap_matches = re.findall(r'Sitemap:\s*(https?://[^\s]+)', robots_text, re.IGNORECASE)
                    if sitemap_matches:
                        sitemap_urls.extend(sitemap_matches)
            except:
                pass
            
            # Common sitemap patterns to check
            sitemap_patterns = [
                '/sitemap.xml',
                '/sitemap_index.xml',
                '/sitemap-index.xml',
                '/post-sitemap.xml',
                '/page-sitemap.xml',
                '/product-sitemap.xml',
                '/category-sitemap.xml',
                '/wp-sitemap.xml',
                '/sitemap.php',
                '/sitemap.txt'
            ]
            
            # If no sitemaps found in robots.txt, try common patterns
            if not sitemap_urls:
                for pattern in sitemap_patterns:
                    sitemap_url = f"{origin}{pattern}"
                    try:
                        response = requests.head(sitemap_url, timeout=3)
                        if response.status_code == 200:
                            sitemap_urls.append(sitemap_url)
                    except:
                        continue
            
            return sitemap_urls
        except Exception as e:
            st.error(f"Error detecting sitemaps: {str(e)}")
            return []

    def load_sitemap(self, url):
        """Load sitemap from URL and parse contents"""
        try:
            headers = {
                'User-Agent': self.state["user_agent"],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=self.state["timeout"])
            if response.status_code != 200:
                st.error(f"Failed to load sitemap. Status code: {response.status_code}")
                return None
            
            sitemap_text = response.text
            self.state["sitemap_content"] = sitemap_text
            
            # Validate XML format
            validation_result = self.validate_sitemap_xml(sitemap_text)
            if not validation_result["valid"]:
                st.warning(f"Sitemap validation warning: {validation_result['error']}")
            
            # Extract URLs
            urls = self.extract_urls_from_sitemap(sitemap_text)
            self.state["urls"] = urls
            
            return sitemap_text
            
        except Exception as e:
            st.error(f"Error loading sitemap: {str(e)}")
            return None
    
    def validate_sitemap_xml(self, xml_content):
        """Validate sitemap XML structure"""
        try:
            # Parse XML content
            root = ET.fromstring(xml_content)
            
            # Check for namespace
            namespaces = root.attrib.get('xmlns')
            if not namespaces or "sitemaps.org/schemas/sitemap" not in namespaces:
                return {
                    "valid": False,
                    "error": "Missing or incorrect sitemap namespace"
                }
            
            # Check if it's a sitemap index
            is_sitemap_index = root.tag.endswith('sitemapindex')
            
            # Check for required elements
            if is_sitemap_index:
                sitemap_nodes = root.findall('.//{*}sitemap')
                if not sitemap_nodes:
                    return {
                        "valid": False,
                        "error": "No sitemap entries found in sitemap index"
                    }
                
                # Check for loc in each sitemap entry
                missing_loc = []
                for i, sitemap in enumerate(sitemap_nodes):
                    loc = sitemap.find('.//{*}loc')
                    if loc is None or not loc.text:
                        missing_loc.append(i + 1)
                
                if missing_loc:
                    return {
                        "valid": False,
                        "error": f"Missing loc element in sitemap entries: {', '.join(map(str, missing_loc))}"
                    }
            else:
                url_nodes = root.findall('.//{*}url')
                if not url_nodes:
                    return {
                        "valid": False,
                        "error": "No URL entries found in sitemap"
                    }
                
                # Check for loc in each URL entry
                missing_loc = []
                for i, url in enumerate(url_nodes):
                    loc = url.find('.//{*}loc')
                    if loc is None or not loc.text:
                        missing_loc.append(i + 1)
                
                if missing_loc:
                    return {
                        "valid": False,
                        "error": f"Missing loc element in URL entries: {', '.join(map(str, missing_loc))}"
                    }
            
            return {
                "valid": True
            }
            
        except ET.ParseError as e:
            return {
                "valid": False,
                "error": f"XML parsing error: {str(e)}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }

    def extract_urls_from_sitemap(self, sitemap_text):
        """Extract URLs, lastmod, and other data from sitemap"""
        try:
            root = ET.fromstring(sitemap_text)
            urls_data = []
            
            # Determine if it's a sitemap index
            is_sitemap_index = root.tag.endswith('sitemapindex')
            
            if is_sitemap_index:
                # Process sitemap index
                for sitemap in root.findall('.//{*}sitemap'):
                    loc_elem = sitemap.find('.//{*}loc')
                    lastmod_elem = sitemap.find('.//{*}lastmod')
                    
                    if loc_elem is not None and loc_elem.text:
                        url_data = {
                            "url": loc_elem.text.strip(),
                            "type": "sitemap",
                            "lastmod": lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else None
                        }
                        urls_data.append(url_data)
            else:
                # Process regular sitemap
                for url in root.findall('.//{*}url'):
                    loc_elem = url.find('.//{*}loc')
                    lastmod_elem = url.find('.//{*}lastmod')
                    changefreq_elem = url.find('.//{*}changefreq')
                    priority_elem = url.find('.//{*}priority')
                    
                    # Extract image data
                    images = []
                    for image in url.findall('.//{*}image'):
                        img_loc = image.find('.//{*}loc')
                        if img_loc is not None and img_loc.text:
                            images.append(img_loc.text.strip())
                    
                    # Extract video data
                    videos = []
                    for video in url.findall('.//{*}video'):
                        video_title = video.find('.//{*}title')
                        if video_title is not None and video_title.text:
                            videos.append(video_title.text.strip())
                    
                    if loc_elem is not None and loc_elem.text:
                        url_data = {
                            "url": loc_elem.text.strip(),
                            "lastmod": lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else None,
                            "changefreq": changefreq_elem.text.strip() if changefreq_elem is not None and changefreq_elem.text else None,
                            "priority": priority_elem.text.strip() if priority_elem is not None and priority_elem.text else None,
                            "images": images,
                            "videos": videos
                        }
                        urls_data.append(url_data)
            
            return urls_data
        
        except Exception as e:
            st.error(f"Error extracting URLs: {str(e)}")
            return []

    def test_url(self, url_data):
        """Test a single URL and return status info"""
        url = url_data["url"]
        try:
            headers = {
                'User-Agent': self.state["user_agent"],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            
            start_time = time.time()
            # Use GET instead of HEAD as some servers don't properly handle HEAD requests
            # Set a short timeout to prevent hanging
            response = requests.get(url, headers=headers, timeout=self.state["timeout"], 
                                   allow_redirects=True, stream=True)
            # Just get headers without downloading the entire content
            response.close()
            end_time = time.time()
            
            response_time = round((end_time - start_time) * 1000)  # Convert to ms
            
            # Check if URL was redirected
            redirected = response.url != url
            final_url = response.url if redirected else None
            
            status_group = self.get_status_group(response.status_code)
            self.state["status_counts"][status_group] += 1
            
            return {
                "url": url,
                "status_code": response.status_code,
                "response_time": response_time,
                "redirected": redirected,
                "final_url": final_url,
                "status_group": status_group
            }
            
        except requests.exceptions.Timeout:
            self.state["status_counts"]["error"] += 1
            return {
                "url": url,
                "status_code": "Timeout",
                "response_time": self.state["timeout"] * 1000,
                "redirected": False,
                "final_url": None,
                "status_group": "error"
            }
        except Exception as e:
            self.state["status_counts"]["error"] += 1
            return {
                "url": url,
                "status_code": "Error",
                "response_time": 0,
                "redirected": False,
                "final_url": None,
                "status_group": "error",
                "error": str(e)
            }

    def get_status_group(self, status):
        """Get status group from status code"""
        if isinstance(status, str):
            return "error"
        
        if status >= 200 and status < 300:
            return "2xx"
        elif status >= 300 and status < 400:
            return "3xx"
        elif status >= 400 and status < 500:
            return "4xx"
        elif status >= 500:
            return "5xx"
        else:
            return "error"

    def test_all_urls(self):
        """Test all URLs with concurrency - this version is kept for backward compatibility"""
        self.state["is_processing"] = True
        self.state["status_counts"] = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0}
        
        results = []
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.state["concurrent_requests"]) as executor:
                future_to_url = {executor.submit(self.test_url, url_data): url_data for url_data in self.state["urls"]}
                
                # Create a progress bar
                total_urls = len(self.state["urls"])
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_url):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        # Handle unexpected errors
                        url_data = future_to_url[future]
                        results.append({
                            "url": url_data.get("url", "Unknown URL"),
                            "status_code": "Error",
                            "response_time": 0,
                            "redirected": False,
                            "final_url": None,
                            "status_group": "error",
                            "error": str(e)
                        })
                    
                    # Update progress
                    completed += 1
                    progress = completed / total_urls
                    progress_bar.progress(progress)
                    progress_text.text(f"Testing URLs: {completed}/{total_urls}")
            
            # Clear progress elements
            progress_bar.empty()
            progress_text.empty()
        except Exception as e:
            st.error(f"Error testing URLs: {str(e)}")
        
        self.state["validation_results"] = results
        self.state["is_processing"] = False
        
        return results
    
    def check_robots_txt(self, url):
        """Check robots.txt for sitemap declarations"""
        try:
            parsed_url = urlparse(url)
            origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = f"{origin}/robots.txt"
            
            response = requests.get(robots_url, timeout=5)
            if response.status_code != 200:
                return {
                    "found": False,
                    "content": None,
                    "sitemaps": [],
                    "sitemap_declared": False
                }
            
            robots_content = response.text
            
            # Extract sitemap declarations
            sitemap_matches = re.findall(r'Sitemap:\s*(https?://[^\s]+)', robots_content, re.IGNORECASE)
            sitemap_declared = url in sitemap_matches if sitemap_matches else False
            
            return {
                "found": True,
                "content": robots_content,
                "sitemaps": sitemap_matches,
                "sitemap_declared": sitemap_declared
            }
        
        except Exception as e:
            return {
                "found": False,
                "content": f"Error: {str(e)}",
                "sitemaps": [],
                "sitemap_declared": False
            }
    
    def analyze_performance(self, results):
        """Analyze performance metrics from test results"""
        if not results:
            return {
                "avg_response_time": 0,
                "status_distribution": {
                    "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0
                },
                "performance_score": 0,
                "recommendations": ["No data available for performance analysis"]
            }
        
        # Calculate metrics
        total_responses = len(results)
        valid_response_times = [r["response_time"] for r in results if isinstance(r["response_time"], (int, float))]
        
        if not valid_response_times:
            avg_time = 0
        else:
            avg_time = sum(valid_response_times) / len(valid_response_times)
        
        # Status distribution
        status_distribution = {
            "2xx": sum(1 for r in results if r["status_group"] == "2xx"),
            "3xx": sum(1 for r in results if r["status_group"] == "3xx"),
            "4xx": sum(1 for r in results if r["status_group"] == "4xx"),
            "5xx": sum(1 for r in results if r["status_group"] == "5xx"),
            "error": sum(1 for r in results if r["status_group"] == "error")
        }
        
        # Calculate performance score (0-100)
        performance_score = 100
        
        # Reduce score based on average response time
        if avg_time > 200:
            performance_score -= min(30, (avg_time - 200) / 30)
        
        # Reduce score based on error rates
        error_rate = (status_distribution["4xx"] + status_distribution["5xx"] + status_distribution["error"]) / total_responses
        performance_score -= min(30, error_rate * 100)
        
        # Reduce score based on redirect rates
        redirect_rate = status_distribution["3xx"] / total_responses
        performance_score -= min(20, redirect_rate * 50)
        
        # Ensure score is between 0-100
        performance_score = max(0, min(100, round(performance_score)))
        
        # Generate recommendations
        recommendations = []
        
        if avg_time > 500:
            recommendations.append('Response times are high. Consider optimizing server performance or implementing CDN.')
        
        if error_rate > 0.05:
            recommendations.append('Error rate is above 5%. Review and fix broken URLs.')
        
        if redirect_rate > 0.1:
            recommendations.append('Redirect rate is above 10%. Update sitemap with direct URLs to reduce redirects.')
        
        return {
            "avg_response_time": round(avg_time),
            "status_distribution": status_distribution,
            "performance_score": performance_score,
            "recommendations": recommendations
        }

    def calculate_health_score(self, results):
        """Calculate sitemap health score from test results"""
        if not results:
            return 0
        
        total_urls = len(results)
        valid_urls = sum(1 for r in results if r["status_group"] == "2xx")
        
        if total_urls == 0:
            return 0
        
        return round((valid_urls / total_urls) * 100)

    def find_slowest_urls(self, results, n=5):
        """Find the n slowest URLs from test results"""
        valid_results = [r for r in results if isinstance(r["response_time"], (int, float))]
        if not valid_results:
            return []
        
        sorted_results = sorted(valid_results, key=lambda r: r["response_time"], reverse=True)
        return sorted_results[:n]

    def format_xml(self, xml_content):
        """Format XML with indentation"""
        try:
            from xml.dom import minidom
            parsed = minidom.parseString(xml_content)
            return parsed.toprettyxml(indent="  ")
        except:
            # Fallback for XML that can't be parsed
            formatted = ''
            indent = ''
            tab = '  '
            
            for line in xml_content.split('\n'):
                if '</' in line:
                    indent = indent[:-len(tab)]
                
                formatted += indent + line + '\n'
                
                if '>' in line and not '/>' in line and not '</' in line:
                    indent += tab
            
            return formatted

    def get_url_domain(self, url):
        """Extract domain from URL"""
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc
        except:
            return None
    
    def find_replace_xml(self, xml_content, find_text, replace_text, use_regex=False):
        """Find and replace text in XML content"""
        try:
            if use_regex:
                modified = re.sub(find_text, replace_text, xml_content)
            else:
                modified = xml_content.replace(find_text, replace_text)
            
            # Count replacements
            if use_regex:
                count = len(re.findall(find_text, xml_content))
            else:
                count = xml_content.count(find_text)
            
            return {
                "modified_content": modified,
                "count": count
            }
        except Exception as e:
            return {
                "error": str(e),
                "modified_content": xml_content,
                "count": 0
            }

def main():
    # Header section with logo and title
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <div style="font-size: 2.5rem; margin-right: 0.5rem;">🌐</div>
        <div>
            <h1 style="margin: 0; padding: 0;">Sitemap Validator & Analyzer</h1>
            <p style="margin: 0; padding: 0; color: #000000;">Validate, test, and analyze XML sitemaps to improve SEO and website health</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    validator = SitemapValidator()
    
    # Initialize session state
    if 'sitemap_data' not in st.session_state:
        st.session_state.sitemap_data = {
            "sitemap_url": "",
            "sitemap_content": None,
            "urls": [],
            "validation_results": None,
            "robots_txt_data": None
        }
    
    # Main card for URL input with modern design
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # URL input section with improved layout
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        sitemap_url = st.text_input(
            "Sitemap URL",
            placeholder="https://example.com/sitemap.xml",
            value=st.session_state.sitemap_data.get("sitemap_url", "")
        )
    
    with col2:
        if st.button("🔎 Detect Sitemaps", use_container_width=True):
            if not sitemap_url:
                st.warning("Please enter a website URL")
            else:
                with st.spinner("Detecting sitemaps..."):
                    detected_sitemaps = validator.detect_sitemaps(sitemap_url)
                    if detected_sitemaps:
                        sitemap_options = detected_sitemaps
                        if len(sitemap_options) == 1:
                            sitemap_url = sitemap_options[0]
                            st.success(f"Found sitemap: {sitemap_url}")
                        else:
                            st.success(f"Found {len(sitemap_options)} sitemaps!")
                            sitemap_url = st.selectbox(
                                "Select a sitemap",
                                options=sitemap_options
                            )
                    else:
                        st.warning("No sitemaps found. Try entering URL manually.")
    
    with col3:
        if st.button("📥 Load Sitemap", use_container_width=True):
            if not sitemap_url:
                st.warning("Please enter a sitemap URL")
            else:
                with st.spinner("Loading sitemap..."):
                    sitemap_content = validator.load_sitemap(sitemap_url)
                    if sitemap_content:
                        urls = validator.state["urls"]
                        
                        # Check robots.txt
                        robots_txt_data = validator.check_robots_txt(sitemap_url)
                        
                        # Update session state
                        st.session_state.sitemap_data = {
                            "sitemap_url": sitemap_url,
                            "sitemap_content": sitemap_content,
                            "urls": urls,
                            "robots_txt_data": robots_txt_data
                        }
                        
                        st.success(f"Loaded {len(urls)} URLs from sitemap")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Only show tabs if sitemap is loaded
    if st.session_state.sitemap_data.get("sitemap_content"):
        # Settings expander with modern design
        st.markdown('<details class="modern-expander">', unsafe_allow_html=True)
        st.markdown('<summary>⚙️ Test Settings</summary>', unsafe_allow_html=True)
        st.markdown('<div style="padding: 1rem;">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            validator.state["concurrent_requests"] = st.slider(
                "Concurrent Requests",
                min_value=1,
                max_value=20,
                value=5,
                help="Number of URLs to test simultaneously"
            )
        with col2:
            validator.state["timeout"] = st.slider(
                "Request Timeout (seconds)",
                min_value=1,
                max_value=30,
                value=10,
                help="Maximum time to wait for each URL response"
            )
        with col3:
            validator.state["user_agent"] = st.text_input(
                "User Agent",
                value="Mozilla/5.0 (Streamlit Sitemap Validator)",
                help="User agent string to use for requests"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</details>', unsafe_allow_html=True)
        
        # Main tabs with modern styling
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "🧪 URL Testing", 
            "📝 Sitemap Editor", 
            "🤖 Robots.txt", 
            "📈 Analytics"
        ])
        
        # Dashboard Tab
        with tab1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.header("Sitemap Dashboard")
            
            # Overview metrics with modern cards
            overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
            
            with overview_col1:
                st.metric("Total URLs", len(st.session_state.sitemap_data.get("urls", [])))
            
            with overview_col2:
                # Count URLs with images or videos
                urls_with_media = sum(
                    1 for url in st.session_state.sitemap_data.get("urls", [])
                    if url.get("images") or url.get("videos")
                )
                st.metric("URLs with Media", urls_with_media)
            
            with overview_col3:
                # Calculate average priority if available
                priorities = [
                    float(url.get("priority", 0)) 
                    for url in st.session_state.sitemap_data.get("urls", []) 
                    if url.get("priority")
                ]
                avg_priority = sum(priorities) / len(priorities) if priorities else 0
                st.metric("Average Priority", f"{avg_priority:.2f}")
            
            with overview_col4:
                # Check if sitemap is in robots.txt
                robots_data = st.session_state.sitemap_data.get("robots_txt_data", {})
                sitemap_in_robots = "Yes" if robots_data.get("sitemap_declared", False) else "No"
                st.metric("In Robots.txt", sitemap_in_robots)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Performance metrics if results available
            if st.session_state.sitemap_data.get("validation_results"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                results = st.session_state.sitemap_data.get("validation_results")
                status_col1, status_col2, status_col3, status_col4 = st.columns(4)
                
                with status_col1:
                    health_score = validator.calculate_health_score(results)
                    color = "#10B981" if health_score >= 90 else "#F59E0B" if health_score >= 70 else "#EF4444"
                    st.metric(
                        "Health Score", 
                        f"{health_score}%",
                        delta=None,
                        delta_color="normal"
                    )
                
                with status_col2:
                    performance_data = validator.analyze_performance(results)
                    score_color = "#10B981" if performance_data['performance_score'] >= 90 else "#F59E0B" if performance_data['performance_score'] >= 70 else "#EF4444"
                    st.metric(
                        "Performance Score", 
                        f"{performance_data['performance_score']}%",
                        delta=None,
                        delta_color="normal"
                    )
                
                with status_col3:
                    avg_response = performance_data['avg_response_time']
                    resp_color = "#10B981" if avg_response < 200 else "#F59E0B" if avg_response < 500 else "#EF4444"
                    st.metric(
                        "Avg Response Time", 
                        f"{avg_response} ms",
                        delta=None,
                        delta_color="normal"
                    )
                
                with status_col4:
                    redirect_count = sum(1 for r in results if r["redirected"])
                    redirect_pct = round((redirect_count / len(results)) * 100)
                    st.metric(
                        "Redirects", 
                        f"{redirect_count} ({redirect_pct}%)",
                        delta=None,
                        delta_color="normal"
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Status distribution chart with enhanced styling
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Status Code Distribution")
                
                status_data = {
                    "Status": ["Success (2xx)", "Redirects (3xx)", "Client Errors (4xx)", "Server Errors (5xx)", "Errors"],
                    "Count": [
                        performance_data["status_distribution"]["2xx"],
                        performance_data["status_distribution"]["3xx"],
                        performance_data["status_distribution"]["4xx"],
                        performance_data["status_distribution"]["5xx"],
                        performance_data["status_distribution"]["error"]
                    ]
                }
                status_df = pd.DataFrame(status_data)
                
                fig = px.bar(
                    status_df,
                    x="Status",
                    y="Count",
                    color="Status",
                    color_discrete_map={
                        "Success (2xx)": "#10B981",
                        "Redirects (3xx)": "#F59E0B",
                        "Client Errors (4xx)": "#EF4444",
                        "Server Errors (5xx)": "#DC2626",
                        "Errors": "#6B7280"
                    }
                )
                fig.update_layout(
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=40),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="",
                    yaxis_title="",
                    showlegend=False,
                    xaxis=dict(
                        tickfont=dict(size=12),
                        tickangle=0
                    ),
                    yaxis=dict(
                        tickfont=dict(size=12)
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Recommendations card
                if performance_data["recommendations"]:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Recommendations")
                    for recommendation in performance_data["recommendations"]:
                        st.markdown(f'<div style="display: flex; align-items: flex-start; margin-bottom: 0.75rem;">'
                                    f'<div style="color: #3B82F6; margin-right: 0.5rem;">●</div>'
                                    f'<div>{recommendation}</div>'
                                    f'</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Show slowest URLs with modern styling
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Slowest URLs")
                slowest_urls = validator.find_slowest_urls(results)
                if slowest_urls:
                    slow_data = []
                    for result in slowest_urls:
                        slow_data.append({
                            "URL": result["url"],
                            "Response Time (ms)": result["response_time"],
                            "Status": result["status_code"]
                        })
                    
                    st.dataframe(pd.DataFrame(slow_data), use_container_width=True)
                else:
                    st.info("No response time data available.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Run URL testing to see performance metrics.")
            
            # Sitemap structure in a clean card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Sitemap Structure")
            
            urls = st.session_state.sitemap_data.get("urls", [])
            
            # Count images and videos
            total_images = sum(len(url.get("images", [])) for url in urls)
            total_videos = sum(len(url.get("videos", [])) for url in urls)
            
            # Extract domains
            domains = {}
            for url in urls:
                domain = validator.get_url_domain(url.get("url", ""))
                if domain:
                    domains[domain] = domains.get(domain, 0) + 1
            
            # Get priorities distribution
            priorities = {}
            for url in urls:
                priority = url.get("priority")
                if priority:
                    priorities[priority] = priorities.get(priority, 0) + 1
            
            stats_col1, stats_col2 = st.columns(2)
            
            with stats_col1:
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Media Resources</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">'
                            f'<div>Images:</div>'
                            f'<div style="font-weight: 500;">{total_images}</div>'
                            f'</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">'
                            f'<div>Videos:</div>'
                            f'<div style="font-weight: 500;">{total_videos}</div>'
                            f'</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin-top: 1rem;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Priority Distribution</span>', unsafe_allow_html=True)
                if priorities:
                    for priority, count in sorted(priorities.items(), key=lambda x: float(x[0]), reverse=True):
                        st.markdown(f'<div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">'
                                    f'<div>Priority {priority}:</div>'
                                    f'<div style="font-weight: 500;">{count} URLs</div>'
                                    f'</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="margin-top: 0.5rem; color: #64748B;">No priority values found</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with stats_col2:
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Domain Distribution</span>', unsafe_allow_html=True)
                if len(domains) > 1:
                    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
                        st.markdown(f'<div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">'
                                    f'<div style="word-break: break-all;">{domain}:</div>'
                                    f'<div style="font-weight: 500; margin-left: 0.5rem;">{count} URLs</div>'
                                    f'</div>', unsafe_allow_html=True)
                else:
                    single_domain = list(domains.keys())[0] if domains else 'N/A'
                    st.markdown(f'<div style="margin-top: 0.5rem; color: #64748B;">All URLs on same domain: {single_domain}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
        
        # URL Testing Tab
        with tab2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.header("URL Testing")
            
            urls = st.session_state.sitemap_data.get("urls", [])
            
            if not urls:
                st.warning("No URLs found in the sitemap.")
            else:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if st.button("🧪 Test All URLs", use_container_width=True, key="test_urls_button"):
                        # Reset status counts before testing
                        validator.state["status_counts"] = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0}
                        
                        # Create placeholder for progress with better styling
                        progress_placeholder = st.empty()
                        progress_bar = progress_placeholder.progress(0)
                        status_placeholder = st.empty()
                        
                        # Start testing with progress updates
                        total_urls = len(urls)
                        results = []
                        
                        # Use ThreadPoolExecutor for concurrent requests
                        with concurrent.futures.ThreadPoolExecutor(max_workers=validator.state["concurrent_requests"]) as executor:
                            future_to_url = {executor.submit(validator.test_url, url): url for url in urls}
                            
                            for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
                                try:
                                    result = future.result()
                                    results.append(result)
                                except Exception as e:
                                    # Handle any unexpected errors
                                    url = future_to_url[future]["url"] if "url" in future_to_url[future] else "Unknown URL"
                                    results.append({
                                        "url": url,
                                        "status_code": "Error",
                                        "response_time": 0,
                                        "redirected": False,
                                        "final_url": None,
                                        "status_group": "error",
                                        "error": str(e)
                                    })
                                
                                # Update progress
                                progress = (i + 1) / total_urls
                                progress_bar.progress(progress)
                                status_placeholder.text(f"Testing URLs: {i + 1}/{total_urls}")
                        
                        # Clear progress indicators
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        
                        # Store results and update UI
                        st.session_state.sitemap_data["validation_results"] = results
                        st.success(f"Tested {len(results)} URLs")
                        
                        # Force a rerun to refresh the UI with the results
                        st.experimental_rerun()
                
                # Display results if available
                results = st.session_state.sitemap_data.get("validation_results")
                
                if results:
                    # Status counts with modern badges
                    status_counts = {
                        "2xx": sum(1 for r in results if r["status_group"] == "2xx"),
                        "3xx": sum(1 for r in results if r["status_group"] == "3xx"),
                        "4xx": sum(1 for r in results if r["status_group"] == "4xx"),
                        "5xx": sum(1 for r in results if r["status_group"] == "5xx"),
                        "error": sum(1 for r in results if r["status_group"] == "error")
                    }
                    
                    # Display counts with better styling
                    st.markdown('<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;">', unsafe_allow_html=True)
                    
                    st.markdown(f'<div style="background-color: #ECFDF5; padding: 0.5rem 1rem; border-radius: 8px;">'
                                f'<span style="font-weight: 500; color: #10B981;">Success:</span> <span style="font-weight: 600;">{status_counts["2xx"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div style="background-color: #FFFBEB; padding: 0.5rem 1rem; border-radius: 8px;">'
                                f'<span style="font-weight: 500; color: #F59E0B;">Redirects:</span> <span style="font-weight: 600;">{status_counts["3xx"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div style="background-color: #FEE2E2; padding: 0.5rem 1rem; border-radius: 8px;">'
                                f'<span style="font-weight: 500; color: #EF4444;">Client Errors:</span> <span style="font-weight: 600;">{status_counts["4xx"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div style="background-color: #FEE2E2; padding: 0.5rem 1rem; border-radius: 8px;">'
                                f'<span style="font-weight: 500; color: #DC2626;">Server Errors:</span> <span style="font-weight: 600;">{status_counts["5xx"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div style="background-color: #F3F4F6; padding: 0.5rem 1rem; border-radius: 8px;">'
                                f'<span style="font-weight: 500; color: #6B7280;">Other Errors:</span> <span style="font-weight: 600;">{status_counts["error"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Create DataFrame for results
                    data = []
                    for result in results:
                        # Format status cell with custom style
                        if isinstance(result["status_code"], (int, float)):
                            if result["status_code"] >= 200 and result["status_code"] < 300:
                                status_html = f"<span class='status-ok'>{result['status_code']}</span>"
                            elif result["status_code"] >= 300 and result["status_code"] < 400:
                                status_html = f"<span class='status-warning'>{result['status_code']}</span>"
                            else:
                                status_html = f"<span class='status-error'>{result['status_code']}</span>"
                        else:
                            status_html = f"<span class='status-error'>{result['status_code']}</span>"
                        
                        # Format response time
                        if result["response_time"] > 1000:
                            response_time_html = f"<span class='status-error'>{result['response_time']} ms</span>"
                        elif result["response_time"] > 500:
                            response_time_html = f"<span class='status-warning'>{result['response_time']} ms</span>"
                        else:
                            response_time_html = f"<span class='status-ok'>{result['response_time']} ms</span>"
                        
                        # Get URL data
                        url_data = next((u for u in urls if u["url"] == result["url"]), {})
                        
                        data.append({
                            "URL": result["url"],
                            "Status": status_html,
                            "Response Time": response_time_html,
                            "Redirected": "Yes" if result["redirected"] else "No",
                            "Last Modified": url_data.get("lastmod", "-"),
                            "Priority": url_data.get("priority", "-"),
                            "Media": len(url_data.get("images", [])) + len(url_data.get("videos", []))
                        })
                    
                    # Create DataFrame
                    df = pd.DataFrame(data)
                    
                    # Add search filter with better styling
                    search_term = st.text_input(
                        "🔍 Filter URLs", 
                        placeholder="Search by domain, path, etc.",
                        key="url_search"
                    )
                    
                    if search_term:
                        filtered_df = df[df['URL'].str.contains(search_term, case=False)]
                    else:
                        filtered_df = df
                    
                    # Display as an interactive table
                    st.markdown(f'<div style="margin-bottom: 0.5rem; color: #64748B; font-size: 0.875rem;">Showing {len(filtered_df)} of {len(df)} URLs</div>', unsafe_allow_html=True)
                    st.write(filtered_df.to_html(escape=False), unsafe_allow_html=True)
                    
                    # Export to CSV button with better styling
                    csv = filtered_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    st.markdown(f'<a href="data:file/csv;base64,{b64}" download="sitemap_results.csv" class="download-button">📥 Download CSV</a>', unsafe_allow_html=True)
                else:
                    st.info("Click 'Test All URLs' to validate the sitemap URLs.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Sitemap Editor Tab
        with tab3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.header("Sitemap Editor")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                sitemap_content = st.session_state.sitemap_data.get("sitemap_content", "")
                formatted_xml = validator.format_xml(sitemap_content) if sitemap_content else ""
                
                # XML Editor with monospace font
                edited_xml = st.text_area(
                    "XML Content",
                    value=formatted_xml,
                    height=400
                )
            
            with col2:
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Find & Replace</span>', unsafe_allow_html=True)
                
                find_text = st.text_input("Find", placeholder="Text to find")
                replace_text = st.text_input("Replace", placeholder="Replacement text")
                use_regex = st.checkbox("Use Regex")
                
                if st.button("Apply", use_container_width=True):
                    if find_text:
                        result = validator.find_replace_xml(
                            edited_xml, 
                            find_text, 
                            replace_text, 
                            use_regex
                        )
                        
                        if "error" in result:
                            st.error(f"Error: {result['error']}")
                        else:
                            edited_xml = result["modified_content"]
                            st.success(f"Made {result['count']} replacements")
                    else:
                        st.warning("Please enter text to find")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Action buttons with better styling
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Actions</span>', unsafe_allow_html=True)
                
                # Validation button
                if st.button("Validate XML", use_container_width=True):
                    validation_result = validator.validate_sitemap_xml(edited_xml)
                    if validation_result["valid"]:
                        st.success("✅ Sitemap is valid")
                    else:
                        st.error(f"❌ {validation_result['error']}")
                
                # Download button
                if edited_xml:
                    b64 = base64.b64encode(edited_xml.encode()).decode()
                    download_filename = "modified_sitemap.xml"
                    st.markdown(f'<a href="data:application/xml;base64,{b64}" download="{download_filename}" class="download-button" style="display: block; text-align: center; margin-top: 0.5rem;">📥 Download XML</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Preview section with better styling
            if edited_xml:
                st.markdown('<details class="modern-expander" style="margin-top: 1rem;">', unsafe_allow_html=True)
                st.markdown('<summary>URL Preview</summary>', unsafe_allow_html=True)
                st.markdown('<div style="padding: 1rem;">', unsafe_allow_html=True)
                
                try:
                    preview_urls = validator.extract_urls_from_sitemap(edited_xml)
                    
                    if preview_urls:
                        preview_data = []
                        for url in preview_urls[:100]:  # Limit to first 100
                            preview_data.append({
                                "URL": url.get("url", ""),
                                "Last Modified": url.get("lastmod", "-"),
                                "Priority": url.get("priority", "-"),
                                "Change Frequency": url.get("changefreq", "-"),
                                "Images": len(url.get("images", [])),
                                "Videos": len(url.get("videos", []))
                            })
                        
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
                        
                        if len(preview_urls) > 100:
                            st.info(f"Showing 100 of {len(preview_urls)} URLs")
                    else:
                        st.info("No URLs found in the edited XML")
                except Exception as e:
                    st.error(f"Error parsing XML: {str(e)}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</details>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Robots.txt Tab
        with tab4:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.header("Robots.txt Analysis")
            
            robots_data = st.session_state.sitemap_data.get("robots_txt_data", {})
            
            if robots_data:
                # Robots.txt status with modern badges
                status_col1, status_col2 = st.columns(2)
                
                with status_col1:
                    if robots_data.get("found", False):
                        st.markdown('<div style="background-color: #ECFDF5; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center;">'
                                   '<span style="color: #10B981; font-size: 1.2rem; margin-right: 0.5rem;">✓</span>'
                                   '<span style="font-weight: 500;">robots.txt found</span>'
                                   '</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="background-color: #FEE2E2; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center;">'
                                   '<span style="color: #EF4444; font-size: 1.2rem; margin-right: 0.5rem;">✗</span>'
                                   '<span style="font-weight: 500;">robots.txt not found</span>'
                                   '</div>', unsafe_allow_html=True)
                
                with status_col2:
                    if robots_data.get("sitemap_declared", False):
                        st.markdown('<div style="background-color: #ECFDF5; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center;">'
                                   '<span style="color: #10B981; font-size: 1.2rem; margin-right: 0.5rem;">✓</span>'
                                   '<span style="font-weight: 500;">Sitemap declared in robots.txt</span>'
                                   '</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="background-color: #FEE2E2; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center;">'
                                   '<span style="color: #EF4444; font-size: 1.2rem; margin-right: 0.5rem;">✗</span>'
                                   '<span style="font-weight: 500;">Sitemap not declared in robots.txt</span>'
                                   '</div>', unsafe_allow_html=True)
                
                # Sitemaps in robots.txt with card styling
                if robots_data.get("sitemaps"):
                    st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 1rem 0;">', unsafe_allow_html=True)
                    st.markdown('<span style="font-weight: 600; color: #334155;">Sitemaps in robots.txt</span>', unsafe_allow_html=True)
                    for sitemap in robots_data.get("sitemaps", []):
                        st.markdown(f'<div style="margin-top: 0.5rem; word-break: break-all;">'
                                   f'<a href="{sitemap}" target="_blank" style="color: #3B82F6; text-decoration: none;">'
                                   f'{sitemap}'
                                   f'</a>'
                                   f'</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Robots.txt content with code styling
                st.subheader("robots.txt Content")
                robots_content = robots_data.get("content", "# No robots.txt content available")
                st.code(robots_content, language="text")
                
                # Recommendations with modern styling
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 1rem 0;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Recommendations</span>', unsafe_allow_html=True)
                
                recommendations = []
                
                if not robots_data.get("found", False):
                    recommendations.append("Create a robots.txt file at the root of your domain")
                
                if not robots_data.get("sitemap_declared", False):
                    sitemap_url = st.session_state.sitemap_data.get("sitemap_url", "")
                    recommendations.append(f"Declare your sitemap in robots.txt with: Sitemap: {sitemap_url}")
                
                if robots_data.get("content") and "user-agent: *" not in robots_data.get("content", "").lower():
                    recommendations.append("Add a default User-agent rule (User-agent: *)")
                
                if robots_data.get("content") and "crawl-delay:" not in robots_data.get("content", "").lower():
                    recommendations.append("Consider adding Crawl-delay directive to control crawler rate")
                
                if recommendations:
                    for i, recommendation in enumerate(recommendations):
                        st.markdown(f'<div style="display: flex; align-items: flex-start; margin-top: 0.5rem;">'
                                   f'<div style="color: #3B82F6; margin-right: 0.5rem;">●</div>'
                                   f'<div>{recommendation}</div>'
                                   f'</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #ECFDF5; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center; margin-top: 0.5rem;">'
                               '<span style="color: #10B981; font-size: 1.2rem; margin-right: 0.5rem;">✓</span>'
                               '<span style="font-weight: 500;">No recommendations - robots.txt appears to be properly configured</span>'
                               '</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Robots.txt data not available. Load a sitemap first.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Analytics Tab
        with tab5:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.header("Sitemap Analytics")
            
            results = st.session_state.sitemap_data.get("validation_results")
            urls = st.session_state.sitemap_data.get("urls", [])
            
            if not results:
                st.info("Run URL testing first to see analytics.")
            else:
                performance_data = validator.analyze_performance(results)
                
                # Performance metrics with enhanced styling
                st.subheader("Performance Metrics")
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    health_score = validator.calculate_health_score(results)
                    st.metric(
                        "Health Score", 
                        f"{health_score}%",
                        delta=None,
                        delta_color="normal"
                    )
                    st.markdown(
                        "<span style='font-size: 0.875rem; color: #000000;'>Percentage of URLs that return a successful status code</span>",
                        unsafe_allow_html=True
                    )
                
                with metric_col2:
                    st.metric(
                        "Performance Score", 
                        f"{performance_data['performance_score']}%",
                        delta=None,
                        delta_color="normal"
                    )
                    st.markdown(
                        "<span style='font-size: 0.875rem; color: #000000;'>Based on response times, error rates, and redirects</span>",
                        unsafe_allow_html=True
                    )
                
                with metric_col3:
                    avg_response = performance_data['avg_response_time']
                    st.metric(
                        "Avg Response Time", 
                        f"{avg_response} ms",
                        delta=None,
                        delta_color="normal"
                    )
                    st.markdown(
                        "<span style='font-size: 0.875rem; color: #000000;'>Average time to respond across all URLs</span>",
                        unsafe_allow_html=True
                    )
                
                # Response time distribution with enhanced styling
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 1rem 0;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Response Time Distribution</span>', unsafe_allow_html=True)
                
                response_times = [r["response_time"] for r in results if isinstance(r["response_time"], (int, float))]
                
                if response_times:
                    # Create histogram
                    fig = px.histogram(
                        x=response_times,
                        nbins=20,
                        labels={"x": "Response Time (ms)"},
                        color_discrete_sequence=["#3B82F6"]
                    )
                    fig.update_layout(
                        height=300,
                        margin=dict(l=20, r=20, t=30, b=40),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            title="Response Time (ms)",
                            titlefont=dict(size=12),
                            tickfont=dict(size=10)
                        ),
                        yaxis=dict(
                            title="Count",
                            titlefont=dict(size=12),
                            tickfont=dict(size=10)
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Additional stats with enhanced styling
                    median_time = np.median(response_times)
                    p90_time = np.percentile(response_times, 90)
                    
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.markdown(f'<div style="text-align: center;">'
                                   f'<div style="font-size: 0.875rem; color: #64748B;">Median Response Time</div>'
                                   f'<div style="font-size: 1.5rem; font-weight: 600; color: #334155;">{int(median_time)} ms</div>'
                                   f'</div>', unsafe_allow_html=True)
                    with stat_col2:
                        st.markdown(f'<div style="text-align: center;">'
                                   f'<div style="font-size: 0.875rem; color: #64748B;">90th Percentile</div>'
                                   f'<div style="font-size: 1.5rem; font-weight: 600; color: #334155;">{int(p90_time)} ms</div>'
                                   f'</div>', unsafe_allow_html=True)
                    with stat_col3:
                        st.markdown(f'<div style="text-align: center;">'
                                   f'<div style="font-size: 0.875rem; color: #64748B;">Max Response Time</div>'
                                   f'<div style="font-size: 1.5rem; font-weight: 600; color: #334155;">{max(response_times)} ms</div>'
                                   f'</div>', unsafe_allow_html=True)
                else:
                    st.info("No valid response time data available.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Domain analysis with card styling
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 1rem 0;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Domain Analysis</span>', unsafe_allow_html=True)
                
                domains = {}
                for result in results:
                    domain = validator.get_url_domain(result["url"])
                    if domain:
                        if domain not in domains:
                            domains[domain] = {
                                "count": 0,
                                "successful": 0,
                                "redirects": 0,
                                "errors": 0,
                                "response_times": []
                            }
                        
                        domains[domain]["count"] += 1
                        
                        if result["status_group"] == "2xx":
                            domains[domain]["successful"] += 1
                        elif result["status_group"] == "3xx":
                            domains[domain]["redirects"] += 1
                        else:
                            domains[domain]["errors"] += 1
                        
                        if isinstance(result["response_time"], (int, float)):
                            domains[domain]["response_times"].append(result["response_time"])
                
                # Prepare data for table
                domain_data = []
                for domain, data in domains.items():
                    avg_time = sum(data["response_times"]) / len(data["response_times"]) if data["response_times"] else 0
                    health = round((data["successful"] / data["count"]) * 100) if data["count"] > 0 else 0
                    
                    domain_data.append({
                        "Domain": domain,
                        "URLs": data["count"],
                        "Success": data["successful"],
                        "Redirects": data["redirects"],
                        "Errors": data["errors"],
                        "Avg Response Time": f"{int(avg_time)} ms",
                        "Health Score": f"{health}%"
                    })
                
                if domain_data:
                    domain_df = pd.DataFrame(domain_data)
                    st.dataframe(domain_df, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Content type analysis with card styling
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 1rem 0;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Content Analysis</span>', unsafe_allow_html=True)
                
                # Count media by URL
                media_data = []
                for url in urls:
                    images_count = len(url.get("images", []))
                    videos_count = len(url.get("videos", []))
                    
                    if images_count > 0 or videos_count > 0:
                        media_data.append({
                            "URL": url.get("url", ""),
                            "Images": images_count,
                            "Videos": videos_count,
                            "Total Media": images_count + videos_count
                        })
                
                if media_data:
                    media_df = pd.DataFrame(media_data)
                    media_df = media_df.sort_values(by="Total Media", ascending=False)
                    
                    # Show top 10 URLs with most media
                    st.markdown('<div style="margin: 1rem 0 0.5rem 0;">Top URLs with Most Media</div>', unsafe_allow_html=True)
                    st.dataframe(media_df.head(10), use_container_width=True)
                    
                    # Total media counts with modern styling
                    total_images = sum(url.get("Images", 0) for url in media_data)
                    total_videos = sum(url.get("Videos", 0) for url in media_data)
                    
                    media_col1, media_col2 = st.columns(2)
                    with media_col1:
                        st.markdown(f'<div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">'
                                   f'<div style="font-size: 0.875rem; color: #64748B;">Total Images</div>'
                                   f'<div style="font-size: 1.5rem; font-weight: 600; color: #334155;">{total_images}</div>'
                                   f'</div>', unsafe_allow_html=True)
                    with media_col2:
                        st.markdown(f'<div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">'
                                   f'<div style="font-size: 0.875rem; color: #64748B;">Total Videos</div>'
                                   f'<div style="font-size: 1.5rem; font-weight: 600; color: #334155;">{total_videos}</div>'
                                   f'</div>', unsafe_allow_html=True)
                else:
                    st.info("No media content found in the sitemap.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Critical insights with modern alert styling
                st.markdown('<div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 1rem 0;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">Insights & Recommendations</span>', unsafe_allow_html=True)
                
                insights = []
                
                # Health score insights
                if health_score < 90:
                    insights.append({
                        "type": "error",
                        "message": f"Site health score is below 90% (currently {health_score}%)"
                    })
                
                # Error insights
                error_count = sum(1 for r in results if r["status_group"] in ["4xx", "5xx", "error"])
                if error_count > 0:
                    error_percentage = round((error_count / len(results)) * 100)
                    insights.append({
                        "type": "error",
                        "message": f"{error_count} URLs ({error_percentage}%) return error codes and need attention"
                    })
                
                # Response time insights
                if performance_data['avg_response_time'] > 1000:
                    insights.append({
                        "type": "warning",
                        "message": f"Average response time is high ({performance_data['avg_response_time']}ms)"
                    })
                
                # Redirect insights
                redirect_count = sum(1 for r in results if r["status_group"] == "3xx")
                if redirect_count > 0:
                    redirect_percentage = round((redirect_count / len(results)) * 100)
                    insights.append({
                        "type": "warning",
                        "message": f"{redirect_count} URLs ({redirect_percentage}%) are redirects"
                    })
                
                # Domain insights
                if len(domains) > 1:
                    insights.append({
                        "type": "warning",
                        "message": f"Sitemap contains URLs from {len(domains)} different domains"
                    })
                
                # Display insights with modern styling
                if insights:
                    for insight in insights:
                        if insight["type"] == "error":
                            st.markdown(f'<div style="background-color: #FEE2E2; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center; margin-top: 0.5rem;">'
                                      f'<span style="color: #EF4444; font-size: 1.2rem; margin-right: 0.5rem;">⚠️</span>'
                                      f'<span style="font-weight: 500;">{insight["message"]}</span>'
                                      f'</div>', unsafe_allow_html=True)
                        elif insight["type"] == "warning":
                            st.markdown(f'<div style="background-color: #FFFBEB; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center; margin-top: 0.5rem;">'
                                      f'<span style="color: #F59E0B; font-size: 1.2rem; margin-right: 0.5rem;">ℹ️</span>'
                                      f'<span style="font-weight: 500;">{insight["message"]}</span>'
                                      f'</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="background-color: #EFF6FF; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center; margin-top: 0.5rem;">'
                                      f'<span style="color: #3B82F6; font-size: 1.2rem; margin-right: 0.5rem;">ℹ️</span>'
                                      f'<span style="font-weight: 500;">{insight["message"]}</span>'
                                      f'</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #ECFDF5; padding: 0.75rem 1rem; border-radius: 8px; display: flex; align-items: center; margin-top: 0.5rem;">'
                              f'<span style="color: #10B981; font-size: 1.2rem; margin-right: 0.5rem;">✓</span>'
                              f'<span style="font-weight: 500;">No issues detected</span>'
                              f'</div>', unsafe_allow_html=True)
                
                # Recommendations with clean styling
                if performance_data["recommendations"]:
                    st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)
                    st.markdown('<span style="font-weight: 600; color: #334155;">Performance Recommendations</span>', unsafe_allow_html=True)
                    for recommendation in performance_data["recommendations"]:
                        st.markdown(f'<div style="display: flex; align-items: flex-start; margin-top: 0.5rem;">'
                                   f'<div style="color: #3B82F6; margin-right: 0.5rem;">●</div>'
                                   f'<div>{recommendation}</div>'
                                   f'</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Additional recommendations
                st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)
                st.markdown('<span style="font-weight: 600; color: #334155;">General Recommendations</span>', unsafe_allow_html=True)
                
                general_recommendations = [
                    "Implement browser caching to improve response times",
                    "Set up monitoring for periodic sitemap validation",
                    "Ensure all URLs respond with 200 status codes"
                ]
                
                if redirect_count > 0:
                    general_recommendations.append("Update sitemap to use final destination URLs instead of redirects")
                
                if performance_data['avg_response_time'] > 500:
                    general_recommendations.append("Optimize server response times through caching and compression")
                    
                    if performance_data['avg_response_time'] > 1000:
                        general_recommendations.append("Consider implementing a CDN to improve content delivery speed")
                
                for recommendation in general_recommendations:
                    st.markdown(f'<div style="display: flex; align-items: flex-start; margin-top: 0.5rem;">'
                               f'<div style="color: #3B82F6; margin-right: 0.5rem;">●</div>'
                               f'<div>{recommendation}</div>'
                               f'</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    # Modern footer
    st.markdown("""
    <div class="footer">
        <p>Sitemap Validator & Analyzer | Built with Streamlit</p>
        <p style="font-size: 0.75rem; margin-top: 0.25rem;">© 2025 | v2.0.0</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
