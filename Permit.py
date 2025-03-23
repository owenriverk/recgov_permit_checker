from dataclasses import dataclass

@dataclass
class Section:
    permit: int
    value: int
    putin: str
    takeout: str
    river: str
    sectionname: str
    startdt: str
    enddt: str

class Permit:
    sections =[
        Section(
            permit=250014,
            value=371,
            putin='Deerlodge Park',
            takeout='Split Mountain',
            river='Yampa',
            sectionname='Yampa',
            startdt='2025-07-01T00:00:00.000Z',
            enddt='2025-07-31T00:00:00.000Z'
        ),
        Section(
            permit=250014,
            value=380,
            putin='Ladore',
            takeout='Split Mountain',
            river='Green',
            sectionname='Gates of Ladore',
            startdt='2025-07-01T00:00:00.000Z',
            enddt='2025-07-31T00:00:00.000Z'
        ),
        Section(
            permit=234623,
            value=377,
            putin='Boundary Creek',
            takeout='Cache Bar',
            river='Salmon',
            sectionname='Middle Fork Salmon',
            startdt='2025-07-01T00:00:00.000Z',
            enddt='2025-07-31T00:00:00.000Z'
        ),
        Section(
            permit=234622,
            value=376,
            putin='Corn Creek',
            takeout='Vinegar Creek',
            river='Salmon',
            sectionname='Main Salmon',
            startdt='2025-07-01T00:00:00.000Z',
            enddt='2025-07-31T00:00:00.000Z'
        )
    ]