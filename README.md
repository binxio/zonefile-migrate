# Name
zonefile-migrate - Migrate Route53 managed zones

# Synopsis
```text
zonefile-migrate zone-to-cfn [OPTIONS] [SRC]... DST
```
# Options
```
  --sceptre-group DIRECTORY      to write sceptre stack group configuration
  --help                         Show this message and exit.
```

# Description
Converts one or more `SRC` zonefiles into AWS CloudFormation templates in
`DST`. Optionally generates the Sceptre stack config for each of the
templates in the `--sceptre-group` directoru.

Each generated CloudFormation template contains a single Route53 HostedZone
and all associated ResourceRecordSet. The SOA and NS records for the origin
domain are not copied into the template.

The zonefiles must contain a $ORIGIN and $TTL statement. If the SRC points
to a directory all files which contain one of these statements will be
converted. If a $ORIGIN is missing, the name of the file will be used as the
domain name.

# Installation
to install the utility, type:

```bash
pip install zonefile-migrate
```

# Example
In the source code we have an example, to try it out, type:

```bash
$ git clone   https://gitlab.com/binxio/zonefile-migrate.git
$ cd zonefile-migrate/example
$ zonefile-migrate zone-to-cfn --sceptre-group config/dns ./zones ./templates/dns
INFO: reading zonefile zones/asample.org
WARNING: ignoring NS records for origin asample.org.
WARNING: ignoring SOA records for origin asample.org.
INFO: reading zonefile zones/land-5.com
WARNING: ignoring NS records for origin land-5.com.
WARNING: ignoring SOA records for origin land-5.com.
```
To deploy all the managed zones, type:

```bash
$ sceptre --var aws_profile=$AWS_PROFILE launch -y dns
[2022-05-14 14:58:23] - dns/zone-land-5-com - Launching Stack
[2022-05-14 14:58:23] - dns/zone-example-org - Launching Stack
[2022-05-14 14:58:23] - dns/zone-land-5-com - Stack is in the PENDING state
[2022-05-14 14:58:23] - dns/zone-land-5-com - Creating Stack
[2022-05-14 14:58:23] - dns/zone-asample-org - Stack is in the PENDING state
[2022-05-14 14:58:23] - dns/zone-asample-org - Creating Stack
[2022-05-14 14:58:24] - dns/zone-asample-org binxio-dns-zone-asample-org AWS::CloudFormation::Stack CREATE_IN_PROGRESS User Initiated
[2022-05-14 14:58:24] - dns/zone-land-5-com binxio-dns-zone-land-5-com AWS::CloudFormation::Stack CREATE_IN_PROGRESS User Initiated
...
```
