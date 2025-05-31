# Product Review Sentiment Scraper

This project scrapes product reviews from an e-commerce site (specifically Daraz.pk), performs sentiment analysis on the reviews, saves the processed data to a Google Sheet, and displays the reviews, sentiment labels, and sentiment distribution charts on a web interface.

The backend is built with FastAPI, and the frontend is built with Next.js.


## Features

*   **Backend (FastAPI):**
    *   Scrapes product name from the main product page using Selenium.
    *   Extracts product `itemId` from the URL.
    *   Fetches product reviews by calling an internal Daraz API endpoint using the `itemId`.
    *   Performs sentiment analysis on review text using TextBlob.
    *   Saves product name, review text, rating, sentiment label, and sentiment score to a Google Sheet.
    *   Returns the processed data as JSON.
*   **Frontend (Next.js):**
    *   Allows users to input a Daraz.pk product URL.
    *   Calls the FastAPI backend to trigger scraping and data processing.
    *   Displays scraped reviews in a sortable table.
    *   Visualizes sentiment distribution using interactive Bar and Pie charts.
    *   Provides a link to the Google Sheet containing the scraped data.

## Tech Stack

*   **Backend:** Python, FastAPI, Uvicorn, Selenium, BeautifulSoup4, Requests, TextBlob, gspread, python-dotenv
*   **Frontend:** Node.js, Next.js, React, Chart.js (react-chartjs-2)
*   **Database/Storage:** Google Sheets
*   **APIs:** Google Sheets API

## Prerequisites

