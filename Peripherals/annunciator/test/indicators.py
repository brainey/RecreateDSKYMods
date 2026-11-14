

DEEP_ORANGE = (255, 80, 0)
WHITE = (255, 255, 255)
DARK_RED = (139, 0, 0)
INDICATOR_GREEN = (0, 200, 0)
LOW_GLARE_GREEN = (0, 50, 0)

NOTICE = (50, 50, 50)
CAUTION = (60, 22, 0)
WARNING = (50, 0, 0)
OFF = (0, 0, 0)
ON = (50, 50, 50)
GO = (0, 50, 0)



# Mapping of indicators to pixel pairs for the display
indicators=[
    (16, 17),    # 0
    (18, 19),    # 1
    (14, 15),    # 2
    (20, 21),    # 3
    (12, 13),    # 4
    (22, 23),    # 5
    (10, 11),    # 6
    (24, 25),    # 7
    (8, 9),      # 8
    (26, 27),    # 9
    (6, 7),      # 10
    (0, 1),      # 11
    (4, 5),      # 12
    (2, 3)       # 13
    ]
 
# Raw mapping of indicators to pixel pairs
# indicators=[
#     (0, 1),     # 0
#     (2, 3),     # 1
#     (4, 5),     # 2
#     (6, 7),     # 3
#     (8, 9),     # 4
#     (10, 11),   # 5
#     (12, 13),   # 6
#     (14, 15),   # 7
#     (16, 17),   # 8
#     (18, 19),   # 9
#     (20, 21),   # 10
#     (22, 23),   # 11
#     (24, 25),   # 12
#     (26, 27)    # 13
#     ]

labels = [
    "uplink_acty",  # 0
    "temp",         # 1
    "noatt",        # 2
    "gim_lock",     # 3
    "stby",         # 4
    "prog",         # 5
    "key_rel",      # 6
    "rstrt",        # 7
    "opr_err",      # 8
    "trkr",         # 9
    "prio_disp",    # 10
    "alt",          # 11
    "no_dap",       # 12
    "vel"           # 13
    ]

def set_indicator(indicator_index, value):
    if 0 <= indicator_index < len(indicators):
        pixel_list = indicators[indicator_index]
        # Tuple is a list of pixel indexes
        for pixel_index in pixel_list:
            pixels[pixel_index] = value
        pixels.show()
    else:
        raise IndexError("Indicator index out of range.")
