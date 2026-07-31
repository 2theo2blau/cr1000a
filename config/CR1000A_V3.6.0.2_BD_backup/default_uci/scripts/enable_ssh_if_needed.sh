#!/bin/sh

if test -f "/tmp/ssh_is_setup.flag"; then
    exit 0
fi

groupadd -f sshd_user

# Check if user exists
if id "cr1000" >/dev/null 2>&1; then
    :
else
    adduser -s /bin/sh -D -h / -G nogroup cr1000
    echo "cr1000:password" | chpasswd -m
    usermod -G sshd_user cr1000
fi

# Generate SSH keys if needed
if test -f "/etc/ssh/ssh_host_rsa_key"; then
    :
else
    ssh-keygen -N '' -t rsa -f /etc/ssh/ssh_host_rsa_key
fi

if test -f "/etc/ssh/ssh_host_ecdsa_key"; then
    :
else
    ssh-keygen -N '' -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key
fi

if test -f "/etc/ssh/ssh_host_ed25519_key"; then
    :
else
    ssh-keygen -N '' -t ed25519 -f /etc/ssh/ssh_host_ed25519_key
fi

if test -d "/var/empty"; then
    :
else
    mkdir -m 0700 -p /var/empty
fi

/usr/sbin/sshd -p 22 &
/usr/sbin/sshd_delay_close -s restart -t 03:00:00 &

touch /tmp/ssh_is_setup.flag