# Name
zonefile-migrate - Migrate DNS managed zones

# Synopsis
```text
zonefile-migrate to-cloudformation [OPTIONS] [SRC]... DST
zonefile-migrate to-terraform [OPTIONS] [SRC]... DST
```
# Options
```
to-cloudformation
  --sceptre-group DIRECTORY      to write sceptre stack group configuration
  
to-terraform
  --provider PROVIDER            to generate for  
```

# Description
Converts one or more `SRC` zonefiles into AWS CloudFormation or Terraform templates in
`DST`. 

The zonefiles must contain a $ORIGIN and $TTL statement. If the SRC points
to a directory all files which contain one of these statements will be
converted. If a $ORIGIN is missing, the name of the file will be used as the
domain name.

Optionally generates the Sceptre stack config for each of the
templates in the `--sceptre-group` directory.

Each generated CloudFormation template contains a single Route53 HostedZone
and all associated ResourceRecordSet. The SOA and NS records for the origin
domain are not copied into the template.

# Installation
to install the utility, type:

```bash
pip install zonefile-migrate
```

# Example - to-cloudformation
In the source code we have an example, to try it out, type:

```bash
$ git clone   https://gitlab.com/binxio/zonefile-migrate.git
$ cd zonefile-migrate/example
$ zonefile-migrate to-cloudformation --sceptre-group config/dns ./zones ./templates/dns
INFO: reading zonefile zones/asample.org
INFO: reading zonefile zones/land-5.com

```
To deploy all the managed zones to AWS, type:

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

# Example - to-terraform

```bash
$ git clone   https://gitlab.com/binxio/zonefile-migrate.git
$ cd zonefile-migrate/example
$ zonefile-migrate to-terraform --provider google ./zones ./templates/dns
INFO: reading zonefile zones/asample.org
INFO: reading zonefile zones/land-5.com
```

To deploy all the managed zones to Google Cloud Platform, type:

```bash
$ terraform init
$ export GOOGLE_PROJECT=$(gcloud config get-value core/project)
$ terraform apply -auto-approve

````
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
+ create

Terraform will perform the following actions:

# module.asample_org.google_dns_managed_zone.managed_zone will be created
+ resource "google_dns_managed_zone" "managed_zone" {
    + description   = "Managed by Terraform"
    + dns_name      = "asample.org."
    + force_destroy = false
    + id            = (known after apply)
    + name          = "asample-org"
    + name_servers  = (known after apply)
    + project       = (known after apply)
    + visibility    = "public"
      }
...
Plan: 49 to add, 0 to change, 0 to destroy.
module.land-5_com.google_dns_managed_zone.managed_zone: Creating...
module.asample_org.google_dns_managed_zone.managed_zone: Creating...
...
```