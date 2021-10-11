def bassFilter(sample):
    """20 - 200hz Single Pole Bandpass IIR Filter"""

    xv = [0, 0, 0]
    yv = [0, 0, 0]

    xv[0] = xv[1]
    xv[1] = xv[2]

    xv[2] = sample / 9.1

    yv[0] = yv[1]
    yv[1] = yv[2]
    
    yv[2] = (xv[2] - xv[0]) + (-0.7960060012 * yv[0]) + (1.7903124146 * yv[1])

    return yv[2]


def envelopeFilter(sample):
    """10hz Single Pole Lowpass IIR Filter"""

    xv = [0, 0]
    yv = [0, 0]

    xv[0] = xv[1]
    xv[1] = sample / 160
    yv[0] = yv[1]

    yv[1] = (xv[0] + xv[1]) + (0.9875119299 * yv[0])

    return yv[1]


def beatFilter(sample):
    """1.7 - 3.0hz Single Pole Bandpass IIR Filter"""

    xv = [0, 0, 0]
    yv = [0, 0, 0]

    xv[0] = xv[1] 
    xv[1] = xv[2]
    xv[2] = sample / 7.015
    yv[0] = yv[1]; yv[1] = yv[2]
    yv[2] = (xv[2] - xv[0]) + (-0.7169861741 * yv[0]) + (1.4453653501 * yv[1])

    return yv[2]