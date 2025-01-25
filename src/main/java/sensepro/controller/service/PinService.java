package sensepro.controller.service;

import sensepro.controller.model.Config;

public interface PinService {
    void configure(Config config);
    void configurePin(int pin);
    void clearPin(int pin);
    void clearAllPins();
}
