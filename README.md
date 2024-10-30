
## How Risky Can It Be? Simulating Returns of Index Funds and Their 2x Daily Leveraged “Evil Twins”

In 2019, I cautiously invested a small portion of my savings in a 2x Daily Leveraged S&P 500 index fund. Five years later, this “test” became my best investment to date. But should I commit more? How can I balance the elevated risk?

To tackle these questions, I needed a fact-based approach to understand how leveraged investments work and how they compare to standard total market index funds. This tool simulates millions of possible outcomes across different strategies, leveraging historical returns of major indices worldwide.

The fund fees are hardcoded to match the specific funds I hold in my PEA (Plan d’Epargne en Actions). I experimented with multiple strategies, though this benchmark assumes a continuous annual investment of €10,000 (approximately €830 per month).

See the results for yourself! Access the app here: https://leveraged.streamlit.app/

---

## Table of Contents

- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
- [Usage](#usage)
  - [Running Simulations](#running-simulations)
  - [Viewing Results](#viewing-results)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [License](#license)

---

## Setup

### Prerequisites

1. **Google Cloud Account**: Required for storing simulation results in Google Cloud Storage (GCS).
2. **GCS Bucket**: Create a dedicated bucket to store simulation results, plots, and configuration files.
3. **Service Account and Credentials**: Set up a Google Cloud service account with storage permissions, and download its JSON credentials.

### Environment Setup

#### 1. Clone the Repository

   ```bash
   git clone https://github.com/Tcha182/Backtest
   cd Backtest
   ```

#### 2. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

#### 3. Configure Streamlit Secrets

   Store your Google Cloud credentials in `.streamlit/secrets.toml` for seamless access to GCS:

   ```toml
   # .streamlit/secrets.toml
   [GS_CREDENTIALS]
   GS_BUCKET_NAME = "your-gcs-bucket-name"
   type = "service_account"
   project_id = "your-gcs-project-id"
   private_key_id = "your-private-key-id"
   private_key = "-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY
-----END PRIVATE KEY-----
"
   client_email = "your-service-account-email@your-project.iam.gserviceaccount.com"
   client_id = "your-client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "your-cert-url"
   ```

#### 4. Upload `indices.json` Configuration File

   Place the `indices.json` file in your GCS bucket under the path `config/indices.json`. This file contains details about each index (ticker, start date, etc.).

#### 5. Optional: Preload `processed_indices.json`

   If simulations have been previously run, upload a `processed_indices.json` file containing the completed indices to `config/processed_indices.json` in your GCS bucket.

---

## Usage

### Running Simulations

1. **Start the Streamlit App**

   Run the following command to start the application:

   ```bash
   streamlit run simulation_page.py
   ```

2. **Select Simulation Parameters**

   - **Number of Simulations**: Set the number of simulations to run.
   - **Minimum and Maximum Duration**: Define the investment duration in years.
   - **Indices**: Choose from available global indices listed in `indices.json`.

3. **Run Simulations**

   Click the `Run Simulations` button. The application will:
   - Fetch historical data for the selected index.
   - Simulate investments with chosen parameters.
   - Save simulation results and plots to GCS.

### Viewing Results

1. **Start the Results Display App**

   To view saved simulation results, run:

   ```bash
   streamlit run display_page.py
   ```

2. **Select Parameters in the Sidebar**

   - Choose the index from the available options.
   - Select the duration and view relevant metrics, distribution plots, risk curves, and more.

3. **Plot Display**

   The application fetches relevant plots (distribution, risk, box plots) from GCS and displays them for easy analysis.

---

## Configuration

- **`indices.json`**: Stores information about each index (e.g., ticker symbol, start date). This file should be saved in GCS under `config/indices.json`.
- **`processed_indices.json`**: (Optional) Tracks processed indices. This file should be saved to `config/processed_indices.json` in GCS.

---

## Project Structure

```
investment-simulation/
├── simulation_page.py           # Main simulation app
├── display_page.py              # Result display app
├── gcs_utils.py                 # Helper functions for GCS operations
├── requirements.txt             # Python dependencies
├── config/                      # Configurations directory
└── .streamlit/
    └── secrets.toml             # Streamlit secrets for Google Cloud credentials
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

## Authors

Created by [Corentin de Tilly](https://github.com/Tcha182). Contributions are welcome!
