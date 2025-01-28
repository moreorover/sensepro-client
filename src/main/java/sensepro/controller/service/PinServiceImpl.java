package sensepro.controller.service;

import com.pi4j.io.gpio.digital.*;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import sensepro.controller.model.Config;
import sensepro.controller.model.Device;
import sensepro.controller.mq.MessagePublisher;
import com.pi4j.Pi4J;
import com.pi4j.context.Context;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Slf4j
@Component
public class PinServiceImpl implements PinService {

    private final MessagePublisher messagePublisher;
    private Context pi4j;
    private final FileService<Config> fileService;
    @Getter
    private final Map<Integer, DigitalInput> pinMap;
    @Getter
    private final Map<DigitalInput, DigitalStateChangeListener> listenerMap;

    public PinServiceImpl(MessagePublisher messagePublisher, FileService<Config> fileService) {
        this.messagePublisher = messagePublisher;
        this.pi4j = Pi4J.newAutoContext();
        this.fileService = fileService;
        this.pinMap = new HashMap<>();
        this.listenerMap = new HashMap<>();
    }

    @PostConstruct
    public void initialize() {
        log.info("Initializing Pins...");
        Config config;
        try {
            config = fileService.readFile("config.json", Config.class);
            log.info("Successfully read config.json");
        } catch (FileServiceException e) {
            log.error(e.getMessage());
            config = null;
        }

        if (config == null) {
            log.warn("No config.json found. Waiting for initial configuration from MQ Server...");
            messagePublisher.sendMessage("server-notifications", "No config.json found.");
            return;
        }

        configure(config);
    }

    public void configure(Config config) {
        clearAllPins();
        if (config.devices.isEmpty()) {
            log.warn("No devices found. Waiting for initial configuration from MQ Server...");
            return;
        }

//        pi4j.registry().all().forEach((id, io) -> log.info("Registered IO: {}", id));

        for (Device device : config.devices) {
            if (device.pin != null ) {
                configurePin(device.pin);
            }
        }
    }

    public void configurePin(int pin) {
        var buttonConfig = DigitalInput.newConfigBuilder(pi4j)
                .id("button-" + pin)
                .name("Button on pin " + pin)
                .address(pin)
                .pull(PullResistance.PULL_DOWN)
                .debounce(5000L)
                .provider("gpiod-digital-input");
        var button = pi4j.din().create(buttonConfig);
        DigitalStateChangeListener listener = e -> {
            log.info("Pin {} state changed to {}", pin, e.state());
            if (e.state() == DigitalState.LOW) {
//                messagePublisher.sendMessage("Button on pin " + pin + " was pressed");
                log.info("Button on pin {} was pressed", pin);
            }
        };

        button.addListener(listener);

        pinMap.put(pin, button);
        listenerMap.put(button, listener);
        log.info("Configured button on pin {}", pin);
    }

    public void clearPin(int pin) {
        DigitalInput button = pinMap.get(pin);
        if (button != null) {
            DigitalStateChangeListener listener = listenerMap.get(button);
            if (listener != null) {
                button.removeListener(listener);
                listenerMap.remove(button);
                log.info("Removed listener from button on pin {}", pin);
            }
            log.info("Button id: {}", button.getId());
//            pi4j.registry().remove(button.id());
            // Release the pin at the OS level (using GpioD if required)
            // Use gpioset to release the pin at the OS level
//            try {
//                String command = String.format("gpioset -r gpiochip0 %d=0", pin);
//                Process process = Runtime.getRuntime().exec(command);
//                int exitCode = process.waitFor();
//                if (exitCode != 0) {
//                    log.warn("Failed to release GPIO pin {} at OS level. Exit code: {}", pin, exitCode);
//                } else {
//                    log.info("Released GPIO pin {} at OS level.", pin);
//                }
//            } catch (Exception e) {
//                log.error("Error while releasing GPIO pin {}: {}", pin, e.getMessage());
//            }
            button.shutdown(pi4j);
            pinMap.remove(pin);
            log.info("Cleared configuration for pin {}", pin);
        } else {
            log.warn("No configuration found for pin {}. Skipping clear operation.", pin);
        }
    }

    public void clearAllPins() {
        Set<Integer> pins = new HashSet<>(pinMap.keySet());
        for (int pin : pins) {
            clearPin(pin); // Reuse clearPin method
        }
//        pi4j.shutdown();
//        pi4j = Pi4J.newAutoContext();
        log.info("All GPIO pins have been cleared.");
    }
}
