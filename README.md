### KG Update
- Module that updates KG

### Prerequsite
- docker cli
- pipenv

### Initialize virtual env
- Run the following command to init venv
```
pipenv install
```

### How to run
- Make sure the SDN controller and mininet is running. Refer: [Ryu-mininet](https://github.com/Krishna-Teja732/ryu-mininet)
- Run Neo4j: From root of the project run the following commands
```sh
cd database
docker compose up
```
- Start KG update
```sh
pipenv shell
python ./src/kg_build.py
```

### Check Graph in neo4j
- The graph database can be viewed through neo4j: http://localhost:7474/browser/ 


### TODO
- [x] Create/Delete switch nodes 
- [x] Create and add flow entry nodes to switch 
- [x] Create and add match nodes to flow entry 
- [x] Create and add action nodes to flow entry 
- [ ] Create and add match lables to match node
- [ ] Create and add action lables to action node
- [ ] Reset DB on startup
- [ ] Create Indexes
- [ ] Update Topology
- [ ] Grabage collection (delete flow entries that are not used)
