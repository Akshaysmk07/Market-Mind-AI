# main.py
import os
import streamlit as st
from groq import Groq
from langchain.agents import initialize_agent, AgentType
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.tools import Tool
import pandas as pd
import requests
from bs4 import BeautifulSoup
import tempfile
import markdown
import time
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from pytrends.request import TrendReq
from datetime import datetime
import re
from serpapi import GoogleSearch
import urllib.parse

# Set up environment variables
os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", "")  # Get from Streamlit secrets
os.environ["SERPAPI_API_KEY"] = st.secrets.get("SERPAPI_API_KEY", "")  # Get from Streamlit secrets

# Initialize Groq client
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Set up LLM and chains
llm = ChatGroq(
    model_name="llama3-70b-8192",  # Using Llama 3 through Groq (free tier)
    temperature=0.2,
)

# Create schema for structured outputs
class Competitor(BaseModel):
    name: str = Field(description="Company name")
    address: Optional[str] = Field(description="Physical address")
    website: Optional[str] = Field(description="Company website")
    description: str = Field(description="Brief description of what they offer")
    pricing: Optional[str] = Field(description="Pricing information if available")
    strengths: List[str] = Field(description="Company strengths")
    weaknesses: List[str] = Field(description="Company weaknesses")
    
class LocalBusinessInfo(BaseModel):
    name: str = Field(description="Business name")
    address: Optional[str] = Field(description="Physical address")
    phone: Optional[str] = Field(description="Contact phone")
    website: Optional[str] = Field(description="Business website")
    rating: Optional[float] = Field(description="Customer rating")
    reviews: Optional[int] = Field(description="Number of reviews")
    description: Optional[str] = Field(description="Description of business")

class MarketTrend(BaseModel):
    trend_name: str = Field(description="Name of the trend")
    description: str = Field(description="Description of the trend")
    impact: str = Field(description="Impact on the business idea")
    source: str = Field(description="Source of this trend information")

class MarketAnalysis(BaseModel):
    market_size: str = Field(description="Estimated market size")
    growth_rate: str = Field(description="Market growth rate")
    target_audience: str = Field(description="Description of target audience")
    barriers_to_entry: List[str] = Field(description="Barriers to entry for this market")
    opportunities: List[str] = Field(description="Market opportunities")
    threats: List[str] = Field(description="Market threats")

# Define tools
def serp_search(query):
    """Search for location-specific information using SerpAPI's Google Maps search."""
    try:
        params = {
            "engine": "google_maps",
            "q": query,
            "api_key": os.environ["SERPAPI_API_KEY"],
            "type": "search",
            "num": "20",  # Fetch more results for better coverage
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "local_results" not in results:
            return json.dumps({"error": "No local results found for this query."})
        
        local_results = []
        for place in results["local_results"]:
            local_results.append({
                "name": place.get("title", ""),
                "address": place.get("address", ""),
                "phone": place.get("phone", ""),
                "website": place.get("website", ""),
                "rating": place.get("rating", ""),
                "reviews": place.get("reviews", ""),
                "description": place.get("description", ""),
                "type": place.get("type", ""),
                "hours": place.get("hours", ""),
                "gps_coordinates": place.get("gps_coordinates", {}),
            })
        
        return json.dumps({"local_results": local_results})
    except Exception as e:
        return f"Error searching local data: {str(e)}"

def search_web(query):
    """Search the web for the given query using SerpAPI."""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": os.environ["SERPAPI_API_KEY"],
            "num": 10,
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "organic_results" not in results:
            return json.dumps({"error": "No search results found."})
        
        search_results = []
        for result in results["organic_results"][:5]:
            search_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
            })
        
        return json.dumps({"search_results": search_results})
    except Exception as e:
        return f"Error searching web: {str(e)}"

