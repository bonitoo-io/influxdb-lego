import logging
from bleak import BleakScanner
from pylgbst.comms import MOVE_HUB_HW_UUID_SERV


async def auto_search():
    logging.basicConfig(level=logging.INFO, format='%(relativeCreated)d\t%(levelname)s\t%(name)s\t%(message)s')
    logging.info("Discovering devices... Press the green button on Hub")
    devices = await BleakScanner.discover(timeout=5, service_uuids=[MOVE_HUB_HW_UUID_SERV])
    if devices is None or len(devices) == 0:
        logging.error("Hub not found.")
        exit(1)
    else:
        return devices[0].name, devices[0].address
