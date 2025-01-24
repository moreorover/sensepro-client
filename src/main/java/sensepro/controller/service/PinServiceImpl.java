package sensepro.controller.service;

import sensepro.controller.mq.MessagePublisher;
import com.pi4j.Pi4J;
import com.pi4j.context.Context;
import com.pi4j.io.gpio.digital.DigitalInput;
import com.pi4j.io.gpio.digital.DigitalState;
import com.pi4j.io.gpio.digital.DigitalStateChangeListener;
import com.pi4j.io.gpio.digital.PullResistance;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Component
public class PinServiceImpl implements PinService {

    Logger logger = LoggerFactory.getLogger(PinServiceImpl.class);

    private final MessagePublisher messagePublisher;
    private final Context pi4j;
    private final FileService<String> fileService;
    private final Map<Integer, DigitalInput> pinMap;
    private final Map<DigitalInput, DigitalStateChangeListener> listenerMap;

    public PinServiceImpl(MessagePublisher messagePublisher, FileService<String> fileService) {
        this.messagePublisher = messagePublisher;
        this.pi4j = Pi4J.newAutoContext();
        this.fileService = fileService;
        this.pinMap = new HashMap<>();
        this.listenerMap = new HashMap<>();
    }

    @PostConstruct
    public void initialize() {
        logger.info("Initializing Pins...");
        String config = fileService.readFile("config.json", String.class);
        configurePin(24);
    }

    public void configurePin(int pin) {
        var buttonConfig = DigitalInput.newConfigBuilder(pi4j)
                .id("button-" + pin)
                .name("Button on pin " + pin)
                .address(pin)
                .pull(PullResistance.PULL_DOWN)
                .debounce(3000L);
        var button = pi4j.create(buttonConfig);
        DigitalStateChangeListener listener = e -> {
            if (e.state() == DigitalState.LOW) {
                messagePublisher.sendMessage("Button on pin " + pin + " was pressed");
            }
        };

        button.addListener(listener);

        pinMap.put(pin, button);
        listenerMap.put(button, listener);
        logger.info("Configured button on pin {}", pin);
    }

    public void clearPin(int pin) {
        DigitalInput button = pinMap.get(pin);
        if (button != null) {
            DigitalStateChangeListener listener = listenerMap.get(button);
            if (listener != null) {
                button.removeListener(listener);
                listenerMap.remove(button);
                logger.info("Removed listener from button on pin {}", pin);
            }
            button.shutdown(pi4j);
            pinMap.remove(pin);
            logger.info("Cleared configuration for pin {}", pin);
        } else {
            logger.warn("No configuration found for pin {}. Skipping clear operation.", pin);
        }
    }

    public void clearAllPins() {
        for (Map.Entry<Integer, DigitalInput> entry : pinMap.entrySet()) {
            int pin = entry.getKey();
            DigitalInput button = entry.getValue();
            DigitalStateChangeListener listener = listenerMap.get(button);
            if (listener != null) {
                button.removeListener(listener);
                logger.info("Removed listener from button on pin {}", pin);
            }
            button.shutdown(pi4j);
            logger.info("Cleared configuration for pin {}", pin);
        }
        pinMap.clear();
        listenerMap.clear();
        logger.info("All GPIO pins have been cleared.");
    }
}
