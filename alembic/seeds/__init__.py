from dataclasses import dataclass

from schemas.schema import BluetoothHardware, FrostDeviceRevisions, SensorHardware

from .bluetooth_hardware import BLUETOOTH_HARDWARE_COMPONENTS
from .hardware_revisions import HARDWARE_REVISIONS
from .sensor_hardware import SENSOR_HARDWARE_COMPONENTS


@dataclass
class RevisionsMapping:
    hardware: SensorHardware
    bluetooth: BluetoothHardware
    revision: FrostDeviceRevisions

    def __hash__(self):
        return self.revision.Name.__hash__()


REVISION_MAPPINGS = {
    RevisionsMapping(
        hardware=next(
            x for x in SENSOR_HARDWARE_COMPONENTS if x.VendorID == "MB7384-1"
        ),
        bluetooth=next(
            x for x in BLUETOOTH_HARDWARE_COMPONENTS if x.VendorID == "FRO-4-0003-R1"
        ),
        revision=next(x for x in HARDWARE_REVISIONS if x.Name == "SDS 1.0"),
    ),
    RevisionsMapping(
        hardware=None,
        bluetooth=next(
            x for x in BLUETOOTH_HARDWARE_COMPONENTS if x.VendorID == "445-002-0301"
        ),
        revision=next(x for x in HARDWARE_REVISIONS if x.Name == "PU 3.0"),
    ),
}
