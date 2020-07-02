# PyONE CLI

**Development! Alpha version**

Python CLI for Open Nebula.

## vmpool.info
https://docs.opennebula.org/5.6/integration/system_interfaces/api.html#one-vmpool-info

## vm.info
https://docs.opennebula.org/5.6/integration/system_interfaces/api.html#one-vm-info

## VM state
The state filter can be one of the following:

| Value | State |
|---|---|
| -2 | Any state, including DONE |
| -1 | Any state, except DONE |
| 0 | INIT |
| 1 | PENDING |
| 2 | HOLD |
| 3 | ACTIVE |
| 4 | STOPPED |
| 5 | SUSPENDED |
| 6 | DONE |
| 8 | POWEROFF |
| 9 | UNDEPLOYED |
| 10 | CLONING |
| 11 | CLONING_FAILURE |

## one.vm.action
https://docs.opennebula.org/5.6/integration/system_interfaces/api.html#one-vm-action

## VM actions
The action String must be one of the following:

- terminate-hard
- terminate
- undeploy-hard
- undeploy
- poweroff-hard
- poweroff
- reboot-hard
- reboot
- hold
- release
- stop
- suspend
- resume
- resched
- unresched

## Bibliografia

https://docs.opennebula.org/5.6/integration/system_interfaces/api.html

http://docs.opennebula.org/5.8/integration/system_interfaces/python.html