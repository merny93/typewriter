// compile with 
// gcc -fPIC -shared -I/usr/local/lib -lbcm2835 -O2 -o libtypewriter.so backend.c /usr/local/lib/libbcm2835.a
#include <sched.h>
#include <bcm2835.h>
#include <stdio.h>
#include <time.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <unistd.h>
#include <string.h>

#define TIMEOUT_POLLING_LOW_CLOCK 2*CLOCKS_PER_SEC/1000
#define TIMEOUT_POLLING_HIGH_CLOCK 20*CLOCKS_PER_SEC/1000

#define POLLING_PINS_NUM 9
#define VALUE_PINS_NUM 8
#define READ_DEBOUNCE 10


#define msgcheck(msg)         \
    if (msg == -1)            \
    {                         \
         \
    }                                   \

typedef struct
{
   long data_type;
   int data_buff[1];
} t_data;


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

extern int init_tw(){
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

int cleanup_tw(){
    /*
    Release all inputs and detach library
    1 if successful else 0
    */
   return bcm2835_close();
}


int write_multiple_tw(int* keys, int key_n, int pulse_n){
    /*
    works in exactly the same way as write 
    */
      
    //set priority for fast!
    if (setPriority() == -1){
        return -1;
    }

    int n_timout = 0;
    clock_t start_t;

    for (int pulse_num = 0; pulse_num < key_n*pulse_n; pulse_num++){
        int waiting = 1;
        int i;
        while (waiting){
            for (i = 0; i < key_n; i++){
                if (bcm2835_gpio_lev(polling_pins[keys[i]/VALUE_PINS_NUM]) == LOW){
                    waiting = 0;
                    break;
                }

            }
            if ((clock() - start_t) > TIMEOUT_POLLING_HIGH_CLOCK){
                n_timout++;
                break;
            }
        }
        // i must have gone low
        for (int j = 0; j<key_n; j++){
            if (polling_pins[keys[i]/VALUE_PINS_NUM] == polling_pins[keys[j]/VALUE_PINS_NUM]){
                bcm2835_gpio_fsel(value_pins[keys[j]%VALUE_PINS_NUM], BCM2835_GPIO_FSEL_OUTP);
                //write low
                bcm2835_gpio_write(value_pins[keys[j]%VALUE_PINS_NUM], LOW);
            }
        }
        //now wait until its back
        start_t =clock();
        while(bcm2835_gpio_lev(polling_pins[keys[i]/VALUE_PINS_NUM]) == LOW){
            if ((clock() - start_t)  > TIMEOUT_POLLING_LOW_CLOCK){
                n_timout++;
                break;
            }
            //wait again for it to go high
        }
        //must have gone high
        for (int j = 0; j<key_n; j++){
            if (polling_pins[keys[i]/VALUE_PINS_NUM] == polling_pins[keys[j]/VALUE_PINS_NUM]){
                bcm2835_gpio_fsel(value_pins[keys[j]%VALUE_PINS_NUM], BCM2835_GPIO_FSEL_INPT);
                bcm2835_gpio_set_pud(value_pins[keys[j]%VALUE_PINS_NUM],BCM2835_GPIO_PUD_OFF);
            }
        }

    }
    //done loop set everything to high impedance
    for(int i = 0; i < key_n; i++){
        int col = value_pins[keys[i]%VALUE_PINS_NUM];
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



void read_stream_tw(int *alive)
{
   /*
  writes to a message queue the next entered key.
  goes untill alive is set to 0
    */

   printf("starting read_stream_tw at the start\n");
   setPriority();

   int msqid;
   t_data data;
   int res;

   // create message queue
    if (-1 == (msqid = msgget( (key_t)1234, IPC_CREAT | 0666))){
        perror("msgget failed");
        exit(1);
    }

   

    int polling_pointer = 0;
    int ignore_pointer = 0;
   printf("starting read_stream_tw\n");

   
   while (alive[0])
   {
        if ((polling_pointer != ignore_pointer) && (bcm2835_gpio_lev(polling_pins[polling_pointer]) == LOW))
        {
                for (int value_pointer = 0; value_pointer < VALUE_PINS_NUM; value_pointer++){
                    int i;
                    for (i=1; i<=READ_DEBOUNCE + 1; i++){
                        if (bcm2835_gpio_lev(polling_pins[polling_pointer]) || bcm2835_gpio_lev(value_pins[value_pointer])){
                            break;
                        }
                    }
                    if (i > READ_DEBOUNCE)
                    {
                        res = polling_pointer * VALUE_PINS_NUM + value_pointer;
                        memcpy(data.data_buff, &res, sizeof(int));
                        // printf("sending %d\n", res);
                        msgcheck(msgsnd( msqid, &data, sizeof( t_data) - sizeof( long), IPC_NOWAIT));
                        // printf("sent %d\n", res);
                    }
                }
                ignore_pointer = polling_pointer;
                
        }
        else
        {
            polling_pointer = ((polling_pointer - 1) + POLLING_PINS_NUM) % POLLING_PINS_NUM;  
        }
   }
   printf("exiting read_stream_tw\n");
   // destroy message queue
   msgctl(msqid, IPC_RMID, NULL);
   return;
}
