###
# Redis Server
which redis-server
sudo apt update && sudo apt install -y redis-server
sudo systemctl start redis-server or redis-server --daemonize yes


# make sure redis is running
ps aux | grep redis