import argparse

check_up = argparse.ArgumentParser(description='Check the status of each link in chain and send requests to fix breaks')

check_up.add_argument('--starting-roo', '-s', action='store', default=False, help='ID of Roo to start on')
check_up.add_argument('--limit', '-l', action="store", default=False, help="how many roos to check from start")

tracer = argparse.ArgumentParser(description="Trace the switcharoo link chain by comment")
tracer.add_argument("--discover", '-d', action='store_true')

