"""Logic to suggest food pairings for wines."""

import ast
from collections import Counter


def suggest_food(wines, wine_type, wine_body, n):
    """Suggest the foods most often paired with similar wines.

    Looks at the wines with the same type and body; if there are none,
    it falls back to the wines with the same type.

    Args:
        wines (pd.DataFrame): Wine table with Type, Body and Harmonize columns.
        wine_type (str): Wine type, e.g. "Red".
        wine_body (str): Wine body, e.g. "Full-bodied".
        n (int): Number of foods to return.

    Returns:
        tuple[list[str], Counter]: The n most common foods, and the count
        of every food found.
    """
    wines = wines[wines["Harmonize"] != "N/A"]
    match = wines[(wines["Type"] == wine_type) & (wines["Body"] == wine_body)]
    if match.empty:
        match = wines[wines["Type"] == wine_type]
    all_pairings = match["Harmonize"].apply(ast.literal_eval).explode().tolist()
    food_count = Counter(all_pairings)
    top_foods = [food for food, _ in food_count.most_common(n)]
    return top_foods, food_count