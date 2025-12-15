#!/usr/bin/env python3
"""
FastAPI Backend for Email Insight Engine
Provides REST API endpoint to analyze emails and return categorized insights
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from app.email_insight_engine import EmailInsightEngine

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Email Insight Engine API",
    description="API for analyzing emails and extracting categorized insights",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class AnalysisRequest(BaseModel):
    email_address: Optional[str] = Field(None, description="Email address to analyze (defaults to EMAIL_ADDRESS env var)")
    email_password: Optional[str] = Field(None, description="Email password (defaults to EMAIL_PASSWORD env var)")
    imap_server: Optional[str] = Field("imap.gmail.com", description="IMAP server address")
    gemini_api_key: Optional[str] = Field(None, description="Gemini API key (defaults to GEMINI_API_KEY env var)")
    gemini_model: Optional[str] = Field("gemini-2.5-flash", description="Gemini model to use")
    folders: Optional[List[str]] = Field(None, description="List of folders to analyze")
    days_back: int = Field(10, description="Number of days to analyze", ge=1, le=90)
    batch_size: int = Field(10, description="Batch size for AI processing", ge=1, le=50)
    confidence_threshold: float = Field(0.6, description="Minimum confidence for entity extraction", ge=0.0, le=1.0)
    batch_delay: int = Field(3, description="Seconds to wait between batches", ge=0)
    max_retries: int = Field(5, description="Maximum retry attempts for API errors", ge=1, le=10)

    class Config:
        schema_extra = {
            "example": {
                "days_back": 7,
                "batch_size": 10,
                "folders": ["INBOX", "[Gmail]/Sent Mail"]
            }
        }


# Response Models
class AnalysisResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    results: Dict[str, List[Any]]
    summary: Dict[str, int]


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str


# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "success",
        "message": "Email Insight Engine API is running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is operational",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_emails(request: AnalysisRequest):
    """
    Analyze emails and return categorized insights

    This endpoint runs the full email analysis pipeline and returns:
    - IMPORTANCE: Important emails
    - URGENCY: Urgent emails
    - INFORMATIONAL: News/newsletters/updates
    - SCHEDULE: Emails with calendar events
    - COMMITMENTS: Commitments from others
    - OUTBOUND_COMMITMENTS: Your commitments
    - REQUESTS: Tasks/requests
    - DEADLINES: Emails with deadlines

    Returns:
        AnalysisResponse: Categorized email insights
    """
    try:
        # Initialize the Email Insight Engine with request parameters
        engine = EmailInsightEngine(
            email_address=request.email_address,
            email_password=request.email_password,
            imap_server=request.imap_server,
            gemini_api_key=request.gemini_api_key,
            gemini_model=request.gemini_model,
            folders=request.folders,
            days_back=request.days_back,
            batch_size=request.batch_size,
            confidence_threshold=request.confidence_threshold,
            batch_delay=request.batch_delay,
            max_retries=request.max_retries
        )

        # Run full analysis
        results = engine.run_full_analysis()

        # If no results, return empty structure
        if not results:
            results = {
                "IMPORTANCE": [],
                "URGENCY": [],
                "INFORMATIONAL": [],
                "SCHEDULE": [],
                "COMMITMENTS": [],
                "OUTBOUND_COMMITMENTS": [],
                "REQUESTS": [],
                "DEADLINES": []
            }

        # Calculate summary statistics
        summary = {
            category: len(emails)
            for category, emails in results.items()
        }

        return {
            "status": "success",
            "message": "Email analysis completed successfully",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": summary
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/categories")
async def get_categories():
    """
    Get available email categories

    Returns:
        dict: Available categories and their descriptions
    """
    return {
        "categories": {
            "IMPORTANCE": "Emails tagged as important",
            "URGENCY": "Emails tagged as urgent",
            "INFORMATIONAL": "News, newsletters, and updates",
            "SCHEDULE": "Emails with calendar events or important dates",
            "COMMITMENTS": "Commitments made by others to you",
            "OUTBOUND_COMMITMENTS": "Commitments you made to others",
            "REQUESTS": "Tasks and requests",
            "DEADLINES": "Emails with deadlines"
        }
    }


# Run the application
if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "app.api:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
