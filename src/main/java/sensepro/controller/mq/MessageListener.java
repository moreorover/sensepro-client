package sensepro.controller.mq;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

@Component
//@ConditionalOnProperty(
//        name = "sensepro.server.listener",
//        havingValue = "true",
//        matchIfMissing = true // Set to true if you want it to be enabled by default when the property is missing
//)
public class MessageListener {

    Logger logger = LoggerFactory.getLogger(MessageListener.class);

    @RabbitListener(queues = "#{rabbitMqConfiguration.getQueue()}")
    public void receiveMessage(String message) {
        logger.info("Received message: {}", message);

        Path filePath = Path.of("output.txt");

        try {
            // Write the string to the file (creates the file if it doesn't exist)
            Files.writeString(filePath, message, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            logger.info("File written successfully!");
        } catch (IOException e) {
            logger.error(e.getMessage());
        }
    }
}
