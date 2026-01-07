from schemas.schema import FrostDeviceRevisions

# Request	                            Items to Ship				                        Packaging
# RWIS 1.6	                            RWIS 1.6	opt - Laser			                    1.6 box or 16x12x8 box
# RWIS 3.0	                            RWIS 3.0	opt - Laser	opt - Adapter A		        16x12x8 box
# WeatherStation 3.0	                RWIS 3.0	PU 3.0	Charging Cable	opt - Laser	    Frost custom packaging (on hand)
# FVC 1.0 	                            FVC 1.0				                                16x12x8 box
# FVC 2.0                               FVC 2.0	opt - Adapter A	                        	16x12x8 box
# VisionStation 2.0	                    FVC 2.0	PU 3.0	Charging Cable	                    Frost custom packaging (on hand)
# FVC 2.0-IL                            FVC 2.0-IL	opt - Adapter A	                    	16x12x8 box
# VisionStation 2.0-IL                  FVC 2.0-IL	PU 3.0	Charging Cable              	Frost custom packaging (on hand)
# PU 3.0                                PU 3.0	Charging Cable	opt - Adapter B		        Frost custom packaging (on hand)


# We'll have RWIS 3 to flash and FVC 2.0 to flash it looks like. When they're paired with a PU (power unit) they come a WeatherStation 3.0 and VisionStation 3.0 respectively
# So on the app, I think we need 2 new HW dropdowns for RWIS 3.0 and FVC 2.0.
# I think those also send some data to Particle's ledger depending on what's chosen


HARDWARE_REVISIONS = [
    FrostDeviceRevisions(Name="RWIS 1.0"),
    FrostDeviceRevisions(Name="RWIS 1.1"),
    FrostDeviceRevisions(Name="RWIS 1.2"),
    FrostDeviceRevisions(Name="RWIS 1.3"),
    FrostDeviceRevisions(Name="RWIS 1.4"),
    FrostDeviceRevisions(Name="RWIS 1.5"),
    FrostDeviceRevisions(Name="RWIS 1.6"),
    FrostDeviceRevisions(Name="RWIS 2.0"),
    FrostDeviceRevisions(Name="RWIS 2.1"),
    FrostDeviceRevisions(Name="FVC 1.0"),
    FrostDeviceRevisions(Name="FVC 1.0-I"),
    FrostDeviceRevisions(Name="FVC 1.1"),
    FrostDeviceRevisions(Name="FVC 1.1-I"),
    FrostDeviceRevisions(Name="SDS 1.0"),
    FrostDeviceRevisions(Name="RWIS 3.0"),
    FrostDeviceRevisions(Name="FVC 2.0"),
    FrostDeviceRevisions(Name="FVC 2.0-IL"),
    FrostDeviceRevisions(Name="PU 3.0"),
]
