# backend/app/main.py

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Import your modules
from .scraper import scrape_daraz_reviews
from .sentiment import get_sentiment
from .gsheets import save_to_google_sheet
from .models import ReviewItem, ScrapeRequest, ScrapeResponse # Ensure ReviewItem is imported

# --- Logging Setup ---
# This basicConfig is good if main.py is the entry point.
# Uvicorn might use its own logger settings, but this ensures your app's logger is configured.
logging.basicConfig(
    level=logging.INFO, # CHANGED FROM DEBUG TO INFO
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
# Load .env file from the current working directory.
# This expects .env to be in `backend/` when you run `uvicorn app.main:app --reload` from `backend/`.
load_dotenv() 
logger.info(".env file loaded (if present). Current Working Directory for .env lookup: %s", os.getcwd())
# Log the values to confirm they are loaded (be careful with sensitive data in production logs)
logger.debug("GOOGLE_SHEET_ID from env: %s", os.getenv("GOOGLE_SHEET_ID"))
logger.debug("GOOGLE_CREDENTIALS_FILE from env: %s", os.getenv("GOOGLE_CREDENTIALS_FILE"))


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Product Review Sentiment Scraper API",
    description="Scrapes product reviews, performs sentiment analysis, and saves to Google Sheets.",
    version="1.0.3" # Incremented version
)

# --- CORS (Cross-Origin Resource Sharing) ---
# Allows your Next.js frontend (running on http://localhost:3000) to communicate with this API.
origins = [
    "http://localhost:3000",
    # Add any other origins if needed (e.g., your deployed frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Allow specific origins
    allow_credentials=True,    # Allow cookies to be included in requests
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
)
logger.info(f"CORS middleware configured for origins: {origins}")

# --- API Endpoints ---

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    logger.info("Root endpoint '/' accessed.")
    return {"message": "Welcome to the Product Review Sentiment Scraper API!"}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_reviews_endpoint(request: ScrapeRequest = Body(...)):
    """
    Scrapes product reviews from the given URL, performs sentiment analysis,
    saves to Google Sheets, and returns the processed data.
    """
    # !!!!! ULTRA-EARLY LOGGING LINE !!!!!
    logger.info(f"!!!!!! --- /scrape endpoint ENTERED. Request object: {request} --- !!!!!!") 
    
    product_url = request.product_url
    if not product_url: 
        logger.warning("Scrape request: product_url is empty in the request.")
        raise HTTPException(status_code=400, detail="product_url is required in the request body.")

    logger.info(f"Processing scrape request for URL: {product_url}")

    # 1. Scrape reviews
    scraped_reviews_raw = [] # Initialize to prevent potential UnboundLocalError if try block fails early
    try:
        logger.info(f"Calling scraper function for URL: {product_url}")
        # Using max_reviews=5 for faster debugging initially, change back to 50 later
        scraped_reviews_raw = scrape_daraz_reviews(product_url, max_reviews=50) 
        
        if not scraped_reviews_raw: # Scraper function itself returned an empty list
            logger.warning(f"Scraper function returned no reviews for URL: {product_url}.")
            # This is a specific case where scraping happened but found nothing.
            raise HTTPException(status_code=404, detail=f"No reviews were found by the scraper for the product at {product_url}. This could be due to incorrect selectors in 'scraper.py', the product having no reviews, or reviews being loaded dynamically in a way the current scraper can't handle.")
        logger.info(f"Scraper function returned {len(scraped_reviews_raw)} raw review items.")

    except HTTPException as e_http: # Re-raise HTTPExceptions (like the 404 above)
        logger.warning(f"HTTPException during scraping stage: {e_http.detail}")
        raise e_http
    except Exception as e_scrape: # Catch any other unexpected error from the scraper function
        logger.error(f"Unexpected error during scraping process for {product_url}: {e_scrape}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scraping process encountered an unexpected error: {str(e_scrape)}")

    # 2. Clean text (already done in scraper ideally) and perform sentiment analysis
    processed_reviews_for_response: list[ReviewItem] = []
    processed_reviews_for_sheets: list[dict] = [] # For gsheets which expects list of dicts

    logger.info("Performing sentiment analysis for scraped reviews...")
    for review_raw in scraped_reviews_raw: # This loop won't run if scraped_reviews_raw is empty
        cleaned_text = review_raw.get("review_text", "") 
        
        if not cleaned_text: # Skip if for some reason review text is empty after scraping
            logger.debug(f"Skipping a review for product '{review_raw.get('product_name')}' due to empty review text after scraping.")
            continue

        sentiment_label, sentiment_score = get_sentiment(cleaned_text)
        
        review_item_data = ReviewItem(
            product_name=str(review_raw.get("product_name", "N/A")),
            review_text=cleaned_text,
            rating=str(review_raw.get("rating", "N/A")), 
            sentiment_label=sentiment_label,
            sentiment_score=round(sentiment_score, 4), # Round score for consistency
        )
        processed_reviews_for_response.append(review_item_data)
        processed_reviews_for_sheets.append(review_item_data.model_dump()) # Convert Pydantic model to dict for gspread

    if not processed_reviews_for_response: # This means scraped_reviews_raw was not empty, but all items had no text
         logger.warning("No reviews were processable after sentiment analysis (e.g., all scraped items had empty text fields).")
         raise HTTPException(status_code=404, detail="Although items might have been scraped, no actual review text was found to process for sentiment analysis.")
    logger.info(f"Successfully processed {len(processed_reviews_for_response)} reviews with sentiment.")


    # 3. Save to Google Sheets
    google_sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not google_sheet_id:
        logger.error("CRITICAL: GOOGLE_SHEET_ID not configured in environment variables.")
        raise HTTPException(status_code=500, detail="Server configuration error: Google Sheet ID missing.")

    sheet_url = "" # Initialize
    try:
        logger.info(f"Attempting to save {len(processed_reviews_for_sheets)} reviews to Google Sheet ID: {google_sheet_id}")
        sheet_url = save_to_google_sheet(processed_reviews_for_sheets, google_sheet_id)
        logger.info(f"Data successfully saved to Google Sheet: {sheet_url}")
    except FileNotFoundError as e_fnf: # Specifically catch if credentials file is missing from gsheets module
        logger.error(f"Google Sheets credentials file error: {e_fnf}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server configuration error related to Google Sheets credentials: {str(e_fnf)}")
    except Exception as e_gsheet: # Catch any other exception from gsheets module
        logger.error(f"Failed to save data to Google Sheets: {e_gsheet}", exc_info=True)
        # It's important that save_to_google_sheet raises an exception if it fails,
        # or this generic catch might not be as useful.
        raise HTTPException(status_code=500, detail=f"Failed to save data to Google Sheets: {str(e_gsheet)}")

    # 4. Return saved data as JSON 
    logger.info("Scraping, analysis, and saving completed successfully. Returning response.")
    return ScrapeResponse(
        message="Scraping, analysis, and saving to Google Sheets completed successfully.",
        data=processed_reviews_for_response, 
        sheet_url=sheet_url
    )

# To run (from backend/ directory with venv active):
# uvicorn app.main:app --reload