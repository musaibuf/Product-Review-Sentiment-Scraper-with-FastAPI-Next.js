# backend/app/scraper.py
import requests
from bs4 import BeautifulSoup
import re
import time
import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

# Selectors for product name from the main product page (still needed)
DARAZ_PRODUCT_INFO_SELECTORS = {
    "product_name_container": "pdp-mod-product-badge-title",
    # "brand_name_link": "pdp-product-brand__brand-link", # Optional
}

def clean_text(text):
    if text:
        text = re.sub(r'\s+', ' ', text)
        # Keep basic punctuation for review text, but remove for product name if it causes issues
        # For product name, being more aggressive with cleaning might be okay:
        # text = text.replace(',', '').replace('\n', ' ').replace('\t', ' ')
        return text.strip()
    return ""

def extract_item_id_from_url(product_url):
    # Standard pattern: ...-i<ITEM_ID>-s<SKU_ID>.html
    # Or sometimes: ...-i<ITEM_ID>.html before the -s part or query params
    match = re.search(r'-i(\d+)', product_url) # Simpler regex to get numbers after -i
    if match:
        item_id = match.group(1)
        logger.info(f"Extracted itemId: {item_id} from URL: {product_url}")
        return item_id
    else:
        logger.error(f"Could not extract itemId using '-i(\\d+)' pattern from URL: {product_url}")
        # Fallback: Try to find numbers after /products/ if the above fails and before .html or ?
        match_fallback = re.search(r'/products/.*?(\d{9,})', product_url) # Look for a sequence of 9+ digits
        if match_fallback:
            item_id = match_fallback.group(1)
            logger.info(f"Extracted itemId (fallback pattern): {item_id} from URL: {product_url}")
            return item_id
        else:
            logger.error(f"Fallback itemId extraction also failed for URL: {product_url}")
            return None


