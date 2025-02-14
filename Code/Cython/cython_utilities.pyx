cimport cython

ctypedef fused number:
    int
    double

cpdef number process_value(number x):
    return x * 2


cpdef number move_number_to_desired_range2(number low, number value, number high):
    if value < low:
        return low
    elif value > high:
        return high
    else:
        return value


cpdef list bresenham(number x1, number y1, number x2, number y2):
    points = []
    dx = x2 - x1
    dy = y2 - y1
    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1
    dx = abs(dx)
    dy = abs(dy)
    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0
    D = 2*dy - dx
    y = 0
    for x in range(dx + 1):
        points.append((x1 + x*xx + y*yx, y1 + x*xy + y*yy))
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy
    return points