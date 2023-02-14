// compile with 
// gcc -fPIC -shared -I/usr/local/lib -lbcm2835 -O2 -o libtypewriter.so backend.c /usr/local/lib/libbcm2835.a
#include <sched.h>
#include <bcm2835.h>
#include <stdio.h>
#include <time.h>

#define TIMEOUT_POLLING_LOW_CLOCK 2*CLOCKS_PER_SEC/1000
#define TIMEOUT_POLLING_HIGH_CLOCK 20*CLOCKS_PER_SEC/1000

#define POLLING_PINS_NUM 9
#define VALUE_PINS_NUM 8

//the polling_pins in order
int polling_pins[POLLING_PINS_NUM] = {
    RPI_V2_GPIO_P1_37, 
    RPI_V2_GPIO_P1_36, 
    RPI_V2_GPIO_P1_33,
    RPI_V2_GPIO_P1_31, 
    RPI_V2_GPIO_P1_29, 
    RPI_V2_GPIO_P1_32, 
    RPI_V2_GPIO_P1_26, 
    RPI_V2_GPIO_P1_23, 
    RPI_V2_GPIO_P1_21, 
};
//the value pins in order
int value_pins[VALUE_PINS_NUM] = {
    RPI_V2_GPIO_P1_19, 
    RPI_V2_GPIO_P1_24, 
    RPI_V2_GPIO_P1_15,
    RPI_V2_GPIO_P1_13, 
    RPI_V2_GPIO_P1_11, 
    RPI_V2_GPIO_P1_22, 
    RPI_V2_GPIO_P1_07, 
    RPI_V2_GPIO_P1_18,  
};

int setPriority(){
    const struct sched_param priority = {1};
    return sched_setscheduler(0, SCHED_FIFO, &priority);
}

extern int init(){
    /*
    Initalizes all the pins as high impeedance inputs.
    1 if successful else 0 or -1 if fails the priority check
    !!! DO NOT PROCEED IF FAILS, will crash the pi !!!!
    */
    //    bcm2835_set_debug(1);
    //try to init the output
    if (!bcm2835_init()){
        return 0;
    }
    //activate the polling pins
    for (int i = 0; i < POLLING_PINS_NUM; i++){
        bcm2835_gpio_fsel(polling_pins[i], BCM2835_GPIO_FSEL_INPT);
        bcm2835_gpio_set_pud(polling_pins[i],BCM2835_GPIO_PUD_OFF);
    }
    //activate the value pins
    for (int i = 0; i < VALUE_PINS_NUM; i++){
        bcm2835_gpio_fsel(value_pins[i], BCM2835_GPIO_FSEL_INPT);
        bcm2835_gpio_set_pud(value_pins[i],BCM2835_GPIO_PUD_OFF);
    }
    //all done can return

    //check if we can set priority
    if(setPriority() == -1){
        return -1;
    }


    return 1;
    
}

int cleanup(){
    /*
    Release all inputs and detach library
    1 if successful else 0
    */
   return bcm2835_close();
}
int write(int row_n, int col_n, int n_repeat){
    /*
    Write to a specific address (designeated by row, col) by pulling it low n_repeat times
    assume init
    row is polling, col is value
    1 if successful else 0
    if it times out it will return failure
    */
   
    //set priority for fast!
    if (setPriority() == -1){
        return -1;
    }

    int row=polling_pins[row_n];
    int col = value_pins[col_n];

    int n_timout = 0;
    clock_t start_t;

    //write low on the correct value_pin (column) when the correct row is depresed
    for (int num_pulses =0; num_pulses<n_repeat; num_pulses++){
        start_t =clock();
        while(bcm2835_gpio_lev(row) == HIGH){
            if ((clock() - start_t) > TIMEOUT_POLLING_HIGH_CLOCK){
                n_timout++;
                break;
            }
            //wait for it to go low
        }
        //must have gone low!
        //update to write
        bcm2835_gpio_fsel(col, BCM2835_GPIO_FSEL_OUTP);
        //write low
        bcm2835_gpio_write(col, LOW);
        //wait for it to finish polling
        start_t =clock();
        while(bcm2835_gpio_lev(row) == LOW){
            if ((clock() - start_t)  > TIMEOUT_POLLING_LOW_CLOCK){
                n_timout++;
                break;
            }
            //wait again for it to go high
        }
        //must have gone high
        //switch back to high-impedance input
        bcm2835_gpio_fsel(col, BCM2835_GPIO_FSEL_INPT);
        bcm2835_gpio_set_pud(col,BCM2835_GPIO_PUD_OFF);
    }
    //all done
    if (n_timout > 0){
        return 0;
    } else {
    return 1;
    }
}

int* read(int* res, int timout_ms){
    /*
    return the next entered key. or timeout... assume init
    check that the key was pressed repeat times
    returns an int** array where res[row][col] == 1 means the button was pressed
    row is polling, col is value
    */
   setPriority(); //fails anyways

   clock_t start_t = clock();
   int timeout_clock = timout_ms*CLOCKS_PER_SEC/1000;

   //need to lock on...
   int polling_pointer = 0;
    for (int i=0; i<POLLING_PINS_NUM; i++){
        if (bcm2835_gpio_lev(polling_pins[i]) == LOW){
            //this is the pin that is being polled currently!
            polling_pointer = (i+1)%POLLING_PINS_NUM;
        }
    }
   //this will probably lock on...it might also just skip it but it does not really matter
    while(clock()- start_t <timeout_clock){
        if (bcm2835_gpio_lev(polling_pins[polling_pointer]) == LOW){
            //it just got pulled down. wait a bit and then read
            // for(int i=0;i < 10; i++){
            //     bcm2835_gpio_lev(value_pins[0]); //dumb wait.. works tho
            // }
            bcm2835_delayMicroseconds(50);
            //loop through all the value pins
            for (int i=0; i<VALUE_PINS_NUM; i++){
                res[polling_pointer*VALUE_PINS_NUM+i] += !bcm2835_gpio_lev(value_pins[i]);
            }
            //done looping through that row increment the pointer
            polling_pointer = (polling_pointer+1)%POLLING_PINS_NUM;
        }
   }
   return res;
}

