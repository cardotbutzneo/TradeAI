import numpy as np

### Calculus function for all python file ###

def sigma(values: list) -> float:
    if len(values) == 0:
        return 0.0

    return float(np.std(values))

def error(actual : any, predicted : any) -> float : 
    """Return the effective error of two value"""
    return np.mean(np.abs(actual - predicted))

def linear_optimisation(data_points: np.array) -> tuple:
    """
    Find the straight line that minimizes the spacing (distance) 
    between itself and the scatter points.
    
    Parameters:
    - data_points : An array of shape (N, 2) containing (x, y) coordinates.
    
    Returns:
    - slope (m) and intercept (b) of the optimized line: y = mx + b
    """
    # Separate the x and y coordinates from your scatter points
    x = data_points[:, 0]
    y = data_points[:, 1]
    
    # np.polyfit(x, y, 1) finds the slope and intercept 
    # that mathematically minimizes the squared "spacing" to all points.
    # The '1' means a polynomial of degree 1 (a straight line).
    slope, intercept = np.polyfit(x, y, 1)
    
    return slope, intercept
