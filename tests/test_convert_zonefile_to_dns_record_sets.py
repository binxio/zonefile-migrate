import unittest
import tempfile
import os
from zonefile_migrate.dns_record_set import create_from_zone
from easyzone import easyzone


zonefile = """
$ORIGIN asample.org.
$TTL 86400
@	SOA	dns1.asample.org.	hostmaster.asample.org. (
            2001062501 ; serial
            21600      ; refresh after 6 hours
            3600       ; retry after 1 hour
            604800     ; expire after 1 week
            86400 )    ; minimum TTL of 1 day
    ;
;
	NS	dns1.asample.org.
	NS	dns2.asample.org.
dns1	A	10.0.1.1
	AAAA	aaaa:bbbb::1
dns2	A	10.0.1.2
	AAAA	aaaa:bbbb::2
;
;
@	MX	10	mail.asample.org.
	MX	20	mail2.asample.org.
mail	A	10.0.1.5
	AAAA	aaaa:bbbb::5
mail2	A	10.0.1.6
	AAAA	aaaa:bbbb::6
;
;
; This sample zone file illustrates sharing the same IP addresses for multiple services:
;
services	60 A	10.0.1.10
		AAAA	aaaa:bbbb::10
		A	10.0.1.11
		AAAA	aaaa:bbbb::11

ftp	CNAME	services.asample.org.
www	CNAME	services.asample.org.
@   TXT     "txt=beautiful"
;
;
"""


class ConvertToDNSRecordSetTestCase(unittest.TestCase):
    def setUp(self) -> None:
        filename = tempfile.NamedTemporaryFile()
        with open(filename.name, "w") as file:
            file.write(zonefile)
            file.flush()
            self.zone = easyzone.zone_from_file("asample.org", filename.name)

    def test_create_from_zone(self):
        record_sets = create_from_zone(self.zone)
        self.assertEqual(16, len(record_sets))
        for record_set in record_sets:
            name = self.zone.names.get(record_set.name)
            self.assertTrue(name, f"{record_set.name} not found in zone")

            self.assertEqual(name.ttl, record_set.ttl)
            records = name.records(record_set.rectype)
            self.assertTrue(
                records,
                f"no records found of type {record_set.rectype} for {record_set.name} in zone",
            )
            expected_resource_records = list(
                map(
                    lambda i: " ".join(map(lambda j: str(j), i))
                    if isinstance(i, (list, tuple))
                    else i,
                    records.items,
                )
            )
            self.assertEqual(expected_resource_records, record_set.rrdatas)


if __name__ == "__main__":
    unittest.main()
