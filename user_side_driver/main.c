#include <winsock2.h>  
#include <Windows.h>
#include <stdio.h>
#include <stdlib.h>


int main() {
    printf("started\n");
    struct sockaddr_in cacheM =  { .sin_family = 2, .sin_port = htons(9998)};
    memset(cacheM.sin_zero, 0, 8);
    cacheM.sin_addr.s_addr = inet_addr("127.0.0.1");
    SOCKET connectedSocket = socket(2, SOCK_STREAM, 0); // AF_LOCAL = 2 for the 127.0.0.1 
    int status = connect(connectedSocket, (struct sockaddr*)&cacheM, sizeof(struct sockaddr_in));
    closesocket(connectedSocket);
}
