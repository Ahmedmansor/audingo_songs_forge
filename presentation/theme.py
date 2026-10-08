"""Semantic colors shared by custom cards and legacy inline presentation."""

LIGHT = {
    "bg": "#F5F5F7", "surface": "#FFFFFF", "ink": "#1D1D1F",
    "muted": "#6E6E73", "line": "#D2D2D7", "blue": "#0066CC",
    "tint": "#EAF3FF", "green": "#216E39", "amber": "#855600",
    "red": "#B42318", "purple": "#7352A2", "teal": "#006B80",
    "pink": "#AF3150", "green-bg": "#EAF5EE", "amber-bg": "#FFF4DC",
    "red-bg": "#FFF0EE", "neutral-bg": "#ECECEE", "neutral-ink": "#515154",
    "track": "#E8E8ED", "sidebar": "#FBFBFD", "mark": "#1D1D1F",
}
DARK = {
    "bg": "#161617", "surface": "#232325", "ink": "#F5F5F7",
    "muted": "#B1B1B7", "line": "#454549", "blue": "#78B7FF",
    "tint": "#20354D", "green": "#8BD5A2", "amber": "#F0C779",
    "red": "#FFABA5", "purple": "#C4B0ED", "teal": "#8BD5DF",
    "pink": "#F2A8BC", "green-bg": "#233C2C", "amber-bg": "#423621",
    "red-bg": "#442A29", "neutral-bg": "#303033", "neutral-ink": "#D1D1D6",
    "track": "#3D3D42", "sidebar": "#1C1C1E", "mark": "#343437",
}


def palette(mode):
    return DARK if mode == "dark" else LIGHT
