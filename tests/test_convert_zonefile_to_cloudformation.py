import unittest
import tempfile
import os
from aws_route53_migrate.zone_to_cfn import convert_to_cloudformation
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


class ConvertToCloudFormationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        filename = tempfile.NamedTemporaryFile()
        with open(filename.name, "w") as file:
            file.write(zonefile)
            file.flush()
            self.zone = easyzone.zone_from_file("asample.org", filename.name)

    def test_something(self):
        template = convert_to_cloudformation(self.zone)
        self.assertEqual("2010-09-09", template.get("AWSTemplateFormatVersion"))
        resources = template.get("Resources", {})
        self.assertTrue(resources, "Resources section exists")
        hostedzone = resources.get("HostedZone")
        self.assertTrue(hostedzone, "HostedZone resource is missing")
        self.assertEqual("asample.org.", hostedzone.get("Properties", {}).get("Name"))
        nr_of_records = 0
        expected_nr_of_records = 14
        for resource_id, resource in resources.items():
            if resource["Type"] == "AWS::Route53::HostedZone":
                continue

            nr_of_records += 1

            self.assertEqual(
                "AWS::Route53::RecordSet",
                resource["Type"],
                f"unexpected type for {resource_id}",
            )
            properties = resource["Properties"]
            recname = properties["Name"]
            rectype = properties["Type"]
            ttl = properties["TTL"]
            name = self.zone.names.get(recname)
            self.assertTrue(name, f"{recname} not found in zone")
            records = name.records(rectype)
            self.assertTrue(
                records, f"no records found of type {rectype} for {recname} in zone"
            )
            expected_resource_records = list(
                map(
                    lambda i: " ".join(map(lambda j: str(j), i))
                    if isinstance(i, tuple)
                    else i,
                    records.items,
                )
            )
            self.assertEqual(expected_resource_records, properties["ResourceRecords"])
        self.assertEqual(expected_nr_of_records, nr_of_records)


if __name__ == "__main__":
    unittest.main()
