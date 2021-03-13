import argparse

check_up = argparse.ArgumentParser(description='Reddit bot for reversing gifs')

check_up.add_argument('--starting-roo', '-s', action='store', default=False, help='ID of Roo to start on')
check_up.add_argument('--limit', '-l', action="store", default=False, help="how many roos to check from start")
