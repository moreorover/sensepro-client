package sensepro.controller.scheduled;

import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import sensepro.controller.mq.MessagePublisher;

import java.time.LocalDateTime;

@Slf4j
@Component
public class ScheduledTasks {

    private final MessagePublisher messagePublisher;

    public ScheduledTasks(MessagePublisher messagePublisher) {
        this.messagePublisher = messagePublisher;
    }

//    @Scheduled(cron = "*/30 * * * * *")
    public void task1() {
        LocalDateTime now = LocalDateTime.now();
        // Task logic goes here
        log.info("Task 1 executed at {}", now);
        messagePublisher.sendMessage("system", "message: " + now);
    }
}
