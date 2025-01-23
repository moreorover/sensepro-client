package sensepro.controller;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
public class MqTesterApplication {

    public static void main(String[] args) {
        SpringApplication.run(MqTesterApplication.class, args);
    }

}
