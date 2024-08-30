#!/bin/sh

invid="$(systemctl show --value -p InvocationID fl-controller.service)"

journalctl -u fl-controller.service _SYSTEMD_INVOCATION_ID=$invid

exit 0
