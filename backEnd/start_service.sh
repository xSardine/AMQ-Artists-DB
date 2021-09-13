sudo docker build -t search_docker:1.0.0 .
sudo docker run --name search -h 127.0.0.1 -p 81:80 search_docker:1.0.0