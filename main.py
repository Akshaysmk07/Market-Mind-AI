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
import firecrawl
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from pytrends.request import TrendReq
import praw
from datetime import datetime

# Set up environment variables
os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", "")  # Get from Streamlit secrets


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
    website: Optional[str] = Field(description="Company website")
    description: str = Field(description="Brief description of what they offer")
    pricing: Optional[str] = Field(description="Pricing information if available")
    strengths: List[str] = Field(description="Company strengths")
    weaknesses: List[str] = Field(description="Company weaknesses")

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
def search_web(query):
    """Search the web for the given query using FireCrawl."""
    try:
        results = firecrawl.search(query, max_results=5)
        return json.dumps([{
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet
        } for r in results])
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

def search_reddit(query):
    """Search Reddit for discussions related to the query."""
    try:
        # Initialize Reddit client (read-only mode)
        reddit = praw.Reddit(
            client_id="YOUR_CLIENT_ID",  # Replace with your Reddit client ID
            client_secret="YOUR_CLIENT_SECRET",  # Replace with your Reddit client secret
            user_agent="market_research_assistant/1.0"
        )
        
        # Search for relevant posts in business-related subreddits
        subreddits = ['startups', 'entrepreneur', 'smallbusiness']
        results = []
        
        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.search(query, limit=3):
                results.append({
                    "title": post.title,
                    "url": f"https://www.reddit.com{post.permalink}",
                    "score": post.score,
                    "comments": post.num_comments,
                    "created": datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d'),
                    "subreddit": subreddit_name
                })
        
        if not results:
            return f"No relevant Reddit posts found for '{query}'"
        
        return json.dumps(results)
    except Exception as e:
        return f"Error searching Reddit: {str(e)}"

# Define tools list
tools = [
    Tool(
        name="Search",
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
        name="SearchReddit",
        func=search_reddit,
        description="Search Reddit for discussions related to a business idea."
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

# Task agents for specific functions
def run_web_crawler_agent(business_idea):
    """Web crawler agent that finds general information about the business domain."""
    prompt = ChatPromptTemplate.from_template(
        """You are a web research specialist. Research the following business idea: {business_idea}.
        Focus on finding market size, industry growth rate, and key market insights.
        Use the search tool to find relevant information and then synthesize it into a concise report.
        """
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(business_idea=business_idea)
    return result

def run_competitor_analysis_agent(business_idea):
    """Competitor analysis agent that identifies and analyzes competitors."""
    parser = PydanticOutputParser(pydantic_object=Competitor)
    
    prompt = ChatPromptTemplate.from_template(
        """You are a competitive intelligence specialist. Identify and analyze key competitors for this business idea: {business_idea}.
        For each competitor, provide:
        1. Company name
        2. Website (if you know it)
        3. Description of their offerings
        4. Pricing information (if available)
        5. Their strengths
        6. Their weaknesses
        
        Format your response as a list of competitors with the requested information for each.
        {format_instructions}
        """
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt.partial(format_instructions=parser.get_format_instructions())
    )
    
    result = chain.run(business_idea=business_idea)
    return result

def run_trend_analyzer_agent(business_idea):
    """Trend analyzer agent that identifies market trends."""
    parser = PydanticOutputParser(pydantic_object=MarketTrend)
    
    prompt = ChatPromptTemplate.from_template(
        """You are a market trend analyst. Identify current trends related to this business idea: {business_idea}.
        Use Google Trends data and Reddit discussions to identify emerging patterns and consumer behaviors.
        For each trend, provide:
        1. Trend name
        2. Description
        3. Potential impact on the business idea
        4. Source of the trend information
        
        Format your response as a list of trends with the requested information for each.
        {format_instructions}
        """
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt.partial(format_instructions=parser.get_format_instructions())
    )
    
    result = chain.run(business_idea=business_idea)
    return result

def run_market_analysis_agent(business_idea):
    """Market analysis agent that provides overall market assessment."""
    parser = PydanticOutputParser(pydantic_object=MarketAnalysis)
    
    prompt = ChatPromptTemplate.from_template(
        """You are a market research analyst. Analyze the market for this business idea: {business_idea}.
        Provide:
        1. Estimated market size
        2. Growth rate
        3. Target audience description
        4. Barriers to entry
        5. Market opportunities
        6. Market threats
        
        Format your response using the requested structure.
        {format_instructions}
        """
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt.partial(format_instructions=parser.get_format_instructions())
    )
    
    result = chain.run(business_idea=business_idea)
    return result

def generate_report(business_idea, web_crawler_results, competitor_analysis, trend_analysis, market_analysis):
    """Generate a comprehensive market research report."""
    report_template = """# Market Research Report: {business_idea}

## Executive Summary
This report provides a comprehensive market analysis for the business idea: **{business_idea}**. 
The analysis includes market size estimation, competitor analysis, trend identification, and overall market assessment.

## Market Overview
{web_crawler_results}

## Market Analysis
{market_analysis}

## Competitor Analysis
{competitor_analysis}

## Market Trends
{trend_analysis}

## Recommendations
Based on the analysis, here are the key recommendations for pursuing this business idea:
1. Consider the market size and growth potential identified in the report.
2. Evaluate the competitive landscape and identify potential differentiators.
3. Align your business strategy with emerging trends in the market.
4. Address potential barriers to entry through strategic planning.

## Conclusion
This report provides initial insights to guide business planning. Further in-depth research is recommended 
for specific areas of interest identified in this report.

*Generated on: {date}*
"""
    
    report = report_template.format(
        business_idea=business_idea,
        web_crawler_results=web_crawler_results,
        competitor_analysis=competitor_analysis,
        trend_analysis=trend_analysis,
        market_analysis=market_analysis,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    return report

# Streamlit app
def app():
    st.set_page_config(page_title="Automated Market Research Assistant", page_icon="📊", layout="wide")
    
    st.title("🔍 Automated Market Research Assistant")
    st.markdown("""
    Enter your business idea below, and our AI agents will conduct market research for you!
    This tool uses:
    - **Web Crawler Agent**: Finds general market information
    - **Competitor Analysis Agent**: Identifies and analyzes competitors
    - **Trend Analyzer Agent**: Tracks industry trends
    - **Market Analysis Agent**: Provides overall market assessment
    """)
    
    business_idea = st.text_input("Enter your business idea:", placeholder="e.g., Online Pet Accessories Store")
    
    if st.button("Generate Market Research Report"):
        if not business_idea:
            st.error("Please enter a business idea.")
            return
        
        if not os.environ["GROQ_API_KEY"]:
            st.error("GROQ API key is missing. Please add it to your Streamlit secrets.")
            return
        
        with st.spinner("Researching your business idea... This may take a few minutes."):
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Run web crawler agent
            status_text.text("Gathering market information...")
            web_crawler_results = run_web_crawler_agent(business_idea)
            progress_bar.progress(25)
            
            # Run competitor analysis agent
            status_text.text("Analyzing competitors...")
            competitor_analysis = run_competitor_analysis_agent(business_idea)
            progress_bar.progress(50)
            
            # Run trend analyzer agent
            status_text.text("Identifying market trends...")
            trend_analysis = run_trend_analyzer_agent(business_idea)
            progress_bar.progress(75)
            
            # Run market analysis agent
            status_text.text("Conducting overall market assessment...")
            market_analysis = run_market_analysis_agent(business_idea)
            progress_bar.progress(90)
            
            # Generate report
            status_text.text("Generating final report...")
            report = generate_report(business_idea, web_crawler_results, competitor_analysis, trend_analysis, market_analysis)
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