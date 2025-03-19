```shell
scp ./target/controller-*.jar pi@raspberrypi:/tmp
```

```shell
systemctl restart controller.service
systemctl status controller.service
systemctl stop controller.service
systemctl start controller.service
```

```shell
journalctl -u controller.service -n 50 -f
```