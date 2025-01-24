package sensepro.controller.rest;

import sensepro.controller.service.PinService;
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

    private final PinService pinService;

    public PinController(PinService pinService) {
        this.pinService = pinService;
    }

    @GetMapping("/{id}")
    public ResponseEntity<Integer> changePin(@PathVariable int id) {
        logger.info("Changing pin with id {}", id);
        pinService.clearAllPins();
        pinService.configurePin(id);
        return ResponseEntity.ok(id);
    }
}
