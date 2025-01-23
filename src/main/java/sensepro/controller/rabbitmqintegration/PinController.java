package sensepro.controller.rabbitmqintegration;

import sensepro.controller.Pins;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/pin")
public class PinController {

    Logger logger = LoggerFactory.getLogger(PinController.class);

    private final Pins pins;

    public PinController(Pins pins) {
        this.pins = pins;
    }

    @GetMapping("/{id}")
    public ResponseEntity<Integer> changePin(@PathVariable int id) {
        logger.info("Changing pin with id {}", id);
        pins.clearAllPins();
        pins.configurePin(id);
        return ResponseEntity.ok(id);
    }
}
