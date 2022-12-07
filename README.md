SpaceONE Secret Service

Secret Service supports multiple backend.

- AWSSecretManager
- Vault
- Consul
- etcd
- MongoDB


# Examples

## AWSSecretsManagerConnector

~~~
BACKEND: AWSSecretManagerConnector
CONNECTORS:
    AWSSecretManagerConnector:
        aws_access_key_id: xxxxxxxxx
	aws_secret_access_key: yyyyyyyy
	region_name: aws-region-name
~~~

## ConsulConnector

~~~

BACKEND: ConsulConnector
CONNECTORS:
    ConsulConnector:
        host: CONSUL_HOST_FQDN
	port: CONSUL_PORT
~~~

if you want to know the CONSUL_HOST_FQDN, comand ***kubectl get svc***.
In this case, CONSUL_HOST_FQDN is ***spaceone-consule-server***.


~~~
$ kubectl get svc
NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                                                                   AGE
...
spaceone-consul-dns      ClusterIP   10.100.170.168   <none>        53/TCP,53/UDP                                                             85m
spaceone-consul-server   ClusterIP   None             <none>        8500/TCP,8301/TCP,8301/UDP,8302/TCP,8302/UDP,8300/TCP,8600/TCP,8600/UDP   85m
...
~~~

## MongoDBConnector

~~~

BACKEND: MongoDBConnector
CONNECTORS:
    MongoDBConnector:
        host: MONGO_HOST
        port': 27017,
        username': MONGO_USER,
        password': MONGO_PASSWD
~~~