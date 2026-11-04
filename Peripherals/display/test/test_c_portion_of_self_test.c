// Test C portion of self-test for Nextion display

#include <stdint.h>
#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("Executing self-test on the Nextion display.\n");

    char buffer[10];

    for (uint8_t reg = 2; reg <= 6; reg++) {
        printf("Setting register R1_%d\n", reg);

        snprintf(buffer, sizeof(buffer), "R1_%d", reg);
        printf("setting %s to %c\n", buffer, '0' + (reg - 1));
        // set_nextion_text(buffer, '0' + (reg - 1));

        snprintf(buffer, sizeof(buffer), "R2_%d", reg);
        printf("setting %s to %c\n", buffer, '0' + reg);
        // set_nextion_text(buffer, '0' + reg);

        snprintf(buffer, sizeof(buffer), "R3_%d", reg);
        printf("setting %s to %c\n", buffer, '0' + (reg + 1));
        // set_nextion_text(buffer, '0' + ((reg + 1) % 10));
    }
    // Populate Numeric Register Positions on the Nextion display for self-test

    printf("Self-test completed.\n");

    return 0;
}