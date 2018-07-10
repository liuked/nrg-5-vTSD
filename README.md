# NRG-5 vTSD prototype (based on WIFI)

### Introduction

- TSD: TSD is a program running on a Raspberry-Pi device.

- vTSD: vTSD is a program running on the xMEC.

### Guideline to run programs

- TSD

    - Prerequisites
        - `gawk`,`hostapd`, `dnsmasq` should be installed on the device
        - 

    - Command to run TSD
        - modify the configurations which are the json files inside the config/etc/ directory
        - here are examples of configuration, which are easy to understand
        - `device.json` is used to describe the device related information
        
        ```json
        {
            "device_id":"RX78001",
            "credential":"upmc75005"
        }
        ```
        
        - `vTSD.json` is used to describe the vTSD related information

        ```json
        {"port":6666, "url": "nrg5.vtsd.fr", "url_resolv": "manual", "ip":"132.227.122.22"}
        ```
        - run TSD

        ```
        cd config
        ./setup.sh
        cd ../ && cd TSD
        ./TSD
        ```

- vTSD

```
```
