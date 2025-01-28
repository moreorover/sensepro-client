package sensepro.controller.scheduled;

import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import sensepro.controller.mq.MessagePublisher;
import sensepro.controller.service.PinService;
import sensepro.controller.service.PinServiceImpl;

import java.time.LocalDateTime;

@Slf4j
@Component
public class ScheduledTasks {

    private final MessagePublisher messagePublisher;
    private final PinServiceImpl pinService;

    public ScheduledTasks(MessagePublisher messagePublisher, PinServiceImpl pinService) {
        this.messagePublisher = messagePublisher;
        this.pinService = pinService;
    }

//    @Scheduled(cron = "*/30 * * * * *")
    public void task1() {
        LocalDateTime now = LocalDateTime.now();
        // Task logic goes here
        log.info("Task 1 executed at {}", now);
        messagePublisher.sendMessage("system", "message: " + now);
    }

//    @Scheduled(cron = "*/30 * * * * *")
    public void task2() {
        LocalDateTime now = LocalDateTime.now();
        // Task logic goes here
        log.info("Task 2 executed at {}", now);
        log.info("Total buttons: {}", pinService.getPinMap().size());
        pinService.getPinMap().forEach((key, value) -> {
            log.info("Button key: {}", key);
            log.info("Button name: {}", value.getName());
            log.info("Setting high...");
            value.isHigh();
            log.info("Setting low...");
            value.isLow();
        });
    }
}
