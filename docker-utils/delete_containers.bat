@ECHO OFF
FOR /f "tokens=*" %%i IN ('docker ps -aq') DO docker rm %%i

