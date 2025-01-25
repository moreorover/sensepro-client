package sensepro.controller.mq;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Validator;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import sensepro.controller.model.Config;
import sensepro.controller.service.PinService;

import java.util.Set;

@Slf4j
@Component
public class MessageListener {

    private final ObjectMapper objectMapper;
    private final Validator validator;
    private final PinService pinService;

    public MessageListener(ObjectMapper objectMapper, Validator validator, PinService pinService) {
        this.objectMapper = objectMapper;
        this.validator = validator;
        this.pinService = pinService;
    }

    @RabbitListener(queues = "#{rabbitMqConfiguration.getControllerQueueName()}")
    public void receiveMessage(Message message) {
        try {
            String body = new String(message.getBody());
            Config config = objectMapper.readValue(body, Config.class);

            // Validate the message
            Set<ConstraintViolation<Config>> violations = validator.validate(config);
            if (!violations.isEmpty()) {
                throw new ConstraintViolationException("Message validation failed", violations);
            }

            // Process message
            log.info("Processing message: {}", message.getMessageProperties().getMessageId());

            pinService.configure(config);

            log.info("New configuration processed.");
            log.info("Message processed: {}", message.getMessageProperties().getMessageId());

        } catch (ConstraintViolationException e) {
            log.error("Validation error: {}", e.getMessage());
        } catch (Exception e) {
            log.error("Error processing message: {}", e.getMessage(), e);
        }
    }
}
