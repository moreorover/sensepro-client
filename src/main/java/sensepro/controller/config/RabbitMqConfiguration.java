package sensepro.controller.config;

import com.rabbitmq.client.Channel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.CachingConnectionFactory;
import org.springframework.amqp.rabbit.connection.Connection;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeoutException;

@Slf4j
@Configuration
public class RabbitMqConfiguration {

    @Value("${spring.rabbitmq.host}")
    private String host;

    @Value("${spring.rabbitmq.port}")
    private int port;

    @Value("${spring.rabbitmq.username}")
    private String username;

    @Value("${spring.rabbitmq.password}")
    private String password;

    @Value("${sensepro.raspberrypi.serial.number}")
    private String raspberryPiSerialNumber;

    public String getControllerQueueName() {
        return "controller-" + raspberryPiSerialNumber;
    }

    //    @Value("${spring.rabbitmq.virtual-host}")
    //    private String virtualHost;

    private static final String CONNECTION_FACTORY = "helloRabbitMQConnectionFactory";

    @Bean(CONNECTION_FACTORY)
    public ConnectionFactory connectionFactory() {
        CachingConnectionFactory connectionFactory = new CachingConnectionFactory();
        connectionFactory.setHost(host);
        connectionFactory.setPort(port);
        connectionFactory.setUsername(username);
        connectionFactory.setPassword(password);
//        connectionFactory.setVirtualHost(virtualHost);
        createControllerQueue(connectionFactory);
        createSystemQueue(connectionFactory);
        return connectionFactory;
    }

    private void createControllerQueue(ConnectionFactory connectionFactory) {
        try (Connection connection = connectionFactory.createConnection();
             Channel channel = connection.createChannel(true)) {
            channel.queueDeclare(getControllerQueueName(), true, false, false, Map.of("x-max-length", 1));
        } catch (IOException | TimeoutException e) {
            log.error(e.getMessage());
        }
    }

    private void createSystemQueue(ConnectionFactory connectionFactory) {
        try (Connection connection = connectionFactory.createConnection();
             Channel channel = connection.createChannel(true)) {
            channel.queueDeclare("system", true, false, false, Map.of());
        } catch (IOException | TimeoutException e) {
            log.error(e.getMessage());
        }
    }

    @Bean
    public SimpleRabbitListenerContainerFactory createRabbitListenerFactory(ConnectionFactory connectionFactory) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        factory.setAutoStartup(true);
        factory.setPrefetchCount(1);
        factory.setConnectionFactory(connectionFactory);
        return factory;
    }
}
