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

st.set_page_config(page_title="Sitemap Validator & Analyzer", layout="wide", page_icon="🌐")

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-radius: 4px 4px 0 0;
        border-right: 1px solid #e0e0e0;
        border-left: 1px solid #e0e0e0;
        border-top: 1px solid #e0e0e0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
    .status-ok {
        background-color: #d1ffd7;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
        color: #0a7b1e;
    }
    .status-warning {
        background-color: #fff7d1;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
        color: #8a6b00;
    }
    .status-error {
        background-color: #ffd1d1;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
        color: #a70000;
    }
    .small-info {
        font-size: 0.8rem;
        color: #666;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #888;
        font-size: 0.8rem;
    }
    .stProgress > div > div > div > div {
        background-color: #2e7fff;
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
    st.title("🌐 Sitemap Validator & Analyzer")
    st.markdown("Validate, test, and analyze XML sitemaps to improve SEO and website health.")
    
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
    
    # URL input section
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
    
    # Only show tabs if sitemap is loaded
    if st.session_state.sitemap_data.get("sitemap_content"):
        # Settings expander for test configuration
        with st.expander("⚙️ Test Settings"):
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
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "🧪 URL Testing", 
            "📝 Sitemap Editor", 
            "🤖 Robots.txt", 
            "📈 Analytics"
        ])
        
        # Dashboard Tab
        with tab1:
            st.header("Sitemap Dashboard")
            
            # Overview metrics
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
            
            # Status metrics
            if st.session_state.sitemap_data.get("validation_results"):
                results = st.session_state.sitemap_data.get("validation_results")
                status_col1, status_col2, status_col3, status_col4 = st.columns(4)
                
                with status_col1:
                    health_score = validator.calculate_health_score(results)
                    st.metric("Health Score", f"{health_score}%")
                
                with status_col2:
                    performance_data = validator.analyze_performance(results)
                    st.metric("Performance Score", f"{performance_data['performance_score']}%")
                
                with status_col3:
                    avg_response = performance_data['avg_response_time']
                    st.metric("Avg Response Time", f"{avg_response} ms")
                
                with status_col4:
                    redirect_count = sum(1 for r in results if r["redirected"])
                    st.metric("Redirects", redirect_count)
                
                # Status distribution chart
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
                        "Success (2xx)": "#2ecc71",
                        "Redirects (3xx)": "#f39c12",
                        "Client Errors (4xx)": "#e74c3c",
                        "Server Errors (5xx)": "#c0392b",
                        "Errors": "#7f8c8d"
                    }
                )
                fig.update_layout(
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=40),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="",
                    yaxis_title="",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Recommendations
                if performance_data["recommendations"]:
                    st.subheader("Recommendations")
                    for recommendation in performance_data["recommendations"]:
                        st.markdown(f"- {recommendation}")
                
                # Show slowest URLs
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
            else:
                st.info("Run URL testing to see performance metrics.")
            
            # Quick sitemap stats
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
                st.markdown("**Media Resources**")
                st.markdown(f"- Images: {total_images}")
                st.markdown(f"- Videos: {total_videos}")
                
                st.markdown("**Priority Distribution**")
                if priorities:
                    for priority, count in sorted(priorities.items(), key=lambda x: float(x[0]), reverse=True):
                        st.markdown(f"- Priority {priority}: {count} URLs")
                else:
                    st.markdown("- No priority values found")
            
            with stats_col2:
                st.markdown("**Domain Distribution**")
                if len(domains) > 1:
                    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
                        st.markdown(f"- {domain}: {count} URLs")
                else:
                    st.markdown(f"- All URLs on same domain: {list(domains.keys())[0] if domains else 'N/A'}")
        
        # URL Testing Tab
        with tab2:
            st.header("URL Testing")
            
            urls = st.session_state.sitemap_data.get("urls", [])
            
            if not urls:
                st.warning("No URLs found in the sitemap.")
            else:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    test_button_col, download_col = st.columns([3, 1])
                with test_button_col:
                    if st.button("🧪 Test All URLs", use_container_width=True, key="test_urls_button"):
                        # Reset status counts before testing
                        validator.state["status_counts"] = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0}
                        
                        # Create placeholder for progress
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
                    # Status counts
                    status_counts = {
                        "2xx": sum(1 for r in results if r["status_group"] == "2xx"),
                        "3xx": sum(1 for r in results if r["status_group"] == "3xx"),
                        "4xx": sum(1 for r in results if r["status_group"] == "4xx"),
                        "5xx": sum(1 for r in results if r["status_group"] == "5xx"),
                        "error": sum(1 for r in results if r["status_group"] == "error")
                    }
                    
                    # Display counts
                    count_cols = st.columns(5)
                    with count_cols[0]:
                        st.markdown(f"**Success:** {status_counts['2xx']}")
                    with count_cols[1]:
                        st.markdown(f"**Redirects:** {status_counts['3xx']}")
                    with count_cols[2]:
                        st.markdown(f"**Client Errors:** {status_counts['4xx']}")
                    with count_cols[3]:
                        st.markdown(f"**Server Errors:** {status_counts['5xx']}")
                    with count_cols[4]:
                        st.markdown(f"**Other Errors:** {status_counts['error']}")
                    
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
                    
                    # Add search filter
                    search_term = st.text_input("🔍 Filter URLs", placeholder="Search by domain, path, etc.")
                    
                    if search_term:
                        filtered_df = df[df['URL'].str.contains(search_term, case=False)]
                    else:
                        filtered_df = df
                    
                    # Display as an interactive table
                    st.write(f"Showing {len(filtered_df)} of {len(df)} URLs")
                    st.write(filtered_df.to_html(escape=False), unsafe_allow_html=True)
                    
                    # Export to CSV button
                    csv = filtered_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="sitemap_results.csv" class="download-button">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.info("Click 'Test All URLs' to validate the sitemap URLs.")
        
        # Sitemap Editor Tab
        with tab3:
            st.header("Sitemap Editor")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                sitemap_content = st.session_state.sitemap_data.get("sitemap_content", "")
                formatted_xml = validator.format_xml(sitemap_content) if sitemap_content else ""
                
                # XML Editor
                edited_xml = st.text_area(
                    "XML Content",
                    value=formatted_xml,
                    height=400
                )
            
            with col2:
                st.subheader("Find & Replace")
                
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
                
                st.divider()
                
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
                    href = f'<a href="data:application/xml;base64,{b64}" download="{download_filename}" class="download-button">Download XML</a>'
                    st.markdown(href, unsafe_allow_html=True)
            
            # Preview section
            if edited_xml:
                with st.expander("URL Preview"):
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
        
        # Robots.txt Tab
        with tab4:
            st.header("Robots.txt Analysis")
            
            robots_data = st.session_state.sitemap_data.get("robots_txt_data", {})
            
            if robots_data:
                # Robots.txt status
                status_col1, status_col2 = st.columns(2)
                
                with status_col1:
                    if robots_data.get("found", False):
                        st.success("✅ robots.txt found")
                    else:
                        st.error("❌ robots.txt not found")
                
                with status_col2:
                    if robots_data.get("sitemap_declared", False):
                        st.success("✅ Sitemap declared in robots.txt")
                    else:
                        st.error("❌ Sitemap not declared in robots.txt")
                
                # Sitemaps in robots.txt
                if robots_data.get("sitemaps"):
                    st.subheader("Sitemaps in robots.txt")
                    for sitemap in robots_data.get("sitemaps", []):
                        st.markdown(f"- [{sitemap}]({sitemap})")
                
                # Robots.txt content
                st.subheader("robots.txt Content")
                robots_content = robots_data.get("content", "# No robots.txt content available")
                st.text_area("Content", value=robots_content, height=300, disabled=True)
                
                # Recommendations
                st.subheader("Recommendations")
                
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
                    for recommendation in recommendations:
                        st.markdown(f"- {recommendation}")
                else:
                    st.success("No recommendations - robots.txt appears to be properly configured")
            else:
                st.info("Robots.txt data not available. Load a sitemap first.")
        
        # Analytics Tab
        with tab5:
            st.header("Sitemap Analytics")
            
            results = st.session_state.sitemap_data.get("validation_results")
            urls = st.session_state.sitemap_data.get("urls", [])
            
            if not results:
                st.info("Run URL testing first to see analytics.")
            else:
                performance_data = validator.analyze_performance(results)
                
                # Performance metrics
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
                        "<span class='small-info'>Percentage of URLs that return a successful status code</span>",
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
                        "<span class='small-info'>Based on response times, error rates, and redirects</span>",
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
                        "<span class='small-info'>Average time to respond across all URLs</span>",
                        unsafe_allow_html=True
                    )
                
                # Response time distribution
                st.subheader("Response Time Distribution")
                
                response_times = [r["response_time"] for r in results if isinstance(r["response_time"], (int, float))]
                
                if response_times:
                    # Create histogram
                    fig = px.histogram(
                        x=response_times,
                        nbins=20,
                        labels={"x": "Response Time (ms)"},
                        color_discrete_sequence=["#2e7fff"]
                    )
                    fig.update_layout(
                        height=300,
                        margin=dict(l=20, r=20, t=30, b=40),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Additional stats
                    median_time = np.median(response_times)
                    p90_time = np.percentile(response_times, 90)
                    
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.metric("Median Response Time", f"{int(median_time)} ms")
                    with stat_col2:
                        st.metric("90th Percentile", f"{int(p90_time)} ms")
                    with stat_col3:
                        st.metric("Max Response Time", f"{max(response_times)} ms")
                else:
                    st.info("No valid response time data available.")
                
                # Domain analysis
                st.subheader("Domain Analysis")
                
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
                
                # Content type analysis (images, videos)
                st.subheader("Content Analysis")
                
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
                    st.write("Top URLs with Most Media")
                    st.dataframe(media_df.head(10), use_container_width=True)
                    
                    # Total media counts
                    total_images = sum(url.get("Images", 0) for url in media_data)
                    total_videos = sum(url.get("Videos", 0) for url in media_data)
                    
                    media_col1, media_col2 = st.columns(2)
                    with media_col1:
                        st.metric("Total Images", total_images)
                    with media_col2:
                        st.metric("Total Videos", total_videos)
                else:
                    st.info("No media content found in the sitemap.")
                
                # Critical insights
                st.subheader("Insights & Recommendations")
                
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
                
                # Display insights
                for insight in insights:
                    if insight["type"] == "error":
                        st.error(insight["message"])
                    elif insight["type"] == "warning":
                        st.warning(insight["message"])
                    else:
                        st.info(insight["message"])
                
                # Recommendations
                if performance_data["recommendations"]:
                    st.subheader("Performance Recommendations")
                    for recommendation in performance_data["recommendations"]:
                        st.markdown(f"- {recommendation}")
                
                # Additional recommendations
                st.subheader("General Recommendations")
                
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
                    st.markdown(f"- {recommendation}")

    # Footer
    st.markdown("""
    <div class="footer">
        <p>Sitemap Validator & Analyzer | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
