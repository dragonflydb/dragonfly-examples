cd /data
mkdir 7000 7001 7002

redis-server --port 7000 --cluster-enabled yes --protected-mode no --cluster-config-file 7000/nodes.conf --cluster-node-timeout 5000 >/dev/null&
sleep 1
redis-server --port 7001 --cluster-enabled yes --protected-mode no --cluster-config-file 7001/nodes.conf --cluster-node-timeout 5000 >/dev/null&
sleep 1
redis-server --port 7002 --cluster-enabled yes --protected-mode no --cluster-config-file 7002/nodes.conf --cluster-node-timeout 5000 >/dev/null&
sleep 1

redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 --cluster-yes >/dev/null

echo "Redis Cluster ready"

exec "$@"
