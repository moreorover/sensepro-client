package sensepro.controller.rabbitmqintegration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class ScheduledTasks {

    Logger logger = LoggerFactory.getLogger(ScheduledTasks.class);

    private final MessagePublisher messagePublisher;

    public ScheduledTasks(MessagePublisher messagePublisher) {
        this.messagePublisher = messagePublisher;
    }

    @Scheduled(cron = "*/30 * * * * *")
    public void task1() {
        LocalDateTime now = LocalDateTime.now();
        // Task logic goes here
        logger.info("Task 1 executed at {}", now);
        messagePublisher.sendMessage("message: " + now);
    }
}
