#include <stdio.h>
#include <stdlib.h>
#include <netdb.h>
#include <netinet/in.h>
#include <string.h>
#include <unistd.h>
#include <netinet/tcp.h>

//gcc -m64 cookies.c -o cookies -no-pie

void serve(int sock)
{
    char buffer[1024];

    // recv data
    recv(sock, buffer, 2048, 0);

    // send the message back
    send(sock, buffer, strlen(buffer), 0);
}

int main(int argc, char *argv[])
{
    int sockfd, newsockfd, portno, clilen;
    struct sockaddr_in serv_addr, cli_addr;
    int n, pid;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);

    if (sockfd < 0)
    {
        perror("ERROR opening socket");
        exit(1);
    }

    bzero((char *)&serv_addr, sizeof(serv_addr));
    portno = 1234;

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);

    if (bind(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
        perror("ERROR on binding");
        exit(1);
    }

    listen(sockfd, 3);
    clilen = sizeof(cli_addr);

    while (1)
    {
        newsockfd = accept(sockfd, (struct sockaddr *)&cli_addr, &clilen);

        if (newsockfd < 0)
        {
            perror("ERROR on accept");
            exit(1);
        }

        pid = fork();

        if (pid < 0)
        {
            perror("ERROR on fork");
            exit(1);
        }

        if (pid == 0)
        {
            close(sockfd);
            write(newsockfd, "Welcome to the best echo service in the world!\n", 47);
            serve(newsockfd);
            send(newsockfd, "Goodbye!\n", strlen("Goodbye!\n"), 0);
            close(newsockfd);
            exit(0);
        }
        else
        {
            close(newsockfd);
        }
    }
}