def scrape_daraz_reviews(product_url: str, max_reviews: int = 50):
    logger.info(f"API-Based Scraper: Initiating for URL: {product_url}")
    reviews_data = []
    processed_reviews_count = 0

    item_id = extract_item_id_from_url(product_url)
    if not item_id:
        logger.error("Failed to get item_id, cannot fetch reviews from API.")
        return []

    # --- Use Selenium briefly to get Product Name ---
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36")

    product_name = "Unknown Product"
    driver = None
    try:
        logger.info("Selenium (for product info): Initializing WebDriver...")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30) # 30-second timeout for page load
        
        page_loaded_successfully = False
        for attempt in range(2): # Try twice to load the page
            try:
                logger.info(f"Selenium (for product info): Navigating to {product_url} (Attempt {attempt + 1})")
                driver.get(product_url)
                logger.info(f"Selenium (for product info): Page loaded. Title: '{driver.title}'")
                if "daraz.pk" in driver.current_url.lower() and "error" not in driver.title.lower() and "captcha" not in driver.title.lower():
                    page_loaded_successfully = True
                    break
                else:
                    logger.warning(f"Selenium (for product info): Suspicious page load. URL: {driver.current_url}, Title: '{driver.title}'")
            except TimeoutException:
                logger.error(f"Selenium (for product info): Page load TIMEOUT for {product_url} on attempt {attempt + 1}.")
                if attempt < 1: time.sleep(2)
            except WebDriverException as e_wd_get:
                logger.error(f"Selenium (for product info): WebDriverException during get() on attempt {attempt+1}: {e_wd_get}")
                if attempt < 1: time.sleep(2)
        
        if page_loaded_successfully:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            pn_selector = DARAZ_PRODUCT_INFO_SELECTORS["product_name_container"]
            product_name_tag = soup.find(class_=pn_selector)
            if not product_name_tag: product_name_tag = soup.find('h1') # Fallback
            if product_name_tag:
                product_name = clean_text(product_name_tag.get_text())
            logger.info(f"Selenium (for product info): Product Name Scraped: '{product_name}'")
        else:
            logger.warning(f"Selenium (for product info): Failed to load product page correctly to get product name. Using default: '{product_name}'")

    except WebDriverException as e_wd_main: # Catch errors during WebDriver setup/main ops
        logger.error(f"Selenium (for product info): Main WebDriverException: {e_wd_main}", exc_info=False)
    except Exception as e_sel:
        logger.error(f"Selenium (for product info): Generic error getting product details: {e_sel}", exc_info=False)
    finally:
        if driver:
            driver.quit()
            logger.info("Selenium (for product info): WebDriver quit.")
    # --- End Selenium part for product name ---

    # --- Fetch reviews using the API ---
    logger.info(f"Fetching reviews from API for itemId: {item_id}, Product Name: '{product_name}'")
    page_no = 1
    api_page_size = 20 # Number of reviews to fetch per API call

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": product_url 
    }

    while processed_reviews_count < max_reviews:
        review_api_url = f'https://my.daraz.pk/pdp/review/getReviewList?itemId={item_id}&pageSize={api_page_size}&filter=0&sort=0&pageNo={page_no}'
        logger.info(f"Fetching reviews: {review_api_url}")
        try:
            response = session.get(review_api_url, headers=headers, timeout=15)
            response.raise_for_status()
            review_json = response.json()

            if not review_json or 'model' not in review_json or 'items' not in review_json['model']:
                logger.warning(f"Review API response format unexpected or model/items missing. Stopping. Response: {str(review_json)[:200]}")
                break 
            
            api_reviews_list = review_json['model']['items']
            if not api_reviews_list:
                logger.info("API returned no more review items. End of reviews.")
                break
            
            logger.info(f"API returned {len(api_reviews_list)} items for page {page_no}.")

            for review_item_api in api_reviews_list:
                if processed_reviews_count >= max_reviews:
                    break
                
                review_text = clean_text(review_item_api.get('reviewContent', ''))
                
                # --- RATING KEY - VERIFY THIS by printing review_item_api ---
                # Common keys: 'ratingStar', 'rating', 'star', 'reviewRating', 'score'
                # The GitHub script implies 'ratingStar' is often used.
                rating_value = review_item_api.get('ratingStar') # Get the value directly
                if rating_value is not None:
                    rating = str(rating_value)
                else:
                    # If 'ratingStar' is not found or None, try other common keys or default to N/A
                    rating = str(review_item_api.get('rating', 'N/A')) 
                    if rating == 'N/A': # If 'rating' also N/A, log the item for inspection
                         logger.debug(f"Rating key 'ratingStar' or 'rating' not found or None in API item. Item: {review_item_api}")
                # --- END RATING KEY ---

                if review_text:
                    reviews_data.append({
                        "product_name": product_name,
                        "review_text": review_text,
                        "rating": rating
                    })
                    processed_reviews_count += 1
                    logger.debug(f"  Added review via API ({processed_reviews_count}/{max_reviews}): Rating: {rating} - Text: {review_text[:50]}...")
                else:
                    logger.debug("Skipped an API review item due to empty reviewContent.")
            
            page_no += 1
            if len(api_reviews_list) < api_page_size:
                logger.info("API returned fewer items than page size, assuming last page.")
                break
            if processed_reviews_count < max_reviews: # Only sleep if we need more reviews
                time.sleep(0.5 + (os.urandom(1)[0] / 255.0) * 0.5) # Small random delay 0.5s-1s

        except requests.exceptions.RequestException as e_req:
            logger.error(f"Error fetching reviews from API: {e_req}", exc_info=True)
            break 
        except ValueError as e_json: # Handles JSONDecodeError
            logger.error(f"Error decoding JSON from review API. URL: {review_api_url}. Response text: {response.text[:300]}", exc_info=True)
            break
        except Exception as e_api_loop:
            logger.error(f"Unexpected error in API review fetching loop: {e_api_loop}", exc_info=True)
            break

    logger.info(f"API-Based Scraper: Finished. Total reviews fetched: {len(reviews_data)}")
    return reviews_data[:max_reviews]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Test with a product URL known to have reviews and the common URL structure
    test_url = "https://www.daraz.pk/products/brite-maximum-power-500g-detergent-washing-powder-i216038129-s1425644897.html"
    # test_url = "https://www.daraz.pk/products/audionic-airbud-590-heavy-bass-speedy-charging-i445073070-s2100003004.html" # Another example
    
    logger.info(f"--- STARTING API-BASED SCRAPER TEST (DIRECT RUN) ---")
    # Test with a number of reviews that might require pagination from the API
    scraped_data = scrape_daraz_reviews(test_url, max_reviews=50) 
    
    logger.info(f"--- API-BASED SCRAPER TEST (DIRECT RUN) FINISHED ---")
    if scraped_data:
        logger.info(f"Direct run successfully scraped {len(scraped_data)} reviews:")
        for i, review in enumerate(scraped_data):
            logger.info(f"--- Review {i+1} ---")
            logger.info(f"  Product: {review['product_name']}")
            logger.info(f"  Rating: {review['rating']}") # CHECK THIS OUTPUT
            logger.info(f"  Review Text (first 70 chars): {review['review_text'][:70]}...")
    else:
        logger.warning("--- Direct run: No reviews were scraped using the API method. Check logs for errors (itemId extraction, API calls, JSON parsing). ---")