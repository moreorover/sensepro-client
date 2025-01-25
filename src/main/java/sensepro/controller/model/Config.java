package sensepro.controller.model;

import java.util.ArrayList;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class Config {
    @NotBlank
    public String controllerId;
    @NotNull
    public Device controller;
    public ArrayList<Device> devices;
    public ArrayList<Rules> rules;
    public ArrayList<Device> devicesAllowedInRules;
}
