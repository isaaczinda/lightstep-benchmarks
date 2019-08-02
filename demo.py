from satellite import SatelliteGroup
from controller import Controller, Command
import logging

logging.basicConfig(level=logging.INFO)

# logging.basicConfig(level=logging.DEBUG)
with SatelliteGroup('typical') as satellites:
    with Controller('python') as c:
        for runtime in [2, 2, 5, 5, 10, 20]:
            result = c.benchmark(
                trace=True,
                satellites=satellites,
                runtime=runtime)
            print(result)
