package sensepro.controller.rest;

import lombok.extern.slf4j.Slf4j;
import sensepro.controller.service.PinService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/pin")
public class PinController {

    private final PinService pinService;

    public PinController(PinService pinService) {
        this.pinService = pinService;
    }

    @GetMapping("/{id}")
    public ResponseEntity<Integer> changePin(@PathVariable int id) {
        log.info("Changing pin with id {}", id);
//        pinService.clearAllPins();
//        pinService.configurePin(id);
        return ResponseEntity.ok(id);
    }
}
