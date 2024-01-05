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

topd=$(readlink -f "$0" | xargs dirname | xargs dirname)

# default network interface
net_if=$(ip route | awk '/^default/{print $5}')
# configured usb dongle network
birch_if=enx8cae4cdd98c0
udev_rules="$topd/Capture/etc/udev/189-reprostim.rules"




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
## Magewell devices "support" for audio/video capture
#
udev_rules_file=$(basename "$udev_rules")
c=/etc/udev/rules.d/"$udev_rules_file"
[ -e "$c" ] || {
	cp "$udev_rules" "$c"
	udevadm control --reload
	# But above is not sufficient if device already connected
	if lsusb | grep -q "ID 2935"; then
		echo "Need to reboot computer for udevd changes to take effect for already attached devices!"
	fi
}

#
# Connecting to Birch.  It needs us to provide it with dhcp server.
#
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

if ! grep -q "$birch_if" /etc/default/isc-dhcp-server; then
	sed -i -e "s,INTERFACESv4=.*,INTERFACESv4=\"$birch_if\",g" /etc/default/isc-dhcp-server
	service isc-dhcp-server restart
fi

# simple way to define custom firewall so we could setup masquarading for birch
apt install -y iptables-persistent
c=/etc/iptables/rules.v4

if ! grep -q "NAT for birch" "$c"; then

	cat >| "$c" << EOF
# Created following a basic tutorial
# https://gridscale.io/en/community/tutorials/debian-router-gateway/
# to establish NAT for birch

*nat
-A POSTROUTING -o $net_if -j MASQUERADE
COMMIT

*filter
-A INPUT -i lo -j ACCEPT
# allow ssh, so that we do not lock ourselves
-A INPUT -i $net_if -p tcp -m tcp --dport 22 -j ACCEPT
# allow ntp
-A INPUT -i $net_if -p udp -m udp --dport 123 -j ACCEPT

# allow incoming traffic to the outgoing connections,
# et al for clients from the private network
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
# prohibit everything else incoming
-A INPUT -i $net_if -j DROP

COMMIT
EOF

	service iptables restart
fi

c=/etc/sysctl.conf
if [ "$(sysctl net.ipv4.ip_forward)" == "net.ipv4.ip_forward = 0" ]; then
	echo "net.ipv4.ip_forward=1" >> "$c"
	sysctl -p
	test "$(sysctl net.ipv4.ip_forward)" = "net.ipv4.ip_forward = 1"
fi

# ntp server
apt install -y ntpsec

s=ntp.dartmouth.edu 

c=/etc/ntpsec/ntp.conf
if ! grep "$s" "$c"; then
	sed -i -e "s,^\(# server .*nts\$\),\1\nserver $s,g" "$c"
fi
