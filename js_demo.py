from satellite import SatelliteGroup
from controller import Controller, Command
import logging

logging.basicConfig(level=logging.INFO)

# logging.basicConfig(level=logging.DEBUG)
with SatelliteGroup('typical') as satellites:
    with Controller('js') as c:
        result = c.benchmark(
            trace=True,
            satellites=satellites,
            runtime=5)

        print(result)
