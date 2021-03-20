import argparse

check_up = argparse.ArgumentParser(description='Check the status of each link in chain and send requests to fix breaks')

check_up.add_argument('--starting-roo', '-s', action='store', default=False, help='ID of Roo to start on or last')
check_up.add_argument('--limit', '-l', action="store", default=False, help="how many roos to check from start")
check_up.add_argument('--no-delete-check', '-d', action="store_true", help="Disable the delete check")
check_up.add_argument('--no-relink', '-r', action="store_true", help="Disable asking for relinking")
check_up.add_argument('--double-check-link', '-c', action="store_true", help="Enable double checking a comment is linked in the DB properly")



tracer = argparse.ArgumentParser(description="Trace the switcharoo link chain by comment")
tracer.add_argument("--discover", '-d', action='store_true')
