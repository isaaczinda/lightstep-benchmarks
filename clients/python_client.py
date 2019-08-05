import psutil
import numpy as np
import time
import opentracing
import json
import sys
import requests
import argparse
import time

MEMORY_PERIOD = 1 # report memory use every 5 seconds
CONTROLLER_PORT = 8023
NUM_SATELLITES = 8

def work(units):
    i = 1.12563
    for i in range(0, units):
        i *= i

def send_done():
    r = requests.get(f'http://localhost:{CONTROLLER_PORT}/result')


""" Mode is either vanilla or cpp_bindings. """
def perform_work(command, tracer_name, port):
    print("performing work:", command)

    # if exit is set to true, end the program
    if command['Exit']:
        send_done()
        sys.exit()

    if command['Trace'] and tracer_name == "vanilla":
        import lightstep
        tracer = lightstep.Tracer(
            component_name='isaac_service',
            collector_port=port,
            collector_host='localhost',
            collector_encryption='none',
            use_http=True,
            access_token='developer'
        )
    elif command['Trace'] and tracer_name == "cpp":
        import lightstep_native
        tracer = lightstep_native.Tracer(
            component_name='isaac_service',
            access_token='developer',
            use_stream_recorder=True,
            collector_plaintext=True,
            satellite_endpoints=[{'host':'localhost', 'port':p} for p in range(port, port + NUM_SATELLITES)],
        )
    else:
        tracer = opentracing.Tracer()


    sleep_debt = 0

    for i in range(command['Repeat']): # time.time() < start_time + command['TestTime']:
        with tracer.start_active_span('TestSpan') as scope:
            work(command['Work'])

        sleep_debt += command['Sleep']

        if sleep_debt > command['SleepInterval']:
            sleep_debt -= command['SleepInterval']
            time.sleep(command['SleepInterval'] * 10**-9) # because there are 10^-9 nanoseconds / second

    # don't include flush in time measurement
    if command['Trace'] and not command['NoFlush']:
        tracer.flush()

    send_done()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a client to test a LightStep tracer.')
    parser.add_argument('port', type=int, help='Which port to connect to the satellite on.')
    parser.add_argument('tracer', type=str, choices=["vanilla", "cpp"], help='Which LightStep tracer to use.')
    args = parser.parse_args()

    while True:
        r = requests.get(f'http://localhost:{CONTROLLER_PORT}/control')
        perform_work(r.json(), args.tracer, args.port)
