package sensepro.controller.model;

import java.util.Date;

public class Device {
    public String id;
    public String name;
    public String mac;
    public String ip;
    public Object tailscaleIp;
    public String serialNumber;
    public int pin;
    public Date createdAt;
    public Date updatedAt;
    public String locationId;
    public String deviceTypeId;
    public String controllerId;
}
