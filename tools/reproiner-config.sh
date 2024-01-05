#!/bin/bash
#
# A rudimentary (and potentially still incomplete) script to configure reproiner.
# reproiner is a small box which is attached to magewell screen grabbers, our custom
# micropython events capturer attached to curdes (birch), and also network (usb ethernet) attached
# to the same birch to be able to harvest events on it directly and also to provide it
# with ntp and internet.
# 
# For reuse, it needs to be parametrized since now it has dartmouth and hardware specific
# (e.g. MAC) addresses here and there.
# And may be potentially converted to ansible playbook.
#
set -eu

# helper tools installed
apt install -y net-tools ncdu 
# tools which will be used by our tools
apt install -y git-annex

if ! id reprostim > /dev/null; then
	# might add --disabled-password here
	adduser reprostim
	for g in dialout audio dip video plugdev ; do
		adduser reprostim $g || echo "failed adding to $g"
	done
fi

#
# Connecting to Birch.  It needs us to provide it with dhcp server.
#
# configured usb dongle network
birchif=enx8cae4cdd98c0
# Installed/configured DHCP server for birch to get an address

apt install -y isc-dhcp-server
c=/etc/dhcp/dhcpd.conf

if ! grep birch "$c"; then
	ns=$(awk '/^nameserver/{print $2}' /etc/resolv.conf | head -n 1)
	cat >| $c <<EOF
option domain-name "centerforopenneuroscience.org";
option domain-name-servers $ns, 8.8.8.8;

default-lease-time 600;
max-lease-time 7200;

subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.110 192.168.1.120;
}
  
host birch {
	hardware ethernet b8:27:eb:d0:3f:77;
	fixed-address 192.168.1.10;
	option subnet-mask 255.255.255.0;
	option routers 192.168.1.2;
}
  
ddns-update-style none;
EOF

	service isc-dhcp-server restart
fi

if ! grep "$birchif" /etc/default/isc-dhcp-server; then
	sed -i -e "s,INTERFACESv4=.*,INTERFACESv4=\"$birchif\",g" /etc/default/isc-dhcp-server
	service isc-dhcp-server restart
fi

  

# ntp server
apt install -y ntpsec

s=ntp.dartmouth.edu 

c=/etc/ntpsec/ntp.conf
if ! grep "$s" "$c"; then
	sed -i -e "s,^\(# server .*nts\$\),\1\nserver $s,g" "$c"
fi
