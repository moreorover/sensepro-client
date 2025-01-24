package sensepro.controller.model;

import java.util.ArrayList;

public class Config {
    public String controllerId;
    public Device controller;
    public ArrayList<Device> devices;
    public ArrayList<Rules> rules;
    public ArrayList<Device> devicesAllowedInRules;
}
