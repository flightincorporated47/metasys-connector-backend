scanner:
  site: "CSUDH"
  building: "Central Plant"
  segment_name: "CP-VLAN-XXX"

network:
  # IMPORTANT: set this to the IP of the NIC that is on the BACnet VLAN/subnet
  local_ip: "10.120.0.50"
  bacnet_port: 47808

safety:
  whois_timeout_seconds: 5
  max_devices: 500

output:
  directory: "./out/bacnet"
  filename: "devices.json"

