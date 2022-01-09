import logging
from bleak import BleakScanner


async def auto_search():
    logging.basicConfig(level=logging.INFO, format='%(relativeCreated)d\t%(levelname)s\t%(name)s\t%(message)s')
    logging.info("Searching for Lego Hub...")
    devices = await BleakScanner.discover(timeout=10)
    possible_devices = []
    for d in devices:
        if d.name == "Move Hub":
            possible_devices.append(d)

    if len(str(possible_devices[1].metadata)) > len(str(possible_devices[0].metadata)):
        return possible_devices[1].name, possible_devices[1].address
    else:
        return possible_devices[0].name, possible_devices[0].address
