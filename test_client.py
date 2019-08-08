import matplotlib.pyplot as plt
import numpy as np
import pytest
from benchmark.controller import Controller, Command, Result
from benchmark.satellite import MockSatelliteGroup as SatelliteGroup


@pytest.fixture(scope='module')
def satellites():
    with SatelliteGroup('typical') as satellites:
        yield satellites

def test_memory(client_name, satellites):
    """ Tracers should not have memory leaks """

    with Controller(client_name) as controller:
        result_100s = controller.benchmark(
            trace=True,
            spans_per_second=500,
            runtime=100,
            satellites=satellites)

        result_5s = controller.benchmark(
            trace=True,
            spans_per_second=500,
            runtime=5,
            satellites=satellites)

    # 100s memory < 1.5x 5s memory
    assert(result_100s.memory / result_5s.memory < 1.5)


def test_dropped_spans(client_name, satellites):
    """ No tracer should drop spans if we're only sending 300 / s. """

    with Controller(client_name) as controller:
        sps_100 = controller.benchmark(
            trace=True,
            spans_per_second=100,
            runtime=10,
            satellites=satellites)

        sps_300 = controller.benchmark(
            trace=True,
            spans_per_second=300,
            runtime=10,
            satellites=satellites)

    assert(sps_100.dropped_spans == 0)
    assert(sps_300.dropped_spans == 0)


def test_cpu(client_name, satellites):
    """ Traced ciode shouldn't consume significatly more CPU than untraced
    code """

    TRIALS = 5
    cpu_traced = []
    cpu_untraced = []
    with Controller(client_name) as controller:
        for i in range(TRIALS):
            result_untraced = controller.benchmark(
                trace=False,
                spans_per_second=500,
                runtime=10)
            cpu_untraced.append(result_untraced.cpu_usage * 100)

            result_traced = controller.benchmark(
                trace=True,
                spans_per_second=500,
                runtime=10,
                satellites=satellites)
            cpu_traced.append(result_traced.cpu_usage * 100)

    assert(abs(np.mean(cpu_traced) - np.mean(cpu_untraced)) < 10)