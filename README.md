# Wine_Sommelier_Project_Bellettini

A Streamlit web app that suggests **wine pairings for a given food**, and **food pairings for a given wine**. You can also add your own custom wines (the app suggests pairings for them automatically) and mark your favorite wines.

## Features

- **Home**: pick a food and see the wines that go well with it, plus the complete list of wines. Click the star (☆ / ⭐) next to a wine to add or remove it from your favorites.
- **Search by Wine**: pick a wine and see its recommended food pairings, together with a bar chart of the foods most often paired with wines of the same type and body.
- **Add Wine**: add a custom wine by choosing a name, a type and a body. The app suggests its 5 most likely food pairings by looking at the wines with the same type and body (if none exist, it falls back to wines of the same type). Custom wines can also be deleted.

## Data

The app uses the **X-Wines** dataset, included in the `data/` folder

Your favorites and custom wines are stored locally in `user_info.json`. This file is created automatically the first time you run the app and is not tracked by Git, because it contains personal data.

| Library | Used for |
|---------|----------|
| `streamlit` (1.67.0) | web app interface |
| `pandas` (3.1.1) | loading and manipulating the data |
| `plotly` (7.1.0) | interactive bar chart |
| `numpy`  (2.5.5) | Array manipulation and standard deviation/percentile calculations |
| `scipy`  (1.18.1) | Statistical calculations ($t$-distribution CIs and Spearman rank correlation) |

The exact versions are listed in `requirements.txt`. The modules `ast`, `os`, `json` and `collections` are part of the Python standard library.

## Setup

You need Python 3 and Git installed. The commands below are for macOS or Linux; run them in the terminal.

1. Clone the repository and move into the project folder:

   ```bash
   git clone https://github.com/chiarabellettini-afk/Wine_Sommelier_Project_Bellettini.git
   cd Wine_Sommelier_Project_Bellettini
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows, activate it with `.venv\Scripts\activate` instead.

3. Install the libraries:

   ```bash
   pip install -r requirements.txt
   ```

## Run

From the root folder of the project, with the virtual environment active:

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`. Press `Ctrl + C` in the terminal to stop it.

## Project structure

```text
Wine_Sommelier_Project_Bellettini/
├── app.py                      # Main Streamlit application
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies and exact versions
├── user_info.json              # Local user data for custom wines & favorites
├── wine_sommelier/             # Package containing modular helper functions
│   ├── __init__.py
│   ├── pairing.py              # Food pairing recommendation algorithm
│   └── rating_analytics.py     # Statistical computations (Bayesian scores, t-CIs, correlation)
└── data/                       # Dataset directory
    ├── XWines_Test_100_wines.csv
    └── XWines_Test_1K_ratings.csv
```

## Notes

- If `user_info.json` becomes corrupted, the app shows a warning and a **Reset file** button that restores an empty file (all favorites and custom wines are lost).

## Author

Chiara Bellettini