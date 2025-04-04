#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

#define SHM_NAME "/my_shared_memory"

int main()
{
    int res;
    res = shm_unlink(SHM_NAME);
    printf("%d\n", res);
    if(res == -1)
    {
        switch(errno)
        {
            case ENOENT:
                printf("Doesnt exist\n");
                break;
            
            case EACCES:
                printf("no perm\n");
                break;
            
            case EINVAL:
                printf("Invalid name\n");
                break;
            
            default:
                printf("Unknown, %d\n", errno);
                break;
        }
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}