def scrape_website(url):
    """Scrape content from a website."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title and paragraphs
        title = soup.title.string if soup.title else "No title found"
        paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text.strip()]
        
        content = f"Title: {title}\n\nContent:\n" + "\n".join(paragraphs[:10])
        return content
    except Exception as e:
        return f"Error scraping website: {str(e)}"

def analyze_google_trends(query):
    """Analyze Google Trends data for the query."""
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        kw_list = [query]
        pytrends.build_payload(kw_list, timeframe='today 12-m')
        
        # Get interest over time
        interest_over_time = pytrends.interest_over_time()
        if not interest_over_time.empty:
            current = interest_over_time[query].iloc[-1]
            peak = interest_over_time[query].max()
            trend = "increasing" if current > interest_over_time[query].iloc[-6] else "decreasing"
            
            # Get related queries
            related_queries = pytrends.related_queries()
            rising = related_queries[query]['rising'] if query in related_queries else None
            top = related_queries[query]['top'] if query in related_queries else None
            
            rising_terms = rising['query'].tolist()[:5] if rising is not None and not rising.empty else []
            top_terms = top['query'].tolist()[:5] if top is not None and not top.empty else []
            
            result = {
                "trend": trend,
                "current_interest": int(current),
                "peak_interest": int(peak),
                "rising_terms": rising_terms,
                "top_terms": top_terms
            }
            return json.dumps(result)
        return "No trend data found"
    except Exception as e:
        return f"Error analyzing Google Trends: {str(e)}"

def get_local_news(location, topic):
    """Get local news about a specific topic in a location."""
    try:
        params = {
            "engine": "google",
            "q": f"{topic} {location} news",
            "api_key": os.environ["SERPAPI_API_KEY"],
            "num": 5,
            "tbm": "nws"  # Search for news
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "news_results" not in results:
            return json.dumps({"error": "No news found for this query."})
        
        news_results = []
        for news in results.get("news_results", [])[:5]:
            news_results.append({
                "title": news.get("title", ""),
                "link": news.get("link", ""),
                "source": news.get("source", ""),
                "date": news.get("date", ""),
                "snippet": news.get("snippet", "")
            })
        
        return json.dumps({"news_results": news_results})
    except Exception as e:
        return f"Error getting local news: {str(e)}"

def get_demographic_data(location):
    """Get demographic data for a location."""
    try:
        # Using Google search to find demographic information
        params = {
            "engine": "google",
            "q": f"{location} demographics population statistics",
            "api_key": os.environ["SERPAPI_API_KEY"],
            "num": 3,
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "organic_results" not in results:
            return json.dumps({"error": "No demographic data found."})
        
        # Return the search results about demographics
        search_results = []
        for result in results["organic_results"][:3]:
            search_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
            })
        
        return json.dumps({"demographic_data": search_results})
    except Exception as e:
        return f"Error getting demographic data: {str(e)}"

# Define tools list
tools = [
    Tool(
        name="LocalSearch",
        func=serp_search,
        description="Search for local businesses and places in a specific location."
    ),
    Tool(
        name="WebSearch",
        func=search_web,
        description="Search the web for information about markets, companies, and trends."
    ),
    Tool(
        name="ScrapeWebsite",
        func=scrape_website,
        description="Scrape content from a website URL for deeper analysis."
    ),
    Tool(
        name="GoogleTrends",
        func=analyze_google_trends,
        description="Analyze Google Trends data for a specific query or business idea."
    ),
    Tool(
        name="LocalNews",
        func=get_local_news,
        description="Get local news about a specific topic in a location."
    ),
    Tool(
        name="DemographicData",
        func=get_demographic_data,
        description="Get demographic data for a location."
    )
]

# Define agent
market_research_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
)

# Extract location from business idea
def extract_location(business_idea):
    """Extract location from business idea if present."""
    # Common patterns: "X in Y", "X at Y", "X for Y"
    location_patterns = [
        r"in\s+([A-Za-z\s]+(?:,\s*[A-Za-z\s]+)?)",
        r"at\s+([A-Za-z\s]+(?:,\s*[A-Za-z\s]+)?)",
        r"for\s+([A-Za-z\s]+(?:,\s*[A-Za-z\s]+)?)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, business_idea)
        if match:
            location = match.group(1).strip()
            if location.lower() not in ["the", "a", "an", "my", "our", "your", "their"]:
                return location
    
    return None

# Extract business type from business idea
def extract_business_type(business_idea):
    """Extract the main business type from the idea."""
    # Remove location part if present
    location = extract_location(business_idea)
    if location:
        business_type = business_idea.split(f"in {location}")[0].strip()
        if not business_type:
            business_type = business_idea.split(f"at {location}")[0].strip()
        if not business_type:
            business_type = business_idea.split(f"for {location}")[0].strip()
        return business_type
    
    return business_idea

# Task agents for specific functions
def run_local_search_agent(business_idea):
    """Local search agent that finds location-specific information."""
    location = extract_location(business_idea)
    business_type = extract_business_type(business_idea)
    
    if not location:
        return "No specific location was provided in your business idea. To get location-specific data, please include a location in your business idea (e.g., 'coffee shop in Boston')."
    
    try:
        query = f"{business_type} in {location}"
        search_results = json.loads(serp_search(query))
        
        if "error" in search_results:
            return f"Could not find local businesses for {query}. Please try a different business type or location."
        
        local_results = search_results.get("local_results", [])
        if not local_results:
            return f"No local businesses found for {query}."
        
        # Format the results
        result = f"## Local Market Analysis for {business_type} in {location}\n\n"
        result += f"Found {len(local_results)} local businesses matching your criteria.\n\n"
        
        for i, business in enumerate(local_results[:10], 1):
            result += f"### {i}. {business.get('name', 'Unnamed Business')}\n"
            if business.get('address'):
                result += f"**Address:** {business.get('address')}\n"
            if business.get('phone'):
                result += f"**Phone:** {business.get('phone')}\n"
            if business.get('website'):
                result += f"**Website:** {business.get('website')}\n"
            if business.get('rating'):
                result += f"**Rating:** {business.get('rating')} ({business.get('reviews', '0')} reviews)\n"
            if business.get('hours'):
                result += f"**Hours:** {business.get('hours')}\n"
            if business.get('description'):
                result += f"**Description:** {business.get('description')}\n"
            result += "\n"
        
        # Get demographic information
        demographic_results = json.loads(get_demographic_data(location))
        if "demographic_data" in demographic_results and demographic_results["demographic_data"]:
            result += f"## Demographic Information for {location}\n\n"
            for data in demographic_results["demographic_data"]:
                if data.get('snippet'):
                    result += f"{data.get('snippet')}\n\n"
        
        return result
    except Exception as e:
        return f"Error running local search: {str(e)}"

def run_competitor_analysis_agent(business_idea):
    """Competitor analysis agent that identifies and analyzes competitors."""
    location = extract_location(business_idea)
    business_type = extract_business_type(business_idea)
    
    if not location:
        location = "generic location"
    
    prompt = ChatPromptTemplate.from_template(
        """You are a competitive intelligence specialist. Analyze the local competitors for this business idea: {business_idea}.
        
        Here's what I know about local businesses in this area:
        {local_data}
        
        Based on this information, provide a detailed competitor analysis including:
        1. Overview of the competitive landscape
        2. Analysis of top 3-5 competitors (strengths and weaknesses)
        3. Gap analysis - what opportunities exist in the market
        4. Threat analysis - what challenges you might face
        
        Format your response with clear sections and detailed analysis.
        """
    )
    
    # Get local data first
    local_data = run_local_search_agent(business_idea)
    
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(business_idea=business_idea, local_data=local_data)
    return result

def run_trend_analyzer_agent(business_idea):
    """Trend analyzer agent that identifies market trends."""
    location = extract_location(business_idea)
    business_type = extract_business_type(business_idea)
    
    prompt = ChatPromptTemplate.from_template(
        """You are a market trend analyst. Identify current trends related to this business idea: {business_idea}.
        
        Use this Google Trends data:
        {trends_data}
        
        And these local news items:
        {news_data}
        
        Provide a comprehensive analysis of:
        1. Overall market trends for this business type
        2. Local trends specific to this location (if available)
        3. Consumer behavior patterns
        4. Emerging opportunities
        5. Potential threats or challenges
        
        Format your response with clear sections and actionable insights.
        """
    )
    
    # Get Google Trends data
    trends_data = analyze_google_trends(business_type)
    
    # Get local news data if location is provided
    if location:
        news_data = get_local_news(location, business_type)
    else:
        news_data = "No specific location provided for local news analysis."
    
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(business_idea=business_idea, trends_data=trends_data, news_data=news_data)
    return result

def run_market_analysis_agent(business_idea):
    """Market analysis agent that provides overall market assessment."""
    location = extract_location(business_idea)
    business_type = extract_business_type(business_idea)
    
    prompt = ChatPromptTemplate.from_template(
        """You are a market research analyst. Provide a comprehensive market analysis for this business idea: {business_idea}.
        
        Use this information about the local market:
        {local_data}
        
        And this information about market trends:
        {trends_data}
        
        Provide an analysis including:
        1. Estimated market size for this business type in this location
        2. Growth rate and market potential
        3. Target audience and customer segments
        4. Barriers to entry
        5. Key success factors in this market
        6. SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
        
        Your analysis should be specific to the location if provided, and include actionable insights.
        """
    )
    
    # Get local data
    local_data = run_local_search_agent(business_idea)
    
    # Get trends data
    trends_data = run_trend_analyzer_agent(business_idea)
    
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(business_idea=business_idea, local_data=local_data, trends_data=trends_data)
    return result

def generate_report(business_idea, market_analysis, competitor_analysis, trend_analysis):
    """Generate a comprehensive market research report."""
    location = extract_location(business_idea)
    business_type = extract_business_type(business_idea)
    
    title = f"Market Research Report: {business_type}"
    if location:
        title += f" in {location}"
    
    report_template = """# {title}

