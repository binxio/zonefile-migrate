import logging
from easyzone import easyzone
from dns.rdatatype import _by_text as DNSRecordTypes


class DNSRecordSet:
    """
    a simple DNS record set representation
    """

    def __init__(self, name: str, rectype: str, ttl: int, rrdatas: list[str]):
        self.name = name
        self.rectype = rectype
        self.ttl = ttl
        self.rrdatas = rrdatas

    @staticmethod
    def create_from_easyzone(
        name: easyzone.Name, records: easyzone.Records
    ) -> "DNSRecordSet":
        """
        create a simple DNS record from an easyzone record.
        """
        rrdatas = records.items
        if len(rrdatas) > 0 and isinstance(rrdatas[0], (tuple, list)):
            rrdatas = list(map(lambda r: " ".join(map(lambda v: str(v), r)), rrdatas))

        return DNSRecordSet(name.name, records.type, name.ttl, rrdatas)


def create_from_zone(zone: easyzone.Zone) -> [DNSRecordSet]:
    result: [DNSRecordSet] = []
    for key, name in zone.names.items():
        for rectype in DNSRecordTypes.keys():
            records = name.records(rectype)
            if not records:
                continue

            result.append(DNSRecordSet.create_from_easyzone(name, records))

    return result
