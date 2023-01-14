from datetime import datetime, timedelta
from switcharoo.core.history import Switcharoo

def get_input_option(options):
    option = ""
    option_string = "/".join(options)
    options = set(options)
    while option not in options:
        option = input(f"({option_string}):")
    return option

def get_grace_period(roo: Switcharoo):
    # Scale cooldown time with age of roo
    grace_period = 5
    if roo.time < datetime.now() - timedelta(days=360):
        grace_period = 30
    if roo.time < datetime.now() - timedelta(days=180):
        grace_period = 14
    elif roo.time < datetime.now() - timedelta(days=30):
        grace_period = 7
    return grace_period
