import numpy as np

### Calculus function for all python file ###

def sigma(values: list) -> float:
    if len(values) == 0:
        return 0.0

    return float(np.std(values))
