package sensepro.controller;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
public class SenseProControllerApplication {

    public static void main(String[] args) {
        SpringApplication.run(SenseProControllerApplication.class, args);
    }

}
