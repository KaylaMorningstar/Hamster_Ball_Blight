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
