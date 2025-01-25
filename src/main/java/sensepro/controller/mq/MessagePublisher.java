package sensepro.controller.mq;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class MessagePublisher {

    private final RabbitTemplate rabbitTemplate;
    public MessagePublisher(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void sendMessage(String routingKey, Object object) {
        rabbitTemplate.convertAndSend(routingKey, object);
    }
}