*   Python 3.8+
*   Node.js 16+ and npm (or yarn/pnpm/bun)
*   A Google Cloud Platform (GCP) Account
*   Google Chrome browser installed (for Selenium's ChromeDriver)

## Setup Instructions

### 1. Google Cloud & Sheets API Setup

Follow these steps to set up the necessary Google Cloud services:

1.  **Create a Google Cloud Project:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (e.g., "DarazReviewScraper").
2.  **Enable Google Sheets API & Google Drive API:**
    *   In your GCP project, navigate to "APIs & Services" > "Library".
    *   Search for "Google Sheets API" and **enable** it.
    *   Search for "Google Drive API" (gspread uses this for discovering sheets by name/ID and permissions) and **enable** it.
3.  **Create Service Account Credentials:**
    *   Go to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "Service account".
    *   Enter a service account name (e.g., `daraz-sheets-writer`).
    *   Click "CREATE AND CONTINUE".
    *   Grant the service account a role: For simplicity in this project, assign "Editor" (Project > Editor). For production, you would create a more restricted custom role with only necessary Sheets/Drive permissions.
    *   Click "CONTINUE", then "DONE".
    *   Find your newly created service account in the list. Click on its email address.
    *   Go to the "KEYS" tab.
    *   Click "ADD KEY" > "Create new key".
    *   Choose "JSON" as the key type and click "CREATE".
    *   A JSON file will download. Rename this file to `google_credentials.json`.
    *   **Important:** Place this `google_credentials.json` file inside the `backend/` directory of your project.
4.  **Create a Google Sheet:**
    *   Go to [Google Sheets](https://sheets.google.com/) and create a new blank spreadsheet.
    *   Name it (e.g., "Daraz Product Reviews").
    *   Note down its **Sheet ID** from the URL. The URL will look like: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_IS_HERE/edit`. Copy the long string that is your Sheet ID.
5.  **Share the Google Sheet with the Service Account:**
    *   Open the `google_credentials.json` file you downloaded. Find the `client_email` address (it looks like an email, e.g., `your-service-account-name@your-project-id.iam.gserviceaccount.com`).
    *   In your Google Sheet, click the "Share" button (top right).
    *   Paste the service account's `client_email` address into the "Add people and groups" field.
    *   Ensure it has **"Editor"** permissions for this sheet. This step is crucial for the application to write data to the sheet.
    *   Click "Send" (you can uncheck "Notify people").

### 2. Backend (FastAPI) Setup

1.  **Navigate to the `backend` directory:**
    ```bash
    cd path/to/your/project/backend
    ```
2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows:
    .\.venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```
3.  **Install Python dependencies:**
    *   The `requirements.txt` file is located in this `backend/` directory.
    ```bash
    pip install -r requirements.txt
    ```
    *(This will also install `webdriver-manager` which handles `chromedriver` automatically).*
4.  **Create the Environment File (`.env`):**
    *   In the `backend/` directory, you can create a `.env` file by copying the `backend/.env.example` file (if you've created one, see "Example Environment Files" below) or by creating a new file named `.env`.
    *   Add the following content, replacing `YOUR_GOOGLE_SHEET_ID_HERE` with the ID you copied in step 1.4:
        ```env
        GOOGLE_SHEET_ID="YOUR_GOOGLE_SHEET_ID_HERE"
        GOOGLE_CREDENTIALS_FILE="google_credentials.json"
        ```
    *   Ensure `google_credentials.json` (obtained from Google Cloud Console as described in step 1.3) is in the `backend/` directory.

### 3. Frontend (Next.js) Setup

1.  **Navigate to the `frontend` directory:**
    ```bash
    cd path/to/your/project/frontend
    ```
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    # or
    # yarn install
    # or
    # pnpm install
    ```
3.  **Create the Environment File (`.env.local`):**
    *   In the `frontend/` directory, you can create a `.env.local` file by copying the `frontend/.env.local.example` file (if you've created one, see "Example Environment Files" below) or by creating a new file named `.env.local`.
    *   Add the following content:
        ```env
        NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
        ```
    *   This tells the frontend where your FastAPI backend is running.

### Example Environment Files (Recommended)

It's good practice to include example environment files in your repository.

*   **`backend/.env.example`:**
    ```env
    GOOGLE_SHEET_ID="YOUR_GOOGLE_SHEET_ID_HERE"
    GOOGLE_CREDENTIALS_FILE="google_credentials.json"
    ```
*   **`frontend/.env.local.example`:**
    ```env
    NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
    ```
You would then instruct users to copy these example files to `.env` (for backend) and `.env.local` (for frontend) respectively, and then fill in their specific values. Remember to add these example files to Git but keep the actual `.env` and `.env.local` files in your `.gitignore`.

## Running the Application

1.  **Start the Backend Server:**
    *   Open a terminal, navigate to the `backend/` directory.
    *   Activate the Python virtual environment (if not already active).
    *   Run Uvicorn:
        ```bash
        uvicorn app.main:app --reload
        ```
    *   The backend API should now be running on `http://localhost:8000`.

2.  **Start the Frontend Development Server:**
    *   Open a **new** terminal, navigate to the `frontend/` directory.
    *   Run the Next.js development server:
        ```bash
        npm run dev
        # or yarn dev / pnpm dev / bun dev
        ```
    *   The frontend should now be accessible at `http://localhost:3000`.

3.  **Using the Application:**
    *   Open `http://localhost:3000` in your browser.
    *   Paste a valid Daraz.pk product URL into the input field.
    *   Click "Scrape Reviews".
    *   Wait for the process to complete. The reviews, sentiment analysis, and charts will be displayed. A link to the populated Google Sheet will also appear.

## Notes on Daraz Scraping

*   This scraper uses Selenium to load the initial product page and extract the product name and `itemId`.
*   It then uses a known Daraz API endpoint (`my.daraz.pk/pdp/review/getReviewList`) to fetch the actual review data in JSON format. This is generally more reliable than parsing HTML for all reviews.
*   The `itemId` is extracted from the product URL using a regular expression. This should work for most standard Daraz product URLs.
*   If Daraz changes its API endpoint, API response structure, or URL patterns for `itemId`, the scraper might need updates.
*   Web scraping, especially of large e-commerce sites, can be fragile. Selectors for the product name might change over time.

## Learn More (Next.js Boilerplate)

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel (Next.js Boilerplate)

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
(Note: Deploying the FastAPI backend would require a separate hosting solution like Heroku, PythonAnywhere, Docker on a VPS, or serverless functions.)
