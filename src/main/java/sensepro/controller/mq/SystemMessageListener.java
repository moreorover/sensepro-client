package sensepro.controller.mq;

import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class SystemMessageListener {

    @RabbitListener(queues = "system")
    public void receiveMessage(Message message) {
        String body = new String(message.getBody());
        log.info("Received message on queue `system`: {}", body);
    }
}
