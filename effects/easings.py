def normalize(val, min, max):
    """Normalizes values between 0 and 1 from a min and max value"""
    return (val-min)/(max-min)


def ease(x):
    """Eases normalized values between 0 and 1 using easeOutQuint"""
    return 1 - pow(1 - x, 5)


def generateEasings(value, threshold, iterations):
    """Creates a set of ease values to transition from a high peak
    to the threshold value using an easeOutQuint peak."""

    # Create an empty list to hold values
    _next_vals = []

    # Calculate delta between curent value and threshold
    delta = value-threshold

    # Create an easing transition between the peak and threshold
    for i in range(iterations):
        # Get current value in loop
        val = (delta/iterations)*i

        # Get normalized value
        normVal = normalize(val, 0, delta)

        # Apply ease to value and multiply it by peak
        easeVal = ease(normVal)*value

        # Append ease value to list
        _next_vals.append(easeVal)
    
    return _next_vals