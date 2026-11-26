"""
wine_sommelier - a small library to find food pairings for wines and explore
wine ratings.

The package is organised in modules, each one with a single responsibility:

- ``data_loader``        : load the X-Wines CSV files and build the wine table
- ``pairing``            : suggest wines for a given food and foods for a given wine
- ``user_store``         : save favorites and custom wines in a JSON file
- ``rating_analytics``   : rating statistics (confidence intervals, Bayesian
                           score, vintage correlation) with numpy and scipy
- ``feature_analytics``  : correlations between wine features (ABV, body,
                           grapes, ...), wine age and food co-occurrence
"""

__version__ = "0.1.0"