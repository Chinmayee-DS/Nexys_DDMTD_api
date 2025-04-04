#include "spi_common.h"
#include "NexysDDMTD.h"

int main(int argc, char** argv)
{
    // Startup the SPI interface on the Pi.
    init_spi();
    bcm2835_spi_setClockDivider(BCM2835_SPI_CLOCK_DIVIDER_64); 
    send3Byte_NexysDDMTD(DDMTD_PLL_EN_ADDR,0x1);
    bcm2835_spi_chipSelect(BCM2835_SPI_CS1); // Changing to the DDTMD PLL thinfe where the SI4344 clock thinge resides.
    bcm2835_spi_setChipSelectPolarity(BCM2835_SPI_CS1, LOW);

    int res1 = 0, res2 = 0, res3 = 0, res4 = 0;
    unsigned char value = '0';
    unsigned int address = 0x0001;
    unsigned int page;
    // res1 = spi_si5344_write_v2(address, value);

    page = (address>>8)&(0xFF);
    set2page(page); //write to page register the page you want to go to.
    // if ((int)read4addr(0x1) == page) printf("Success at setting the page to 0x%04x\n",(int)read4addr(0x1) );
    // else printf("Oh No...... Page not set to 0x%04x, the read value is 0x%04x! \n",page,(int)read4addr(0x1));
    write2addr((address&0xFF),value);
    // if ((int)read4addr(address&0xFF) == (int)value) printf("Success at writing  to 0x%04x with the value 0x%02x \n",(int)read4addr(0x1)<<8|address&0xFF,value );
    // else printf("Oh No...... Page not set to 0x%02x, the read value is 0x%02x! \n",(int)value,(int)read4addr(0x1));

    // printf("write done\n");


    address = 0x0002;
    page = (address>>8)&(0xFF);
    set2page(page); //write to page register the page you want to go to.
    // if ((int)read4addr(0x1) == page) printf("Success at setting the page to 0x%04x\n",(int)read4addr(0x1) );
    // else printf("Oh No...... Page not set to 0x%04x, the read value is 0x%04x! \n",page,(int)read4addr(0x1));
    res2 = read4addr((address&0xFF));

    
    // res2 = spi_si5344_read_v2(0x0002);
    // printf("%d %d %d %d\n", res1, res2, res3, res4);


    res3 = spi_si5344_read_v2(0x0003);
    // printf("%d %d %d %d\n", res1, res2, res3, res4);
    res4 = spi_si5344_read_v2(0x0004);
    // printf("%d %d %d %d\n", res1, res2, res3, res4);
    printf("%d %d %d\n", res2, res3, res4);

    return 0;
}