## Executive Summary
This report provides a comprehensive market analysis for the business idea: **{business_idea}**. 
The analysis includes location-specific data, competitor analysis, trend identification, and overall market assessment.

## Market Analysis
{market_analysis}

## Competitor Analysis
{competitor_analysis}

## Market Trends
{trend_analysis}

## Recommendations
Based on the analysis, here are the key recommendations for pursuing this business idea:

{recommendations}

## Conclusion
This report provides location-specific insights to guide your business planning. The local market analysis, competitor assessment,
and trend identification should help you develop a strategic approach to launching or growing your business.

*Generated on: {date}*
"""
    
    # Generate recommendations based on all analysis
    recommendations_prompt = ChatPromptTemplate.from_template(
        """Based on the following market analysis, competitor analysis, and trend analysis for the business idea: {business_idea},
        provide 5-7 specific, actionable recommendations for the business owner.
        
        Market Analysis:
        {market_analysis}
        
        Competitor Analysis:
        {competitor_analysis}
        
        Trend Analysis:
        {trend_analysis}
        
        Each recommendation should be clear, specific, and directly actionable.
        """
    )
    
    recommendations_chain = LLMChain(llm=llm, prompt=recommendations_prompt)
    recommendations = recommendations_chain.run(
        business_idea=business_idea,
        market_analysis=market_analysis,
        competitor_analysis=competitor_analysis,
        trend_analysis=trend_analysis
    )
    
    report = report_template.format(
        title=title,
        business_idea=business_idea,
        market_analysis=market_analysis,
        competitor_analysis=competitor_analysis,
        trend_analysis=trend_analysis,
        recommendations=recommendations,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    return report

# Streamlit app
def app():
    st.set_page_config(page_title="Local Market Research Assistant", page_icon="📊", layout="wide")
    
    st.title("🔍 Local Market Research Assistant")
    st.markdown("""
    Enter your business idea with a specific location to get realistic, location-specific market research!
    
    ### Examples:
    - "Gym in Coimbatore"
    - "Coffee shop in New York"
    - "IT consulting in Bangalore"
    
    This tool provides:
    - **Local Market Data**: Real information about local businesses
    - **Competitor Analysis**: Analysis of actual competitors in your area
    - **Location-Specific Trends**: Trends relevant to your business and location
    - **Market Assessment**: Comprehensive market analysis for your specific area
    """)
    
    business_idea = st.text_input("Enter your business idea with location:", placeholder="e.g., Gym in Coimbatore")
    
    if st.button("Generate Market Research Report"):
        if not business_idea:
            st.error("Please enter a business idea with a location.")
            return
        
        if not os.environ["GROQ_API_KEY"]:
            st.error("GROQ API key is missing. Please add it to your Streamlit secrets.")
            return
            
        if not os.environ["SERPAPI_API_KEY"]:
            st.error("SERPAPI API key is missing. Please add it to your Streamlit secrets.")
            return
        
        # Check if location is included
        location = extract_location(business_idea)
        if not location:
            st.warning("No location detected in your business idea. Including a location (e.g., 'in Coimbatore') will give you more realistic, location-specific research.")
        
        with st.spinner(f"Researching {business_idea}... This may take a few minutes."):
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Run market analysis agent
            status_text.text("Conducting market analysis...")
            market_analysis = run_market_analysis_agent(business_idea)
            progress_bar.progress(33)
            
            # Run competitor analysis agent
            status_text.text("Analyzing competitors...")
            competitor_analysis = run_competitor_analysis_agent(business_idea)
            progress_bar.progress(66)
            
            # Run trend analyzer agent
            status_text.text("Identifying market trends...")
            trend_analysis = run_trend_analyzer_agent(business_idea)
            progress_bar.progress(90)
            
            # Generate report
            status_text.text("Generating final report...")
            report = generate_report(business_idea, market_analysis, competitor_analysis, trend_analysis)
            progress_bar.progress(100)
            
            # Display report
            status_text.text("Report complete!")
            
            # Create tabs for report viewing options
            tab1, tab2 = st.tabs(["View Report", "Download Report"])
            
            with tab1:
                st.markdown(report)
            
            with tab2:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp_file:
                    tmp_file.write(report.encode())
                    tmp_file_path = tmp_file.name
                
                with open(tmp_file_path, 'rb') as f:
                    st.download_button(
                        label="Download Report as Markdown",
                        data=f,
                        file_name=f"market_research_{business_idea.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                
                # Also offer HTML version
                html_report = markdown.markdown(report)
                st.download_button(
                    label="Download Report as HTML",
                    data=html_report,
                    file_name=f"market_research_{business_idea.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )

if __name__ == "__main__":
    app()